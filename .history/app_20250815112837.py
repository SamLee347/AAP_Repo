from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from Database_Table.order import Order
from GenerativeModels.ChatBot.nlpQuery import query_gemini

app = Flask(__name__)
CORS(app)


def populate_test_data():
    session = SessionLocal()

    # Clear existing data (important for testing)
    session.query(Order).delete()
    session.query(Inventory).delete()

    # Create Inventory test items
    electronics = Inventory(
        ItemId=101,
        Date="2025-06-01",
        ItemQuantity=100,
        ItemCategory="Electronics",
        UnitsSold=50,
        Weight=1.5,
        Size=10.0,
        Priority="High",
        Dispose=False,
    )

    clothing = Inventory(
        ItemId=102,
        Date="2025-07-01",
        ItemQuantity=200,
        ItemCategory="Clothing",
        UnitsSold=100,
        Weight=2.0,
        Size=20.0,
        Priority="Medium",
        Dispose=False,
    )

    furniture = Inventory(
        ItemId=103,
        Date="2025-08-01",
        ItemQuantity=150,
        ItemCategory="Furniture",
        UnitsSold=75,
        Weight=15.0,
        Size=50.0,
        Priority="Low",
        Dispose=True,
    )

    # Create Orders that reference these inventory items
    orders = [
        Order(
            OrderId=1001,
            ItemId=101,  # References electronics ItemId
            OrderQuantity=10,
            Sales=5000,
            Price=500,
            Discount=50,
            Profit=4500,
            DateOrdered="2025-06-15",
            DateReceived="2025-06-20",
            CustomerSegment="Corporate",
        ),
        Order(
            OrderId=1002,
            ItemId=102,  # References clothing ItemId
            OrderQuantity=20,
            Sales=2000,
            Price=100,
            Discount=20,
            Profit=1980,
            DateOrdered="2025-07-10",
            DateReceived="2025-07-12",
            CustomerSegment="Retail",
        ),
        Order(
            OrderId=1003,
            ItemId=101,  # References electronics ItemId again
            OrderQuantity=5,
            Sales=2500,
            Price=500,
            Discount=25,
            Profit=2475,
            DateOrdered="2025-08-05",
            DateReceived="2025-08-10",
            CustomerSegment="Wholesale",
        ),
    ]

    # Add to session and commit
    session.add_all([electronics, clothing, furniture])
    session.add_all(orders)
    session.commit()
    session.close()


@app.route("/test-chatbot", methods=["GET"])
def test_chatbot():
    """Endpoint to test inventory and order queries"""
    test_queries = [
        # Inventory queries
        "Suggest  would be suitable for a holiday flash sale? Provide reasoning",
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
