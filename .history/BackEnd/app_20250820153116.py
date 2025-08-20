import datetime
import os
from sqlalchemy.orm import joinedload
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
from Generative_Models.ChatBot.unifiedChatbot import create_unified_chatbot
from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from Database_Table.order import Order
from Generative_Models.ChatBot.nlpQuery import query_gemini
from mockdata import populate_test_data
from datetime import datetime
from Supervised_Models.ShernFai.model_functions import forecast_generalized_category, category_mapping
        

# Supervised Models
from load_model import (
    DISPOSAL_MODEL,
    STORAGE_MODEL,
    FORECAST_MODEL,
    CATEGORY_MODEL,
    REPORT_GENERATION_MODEL,
)
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import pickle
import numpy as np
import pandas as pd
import sys
import os
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "Supervised_Models"


# Gen-ai
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw")
unified_chatbot = None

app = Flask(__name__)
CORS(app)

# ======== Supervised Model =========== #
@app.route("/disposal-prediction", methods=["POST"])
def disposal_prediction():
    session = SessionLocal()
    try:
        item = session.query(Inventory).filter_by(ItemId=request.json["item_id"]).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        features = item.get_disposal_features()
        model = DISPOSAL_MODEL["model"]
        
        # Get prediction and confidence
        raw_prediction = model.predict([features])[0]
        
        # Determine prediction type and get confidence
        if isinstance(raw_prediction, (float, np.floating)) and 0 <= raw_prediction <= 1:
            # It's a probability
            dispose_probability = raw_prediction
            should_dispose = dispose_probability >= 0.5
            confidence = dispose_probability if should_dispose else (1 - dispose_probability)
        else:
            # It's binary (0 or 1)
            should_dispose = bool(raw_prediction)
            confidence = 1.0
        
        # Get proper probabilities if available
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba([features])[0]
            confidence = max(proba)  # Actual model confidence

        # SET CONFIDENCE THRESHOLD (adjust this value)
        CONFIDENCE_THRESHOLD = 0.7  # Only show predictions if 70%+ confident
        
        if confidence < CONFIDENCE_THRESHOLD:
            # Model is not confident enough
            response = {
                "recommendation": "UNCERTAIN",
                "confidence": float(confidence),
                "message": "Model is not confident enough to make a recommendation",
                "reasons": [
                    f"Confidence too low: {confidence:.1%}",
                    f"Minimum required: {CONFIDENCE_THRESHOLD:.0%}",
                    f"Consider manual review for this item"
                ]
            }
        else:
            # Model is confident - provide recommendation
            response = {
                "recommendation": "DISPOSE" if should_dispose else "KEEP",
                "confidence": float(confidence),
                "reasons": [
                    f"Quantity: {item.ItemQuantity}",
                    f"Sales: {item.UnitsSold}",
                    f"Turnover: {(item.UnitsSold/item.ItemQuantity):.2f}" if item.ItemQuantity else "N/A",
                    f"Confidence: {confidence:.1%}"
                ]
            }

        return jsonify(response)

    except Exception as e:
        logger.exception("Prediction failed")
        return jsonify({"error": "Prediction service unavailable"}), 500
    finally:
        session.close()

@app.route("/predictLocation", methods=["POST"])
def predict_location():
    """Endpoint to predict the location of an inventory item"""
    logger.info("Starting location prediction request")
    session = SessionLocal()
    input_data = request.json

    try:
        # Validate input
        if not input_data or "item_id" not in input_data:
            logger.error("Missing item_id in request")
            return jsonify({"error": "item_id is required"}), 400

        logger.debug(f"Input data received: {input_data}")

        # Database operations
        logger.info(f"Querying database for item_id: {input_data['item_id']}")
        item = session.query(Inventory).filter_by(ItemId=input_data["item_id"]).first()
        orders = session.query(Order).filter_by(ItemId=input_data["item_id"]).all()

        if not item:
            logger.warning(f"Item not found: {input_data['item_id']}")
            return jsonify({"error": "Item not found"}), 404

        logger.info(f"Found item: {item.ItemId} with {len(orders)} orders")

        try:
            with open(MODEL_DIR / "Samuel/storage_prediction_model.pkl", "rb") as file:
                storage_prediction_model = pickle.load(file)
            logger.debug("Model loaded successfully")
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            return jsonify({"error": "Model loading failed"}), 500

        # Define all expected features (this should match your training data)
        # You need to know what features the model was trained with
        # This is just an example - adjust according to your actual model
        expected_categories = {
            "Priority": ["High", "Low", "Medium"],
            "Product_Type": ["Clothing", "Electronics", "Home Goods", "Sports"],
            "Size": ["Large", "Medium", "Small"],
        }

        expected_numerical = ["Order_Quantity", "Weight"]

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
            if (
                hasattr(item, "Priority")
                and item.Priority in expected_categories["Priority"]
            ):
                features[f"Priority_{item.Priority}"] = 1

            if (
                hasattr(item, "Product_Type")
                and item.Product_Type in expected_categories["Product_Type"]
            ):
                features[f"Product_Type_{item.Product_Type}"] = 1

            if hasattr(item, "Size") and item.Size in expected_categories["Size"]:
                features[f"Size_{item.Size}"] = 1

            # Set numerical features
            features["Order_Quantity"] = sum(order.OrderQuantity for order in orders)
            features["Weight"] = item.Weight

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

            prob_dict = {
                str(label): float(prob)
                for label, prob in zip(class_labels, probabilities)
            }
            logger.info(f"Prediction probabilities: {prob_dict}")

            response = {
                "recommendation": str(prediction[0]),
                "confidence": prob_dict[str(prediction[0])],
                "reasons": [
                    f"Priority: {item.Priority}",
                    f"Total Orders: {len(orders)}",
                    f"Weight: {item.Weight}",
                ],
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

@app.route("/sales-forecast", methods=["POST"])
def sales_forecast():
    """Sales forecast using live database features"""
    session = SessionLocal()
    data = request.json
    
    try:
        if not data or 'item_id' not in data:
            return jsonify({"error": "Missing required field: item_id"}), 400
        
        # Check if forecast model is loaded
        if not FORECAST_MODEL:
            return jsonify({"error": "Forecast model not available"}), 500
        
        # Get item from database
        item = session.query(Inventory).filter_by(ItemId=data["item_id"]).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404
        
        # Get related orders to calculate LIVE features
        orders = session.query(Order).filter_by(ItemId=data["item_id"]).all()
        
        # Calculate LIVE features from your database
        live_features = calculate_live_features(item, orders)
        
        # Map inventory category to your model's expected categories
        category_mapping_for_model = {
            "Electronics": "Technology",
            "Clothing": "Clothing",
            "Sports": "Sports and Fitness", 
            "Technology": "Technology",
            "Cosmetics": "Other",
            "Home Goods": "Other",
            "Fitness": "Sports and Fitness"
        }
        
        mapped_category = category_mapping_for_model.get(item.ItemCategory, "Other")
        
        # Use your loaded model with live features
        result = forecast_generalized_category(
            model=FORECAST_MODEL['model'],
            le_category=FORECAST_MODEL['preprocessor']['label_encoder_category'],
            reference_date=FORECAST_MODEL['preprocessor']['reference_date'],
            future_year_month=data.get('month', '2025-03'),
            generalized_category=mapped_category,  # Use mapped category
            avg_price=live_features['avg_price'],
            customer_segment=live_features['dominant_segment'],
            discount_rate=live_features['avg_discount_rate'],
            category_mapping=category_mapping, # From your model_functions
            feature_columns=FORECAST_MODEL['feature_columns']
        )
        
        # Calculate confidence based on data quality
        confidence_score = 0.9 if live_features['data_quality'] == 'live_orders' else 0.3
        
        # Determine trend
        current_stock = item.ItemQuantity or 0
        predicted_demand = result['total_prediction']
        
        if predicted_demand > current_stock * 1.2:
            trend = "increasing"
        elif predicted_demand < current_stock * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Format response to match TypeScript interface
        response = {
            "next_month": int(round(predicted_demand)),
            "trend": trend,
            "confidence": int(round(confidence_score * 100))
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Sales forecast error: {e}")
        # Return fallback that matches TypeScript interface
        return jsonify({
            "next_month": 10,  # Fallback prediction
            "trend": "stable",
            "confidence": 30
        })
    finally:
        session.close()

def calculate_live_features(item, orders):
    """Calculate features from your actual database schema"""
    
    print(f"DEBUG: Item {item.ItemId} ({item.ItemName}) - {len(orders)} orders found")
    
    if not orders:
        # No orders - use defaults
        return {
            'avg_price': 25.50,
            'dominant_segment': 'Consumer',
            'avg_discount_rate': 0.08,
            'data_quality': 'no_orders',
            'order_count': 0
        }
    
    # Extract from actual orders (your schema has Price field!)
    prices = [float(order.Price) for order in orders if order.Price]
    discounts = [float(order.Discount) for order in orders if order.Discount]
    segments = [order.CustomerSegment for order in orders if order.CustomerSegment]
    
    # Calculate live features
    avg_price = np.mean(prices) if prices else 25.50
    avg_discount_rate = np.mean([d/p for d, p in zip(discounts, prices) if p > 0]) if discounts and prices else 0.08
    dominant_segment = max(set(segments), key=segments.count) if segments else 'Consumer'
    
    print(f"DEBUG: Calculated avg_price={avg_price}, segment={dominant_segment}, discount_rate={avg_discount_rate}")
    
    return {
        'avg_price': avg_price,
        'dominant_segment': dominant_segment,
        'avg_discount_rate': avg_discount_rate,
        'data_quality': 'live_orders',
        'order_count': len(orders)
    }

@app.route('/categorization', methods=["POST"])
def categorize_item():
    data = request.json
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "Item ID is required"}), 400

    session = SessionLocal()
    try:
        item = session.query(Inventory).filter(Inventory.ItemId == item_id).first()
        orders = session.query(Order).filter(Order.ItemId == item_id).all()

        if not item:
            return jsonify({"error": "Item not found"}), 404
        
        # Calculate features
        feature_values = [
            orders[0].Price if orders else 0,
            sum(order.Sales for order in orders) if orders else 0,
            sum(order.Profit for order in orders) if orders else 0,
            item.Weight if item.Weight else 0.0,
            item.ItemQuantity if item.ItemQuantity else 1,
        ]
        
        # Make prediction
        numeric_prediction = CATEGORY_MODEL['model'].predict([feature_values])[0]
        print(f"DEBUG: Raw prediction: {numeric_prediction}, type: {type(numeric_prediction)}")
        
        # Convert numeric prediction to category name
        print(f"DEBUG: Raw prediction: {numeric_prediction}, type: {type(numeric_prediction)}")
        
        # The trained model was built with numeric string labels, not actual category names
        # So we need to map from the model's weird outputs to meaningful main categories
        model_label_to_category = {
            '0': "Technology",
            '3': "Clothing", 
            '5': "Sports and Fitness",
            '6': "Other",  # This includes Book Shop, Pet Shop, Health and Beauty, Fan Shop
            '8': "Technology",
            'Other': "Other"
        }
        
        # Create fallback mapping based on prediction index
        prediction_index_to_category = {
            0: "Technology",    # Maps to label '0'
            1: "Clothing",      # Maps to label '3'  
            2: "Sports",        # Maps to label '5'
            3: "Books",         # Maps to label '6' <- This is your case!
            4: "Electronics",   # Maps to label '8'
            5: "Other"          # Maps to label 'Other'
        }
        
        try:
            # Try using the label encoder first
            model_output = CATEGORY_MODEL['label_encoder'].inverse_transform([int(numeric_prediction)])[0]
            print(f"DEBUG: Label encoder returned: '{model_output}' (type: {type(model_output)})")
            # Now map the model's weird output to a real category name
            category_name = model_label_to_category.get(str(model_output), f"Unknown_{model_output}")
            print(f"DEBUG: Mapped to category: '{category_name}'")
        except Exception as e:
            print(f"DEBUG: Label encoder failed ({e}), using fallback mapping")
            # Use fallback mapping based on prediction index
            category_name = prediction_index_to_category.get(int(numeric_prediction), f"Category_{int(numeric_prediction)}")
            print(f"DEBUG: Fallback mapping result: '{category_name}'")
        
        # Get confidence score
        confidence = 80.0
        if hasattr(CATEGORY_MODEL['model'], 'predict_proba'):
            proba = CATEGORY_MODEL['model'].predict_proba([feature_values])[0]
            confidence = max(proba) * 100

        response = {
            "category": str(category_name),
            "confidence": float(confidence),
            "attributes": [
                f"Price: ${feature_values[0]:.2f}",
                f"Sales: {feature_values[1]} units",
                f"Profit: ${feature_values[2]:.2f}",
                f"Weight: {feature_values[3]} kg",
                f"Stock: {feature_values[4]} units",
                f"Total Orders: {len(orders)}"
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Categorization error: {e}")
        return jsonify({"error": f"Categorization failed: {str(e)}"}), 500
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






# GENERATIVE MODELS
# REPORT GENERATION
# ---------------------------------------------------------------------------
@app.route("/generateReport", methods=["POST"])
def generate_report():
    return REPORT_GENERATION_MODEL()

@app.route("/list-reports", methods=["GET"])
def list_reports():
    """Return a list of all filenames in Generative_Models/ReportGeneration/Reports"""
    reports_dir = Path(__file__).parent / "Generative_Models" / "ReportGeneration" / "Reports"
    try:
        if not reports_dir.exists() or not reports_dir.is_dir():
            return jsonify({"error": "Reports directory not found"}), 404
        filenames = [f.name for f in reports_dir.iterdir() if f.is_file()]
        return jsonify(filenames)
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        return jsonify({"error": "Failed to list reports"}), 500

@app.route("/Reports/<path:filename>")
def serve_report(filename):
    try:
        return send_from_directory('Generative_Models/ReportGeneration/Reports', filename, mimetype="application/pdf")
    except FileNotFoundError:
        # If the file doesn't exist, return 404
        abort(404)

# CHATBOT BACKEND
# ---------------------------------------------------------------------------
try:
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw")
    unified_chatbot = create_unified_chatbot(API_KEY)
    print("✅ Unified chatbot initialized successfully")
except Exception as e:
    print(f"❌ Error initializing unified chatbot: {e}")
    unified_chatbot = None


# CHATBOT INITIALIZATION - Start
# =======================================================================================#


def initialize_chatbot():
    """Initialize chatbot with proper error handling"""
    global unified_chatbot
    try:
        unified_chatbot = create_unified_chatbot(API_KEY)
        print("✅ Unified chatbot initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing unified chatbot: {e}")
        unified_chatbot = None
        return False


# CHATBOT ROUTES
@app.route("/chat", methods=["POST", "GET"])
def unified_chat_endpoint():
    """Single endpoint for ALL chatbot functionality"""
    global unified_chatbot

    logger.info(f"=== CHAT ENDPOINT CALLED ===")

    if request.method == "GET":
        return jsonify(
            {
                "message": "Chat endpoint is ready. Send POST requests with 'message' field.",
                "status": "ready",
                "chatbot_available": unified_chatbot is not None,
            }
        )

    try:
        # Initialize chatbot if needed
        if unified_chatbot is None:
            if not initialize_chatbot():
                return (
                    jsonify(
                        {
                            "success": False,
                            "response": "Chatbot service is currently unavailable.",
                        }
                    ),
                    503,
                )

        data = request.get_json()
        if not data or "message" not in data:
            return (
                jsonify({"success": False, "response": "Please provide a message."}),
                400,
            )

        user_message = data["message"].strip()
        if not user_message:
            return (
                jsonify(
                    {"success": False, "response": "Please enter a valid question."}
                ),
                400,
            )

        logger.info(f"Processing message: '{user_message}'")

        # Get response from unified chatbot
        logger.info("=== CALLING CHATBOT ===")
        response = unified_chatbot.chat_with_unified_intelligence(user_message)
        logger.info("=== CHATBOT CALL COMPLETED ===")

        # Debug the response
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response length: {len(str(response)) if response else 'None'}")

        # Check if response is serializable
        try:
            import json

            # Try to serialize the response
            json_test = json.dumps(str(response))
            logger.info("✅ Response is JSON serializable")
        except Exception as json_error:
            logger.error(f"❌ Response not JSON serializable: {json_error}")
            # Clean the response
            response = str(response).encode("utf-8", errors="ignore").decode("utf-8")
            logger.info("🔧 Cleaned response for JSON compatibility")

        # Test datetime creation
        try:
            timestamp = datetime.now().isoformat()  # ← This line fails
            logger.info(f"✅ Timestamp created: {timestamp}")
        except Exception as dt_error:
            logger.error(f"❌ Datetime error: {dt_error}")
            timestamp = "2025-08-19T19:43:00"  # Fallback timestamp

        # Build response step by step
        logger.info("=== BUILDING RESPONSE ===")
        try:
            response_data = {
                "success": True,
                "message": user_message,
                "response": str(response),  # Ensure it's a string
                "timestamp": timestamp,
            }
            logger.info("✅ Response data structure created")

            # Test JSON serialization of the full response
            test_json = json.dumps(response_data)
            logger.info("✅ Full response is JSON serializable")

            logger.info("=== RETURNING RESPONSE ===")
            return jsonify(response_data)

        except Exception as build_error:
            logger.error(f"❌ Error building response: {build_error}")

            # Return a safe fallback response
            return (
                jsonify(
                    {
                        "success": False,
                        "response": "I processed your request but encountered an error formatting the response. Please try again.",
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"❌ MAIN ERROR: {e}")

        return (
            jsonify(
                {
                    "success": False,
                    "response": f"Sorry, I encountered an error: {str(e)}",
                }
            ),
            500,
        )


@app.route("/chat/status", methods=["GET"])
def chat_status():
    return jsonify(
        {
            "success": True,
            "chatbot_available": unified_chatbot is not None,
            "capabilities": [
                "Demand Forecasting",
                "Trend Analysis",
                "Database Querying",
            ],
        }
    )


@app.route("/chat/test", methods=["GET"])
def test_chat():
    test_message = "What categories do you have?"

    try:
        if unified_chatbot is None:
            initialize_chatbot()

        if unified_chatbot:
            response = unified_chatbot.chat_with_unified_intelligence(test_message)
            return jsonify(
                {
                    "test_message": test_message,
                    "response": response,
                    "status": "success",
                }
            )
        else:
            return jsonify(
                {
                    "test_message": test_message,
                    "response": "Chatbot not available",
                    "status": "failed",
                }
            )
    except Exception as e:
        return jsonify(
            {"test_message": test_message, "response": str(e), "status": "error"}
        )


# =======================================================================================#
# CHATBOT INITIALIZATION - End


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
