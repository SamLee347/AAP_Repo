import os
from datetime import datetime  # ADD THIS MISSING IMPORT
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

# ====================================== #

# CHATBOT INITIALIZATION - SINGLE CLEAN VERSION
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
        
        # Get response from unified chatbot
        response = unified_chatbot.chat_with_unified_intelligence(user_message)
        
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