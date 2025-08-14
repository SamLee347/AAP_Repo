from flask import Flask, request, jsonify, render_template
from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from Database_Table.order import Order


app = Flask(__name__)

# Function to populate test data
def populate_test_data():
    session = SessionLocal()
    s1 = Inventory(Date="2025-06-01", ItemQuantity=100, ItemCategory="Technology", UnitsSold=50, Weight=1.5, Size=10.0, Priority="High", Dispose=False)
    s2 = Inventory(Date="2025-07-01", ItemQuantity=200, ItemCategory="Other", UnitsSold=100, Weight=2.0, Size=20.0, Priority="Medium", Dispose=False)

    session.add_all([s1, s2])
    session.commit()
    session.close()

def populate_order_data():
    session = SessionLocal()
    o1 = Order(ItemId=1, OrderQuantity=50, Sales=5000, Price=100.0, Discount=10.0, Profit=4500.0, DateOrdered="2025-06-01", DateReceived="2025-06-05", CustomerSegment="Corporate")
    o2 = Order(ItemId=2, OrderQuantity=100, Sales=10000, Price=100.0, Discount=5.0, Profit=9500.0, DateOrdered="2025-07-01", DateReceived="2025-07-05", CustomerSegment="Consumer")

    session.add_all([o1, o2])
    session.commit()
    session.close()


@app.route('/', methods=['GET'])
def home():
    return render_template("index.html", result=None)

if __name__ == "__main__":
    try:
        init_db()
        populate_test_data()
        populate_order_data()
        print("Database initialized and test data populated successfully.")
    except Exception as e:
        print(f"Error occurred: {e}: DATABASE NOT INITIALIZED MAYBE DUE TO MYSQL NOT RUNNING")
        
    app.run(debug=True, port=5000)
    print("Flask app running on port 5000")


