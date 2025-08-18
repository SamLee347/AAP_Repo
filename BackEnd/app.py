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

