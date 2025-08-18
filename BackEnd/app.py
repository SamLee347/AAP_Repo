from sqlalchemy.orm import joinedload
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from Database_Table.order import Order
from Generative_Models.ChatBot.nlpQuery import query_gemini
from mockdata import populate_test_data
import numpy as np

#Supervised Models
from load_model import DISPOSAL_MODEL, STORAGE_MODEL, FORECAST_MODEL, CATEGORY_MODEL
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import pickle
import numpy as np
import pandas as pd
import sys
import os



app = Flask(__name__)
CORS(app)

# ======== Supervised Model =========== #

@app.route('/disposal-prediction', methods=['POST'])
def disposal_prediction():
    logger.debug("Request received: %s", request.json)
    
    session = SessionLocal()
    try:
        item = session.query(Inventory).filter_by(ItemId=request.json['item_id']).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        features = item.get_disposal_features()
        logger.debug("Features shape: %s", np.array(features).shape)
        
        model = DISPOSAL_MODEL['model']
        prediction = model.predict([features])[0]  # Get single prediction
        proba = model.predict_proba([features])[0] if hasattr(model, 'predict_proba') else None  # Fixed
        
        response = {
            "recommendation": "DISPOSE" if prediction >= DISPOSAL_MODEL['threshold'] else "KEEP",
            "confidence": float(max(proba)) if proba is not None else None,  # Now safe
            "reasons": [
                f"Quantity: {item.ItemQuantity}",
                f"Sales: {item.UnitsSold}",
                f"Turnover: {(item.UnitsSold/item.ItemQuantity):.2f}" if item.ItemQuantity else "N/A"
            ]
        }
        return jsonify(response)
        
    except Exception as e:
        logger.exception("Prediction failed")
        return jsonify({"error": "Prediction service unavailable"}), 500
    finally:
        session.close()
# ====================================== #


@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Endpoint to get all inventory items"""
    session = SessionLocal()
    inventory_items = session.query(Inventory).all()
    result = [item.to_dict() for item in inventory_items]
    session.close()
    return jsonify(result)

@app.route("/orders", methods=["GET"])
def get_orders():
    """Endpoint to get all orders"""
    session = SessionLocal()
    # Eagerly load the inventory_item relationship
    orders = session.query(Order).options(joinedload(Order.inventory_item)).all()
    # Convert to dict while session is still open
    result = [order.to_dict() for order in orders]
    session.close()
    return jsonify(result)

@app.route("/test-chatbot", methods=["GET"])
def test_chatbot():
    """Endpoint to test inventory and order queries"""
    test_queries = [
        # Inventory queries
        "Suggest an item in inventory would be suitable for a holiday flash sale.Must pick at least 1",
        # Order queries
        "Show me all orders for item ID 101",
        "What was the total profit from corporate customers?",
        "Which order had the highest discount?",
        # Combined queries
        "What's the total quantity ordered for electronics items?",
        "Show me items that have orders from retail customers",
    ]

    results = []
    for query in test_queries:
        try:
            answer = query_gemini(query)
            results.append({"question": query, "answer": answer, "status": "success"})
        except Exception as e:
            results.append(
                {"question": query, "answer": f"Error: {str(e)}", "status": "failed"}
            )

    return jsonify({"tests": results})

@app.route("/predictLocation", methods=["POST"])
def predict_location():
    """Endpoint to predict the location of an inventory item"""
    logger.info("Starting location prediction request")
    session = SessionLocal()
    input_data = request.json
    
    try:
        # Validate input
        if not input_data or 'item_id' not in input_data:
            logger.error("Missing item_id in request")
            return jsonify({"error": "item_id is required"}), 400

        logger.debug(f"Input data received: {input_data}")

        # Database operations
        logger.info(f"Querying database for item_id: {input_data['item_id']}")
        item = session.query(Inventory).filter_by(ItemId=input_data['item_id']).first()
        orders = session.query(Order).filter_by(ItemId=input_data['item_id']).all()

        if not item:
            logger.warning(f"Item not found: {input_data['item_id']}")
            return jsonify({"error": "Item not found"}), 404

        logger.info(f"Found item: {item.ItemId} with {len(orders)} orders")

        # Model loading
        model_path = 'Supervised_Models/Samuel/storage_prediction_model.pkl'
        logger.info(f"Loading model from: {model_path}")
        
        try:
            with open(model_path, 'rb') as file:
                storage_prediction_model = pickle.load(file)
            logger.debug("Model loaded successfully")
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            return jsonify({"error": "Model loading failed"}), 500

        # Define all expected features (this should match your training data)
        # You need to know what features the model was trained with
        # This is just an example - adjust according to your actual model
        expected_categories = {
            'Priority': ['High', 'Low', 'Medium'],
            'Product_Type': ['Clothing', 'Electronics', 'Home Goods', 'Sports'],
            'Size': ['Large', 'Medium', 'Small']
        }
        
        expected_numerical = ['Order_Quantity', 'Weight']
        
        # Initialize all features to 0
        features = {}
        
        # Set up one-hot encoded features
        for feature, categories in expected_categories.items():
            for category in categories:
                features[f"{feature}_{category}"] = 0
        
        # Add numerical features
        for feature in expected_numerical:
            features[feature] = 0
        
        # Now populate the actual values
        try:
            # Set the correct category to 1
            if hasattr(item, 'Priority') and item.Priority in expected_categories['Priority']:
                features[f"Priority_{item.Priority}"] = 1
            
            if hasattr(item, 'Product_Type') and item.Product_Type in expected_categories['Product_Type']:
                features[f"Product_Type_{item.Product_Type}"] = 1
            
            if hasattr(item, 'Size') and item.Size in expected_categories['Size']:
                features[f"Size_{item.Size}"] = 1
            
            # Set numerical features
            features['Order_Quantity'] = sum(order.OrderQuantity for order in orders)
            features['Weight'] = item.Weight
            
            # Create feature array in correct order (this must match training)
            # You might need to save the feature order when training the model
            feature_names = sorted(features.keys())
            feature_values = [features[name] for name in feature_names]
            
            features_array = np.array(feature_values).reshape(1, -1)
            logger.debug(f"Final feature array shape: {features_array.shape}")
            
        except Exception as e:
            logger.error(f"Feature processing failed: {str(e)}")
            return jsonify({"error": "Feature processing failed"}), 500

        # Prediction
        logger.info("Making prediction")
        try:
            prediction = storage_prediction_model.predict(features_array)
            probabilities = storage_prediction_model.predict_proba(features_array)[0]
            class_labels = storage_prediction_model.classes_
            
            logger.debug(f"Raw prediction: {prediction}")
            logger.debug(f"Class probabilities: {probabilities}")
            
            prob_dict = {str(label): float(prob) for label, prob in zip(class_labels, probabilities)}
            logger.info(f"Prediction probabilities: {prob_dict}")
            
            response = {
                "recommendation": str(prediction[0]),
                "confidence": prob_dict[str(prediction[0])],
                "reasons": [
                    f"Priority: {item.Priority}",
                    f"Total Orders: {len(orders)}",
                    f"Weight: {item.Weight}"
                ]
            }
            
            logger.info(f"Successful prediction: {response}")
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return jsonify({"error": "Prediction failed"}), 500

    except Exception as e:
        logger.exception("Unexpected error in predict_location")
        return jsonify({"error": "Internal server error"}), 500
        
    finally:
        session.close()
        logger.info("Database session closed")
        
    # return {'PredictedLocation': prediction[0], 'Confidence': prob_dict[prediction[0]]}

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    try:
        init_db()
        populate_test_data()
        print("Database initialized and test data populated successfully.")
    except Exception as e:
        print(
            f"Error occurred: {e}: DATABASE NOT INITIALIZED MAYBE DUE TO MYSQL NOT RUNNING"
        )

    app.run(debug=True, port=5000)
    print("Flask app running on port 5000")

