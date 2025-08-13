from flask import Flask, request, jsonify, render_template
from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from GenerativeModels.ChatBot.nlpQuery import query_gemini

app = Flask(__name__)

# Function to populate test data
def populate_test_data():
    session = SessionLocal()
    s1 = Inventory(ItemId=1, Date="2025-06-01", ItemQuantity=100, ItemCategory="Electronics", UnitsSold=50, Weight=1.5, Size=10.0, Priority="High", Dispose=False)
    s2 = Inventory(ItemId=2, Date="2025-07-01", ItemQuantity=200, ItemCategory="Electronics", UnitsSold=100, Weight=2.0, Size=20.0, Priority="Medium", Dispose=False)

    session.add_all([s1, s2])
    session.commit()
    session.close()

def testing_nlpchatbot():
    question = "How many units of ItemId 101 are in stock?"
    answer = query_gemini(question)
    print(answer)

@app.route('/', methods=['GET'])
def home():
    testing_nlpchatbot()
    return render_template("index.html", result=None)

if __name__ == "__main__":
    try:
        init_db()
        populate_test_data()
        print("Database initialized and test data populated successfully.")
    except Exception as e:
        print(f"Error occurred: {e}: DATABASE NOT INITIALIZED MAYBE DUE TO MYSQL NOT RUNNING")
        
    app.run(debug=True, port=5000)
    print("Flask app running on port 5000")

    try:
        testing_nlpchatbot()
    except Exception as e:
        print(f"Error occurred while testing NLP chatbot: {e}")
