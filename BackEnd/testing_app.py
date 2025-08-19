import os
from sqlalchemy.orm import joinedload
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from Generative_Models.ChatBot.unifiedChatbot import create_unified_chatbot
from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from Database_Table.order import Order
from Generative_Models.ChatBot.nlpQuery import query_gemini
from mockdata import populate_test_data
import numpy as np
import pickle

#Supervised Models
from load_model import DISPOSAL_MODEL, STORAGE_MODEL, FORECAST_MODEL, CATEGORY_MODEL
import logging
import traceback
import json
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        prediction = model.predict([features])[0]
        proba = model.predict_proba([features])[0] if hasattr(model, 'predict_proba') else None
        
        response = {
            "recommendation": "DISPOSE" if prediction >= DISPOSAL_MODEL['threshold'] else "KEEP",
            "confidence": float(max(proba)) if proba is not None else None,
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

# =======================================================================================# #
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

# @app.route("/test-chatbot", methods=["GET"])
# def test_chatbot():
#     """Endpoint to test inventory and order queries"""
#     test_queries = [
#         # Inventory queries
#         "Suggest an item in inventory would be suitable for a holiday flash sale.Must pick at least 1",
#         # Order queries
#         "Show me all orders for item ID 101",
#         "What was the total profit from corporate customers?",
#         "Which order had the highest discount?",
#         # Combined queries
#         "What's the total quantity ordered for electronics items?",
#         "Show me items that have orders from retail customers",
#     ]

#     results = []
#     for query in test_queries:
#         try:
#             answer = query_gemini(query)
#             results.append({"question": query, "answer": answer, "status": "success"})
#         except Exception as e:
#             results.append(
#                 {"question": query, "answer": f"Error: {str(e)}", "status": "failed"}
#             )

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
        
        

# CHATBOT INITIALIZATION - Start
# =======================================================================================#
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw')
unified_chatbot = None

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
        return jsonify({
            "message": "Chat endpoint is ready. Send POST requests with 'message' field.",
            "status": "ready",
            "chatbot_available": unified_chatbot is not None
        })
    
    try:
        # Initialize chatbot if needed
        if unified_chatbot is None:
            if not initialize_chatbot():
                return jsonify({
                    "success": False,
                    "response": "Chatbot service is currently unavailable."
                }), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "response": "Please provide a message."
            }), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                "success": False,
                "response": "Please enter a valid question."
            }), 400
        
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
            response = str(response).encode('utf-8', errors='ignore').decode('utf-8')
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
                "timestamp": timestamp
            }
            logger.info("✅ Response data structure created")
            
            # Test JSON serialization of the full response
            test_json = json.dumps(response_data)
            logger.info("✅ Full response is JSON serializable")
            
            logger.info("=== RETURNING RESPONSE ===")
            return jsonify(response_data)
            
        except Exception as build_error:
            logger.error(f"❌ Error building response: {build_error}")
            logger.error(traceback.format_exc())
            
            # Return a safe fallback response
            return jsonify({
                "success": False,
                "response": "I processed your request but encountered an error formatting the response. Please try again."
            }), 500
        
    except Exception as e:
        logger.error(f"❌ MAIN ERROR: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "response": f"Sorry, I encountered an error: {str(e)}"
        }), 500

@app.route("/chat/status", methods=["GET"])
def chat_status():
    return jsonify({
        "success": True,
        "chatbot_available": unified_chatbot is not None,
        "capabilities": ["Demand Forecasting", "Trend Analysis", "Database Querying"]
    })

@app.route("/chat/test", methods=["GET"])
def test_chat():
    test_message = "What categories do you have?"
    
    try:
        if unified_chatbot is None:
            initialize_chatbot()
        
        if unified_chatbot:
            response = unified_chatbot.chat_with_unified_intelligence(test_message)
            return jsonify({
                "test_message": test_message,
                "response": response,
                "status": "success"
            })
        else:
            return jsonify({
                "test_message": test_message,
                "response": "Chatbot not available",
                "status": "failed"
            })
    except Exception as e:
        return jsonify({
            "test_message": test_message,
            "response": str(e),
            "status": "error"
        })
#=======================================================================================#
# CHATBOT INITIALIZATION - End

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    try:
        init_db()
        populate_test_data()
        print("Database initialized and test data populated successfully.")
        
        # Initialize chatbot on startup
        initialize_chatbot()
        
    except Exception as e:
        print(f"Error occurred: {e}: DATABASE NOT INITIALIZED MAYBE DUE TO MYSQL NOT RUNNING")

    app.run(debug=True, port=5000)