import os
from sqlalchemy.orm import joinedload
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from Generative_Models.ChatBot.unifiedChatbot import create_unified_chatbot
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

@app.route("/chat", methods=["POST", "GET"])
def unified_chat_endpoint():
    """Simple chat endpoint"""
    global unified_chatbot
    
    if request.method == "GET":
        # Serve a simple chat interface (you can create this later)
        return jsonify({
            "message": "Chat endpoint is ready. Send POST requests with 'message' field."
        })
    
    try:
        # Initialize chatbot if not already done
        if unified_chatbot is None:
            if not initialize_chatbot():
                return jsonify({
                    "success": False,
                    "response": "Chatbot service is currently unavailable. Please try again later."
                }), 503
        
        # Get user message
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
        
        # Get response from chatbot
        response = unified_chatbot.chat_with_unified_intelligence(user_message)
        
        # Return simple response
        return jsonify({
            "success": True,
            "message": user_message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "success": False,
            "response": f"Sorry, I encountered an error: {str(e)}"
        }), 500

@app.route("/chat/test", methods=["GET"])
def test_chat():
    """Simple test endpoint"""
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
        
# CHATBOT BACKEND
# ---------------------------------------------------------------------------
try:
    API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw')
    unified_chatbot = create_unified_chatbot(API_KEY)
    print("✅ Unified chatbot initialized successfully")
except Exception as e:
    print(f"❌ Error initializing unified chatbot: {e}")
    unified_chatbot = None

# ... existing routes ...
@app.route("/chat", methods=["POST", "GET"])
def unified_chat_endpoint():
    """Single endpoint for ALL chatbot functionality with intent recognition"""
    if request.method == "GET":
        # Serve the chat interface
        return render_template('chat.html')
    
    try:
        if not unified_chatbot:
            return jsonify({
                "success": False,
                "error": "Chatbot service not available",
                "response": "Sorry, the AI assistant is currently unavailable. Please try again later."
            }), 503
        
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Missing message in request",
                "response": "Please provide a message to process."
            }), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "Empty message",
                "response": "Please enter a valid question."
            }), 400
        
        # Let the unified chatbot handle EVERYTHING - it will determine intent automatically
        response = unified_chatbot.chat_with_unified_intelligence(user_message)
        
        # Simple, clean response
        return jsonify({
            "success": True,
            "message": user_message,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "chatbot_type": "unified_intelligence"
        })
        
    except Exception as e:
        return jsonify({
"success": False,
            "error": str(e),
            "response": f"An error occurred while processing your request: {str(e)}"
        }), 500

@app.route("/chat/status", methods=["GET"])
def chat_status():
    """Simple status check endpoint"""
    return jsonify({
        "success": True,
        "chatbot_available": unified_chatbot is not None,
        "capabilities": [
            "Demand Forecasting",
            "Trend Analysis", 
            "Database Querying",
            "Business Intelligence"
        ],
        "example_queries": [
            "Forecast Technology demand for March 2025",
            "Which categories are declining?",
            "Show me recent orders for electronics",
            "What's our best selling category?",
            "Predict Office Supplies with optimistic scenario"
        ]
    })
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    try:
        init_db()
        populate_test_data()
        print("Database initialized and test data populated successfully.")
        
        # Initialize chatbot on startup
        initialize_chatbot()
        
    except Exception as e:
        print(f"Error occurred: {e}: DATABASE NOT INITIALIZED MAYBE DUE TO MYSQL NOT RUNNING")

    app.run(debug=True)
