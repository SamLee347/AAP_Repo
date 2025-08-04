from flask import Flask, request, jsonify
from Database.db import SessionLocal, init_db
from Models.sample import Sample

app = Flask(__name__)

# Function to populate test data
def populate_test_data():
    session = SessionLocal()
    s1 = Sample(name="Sample A", date="2025-06-01", description="Test Desc")
    s2 = Sample(name="Sample B", date="2025-07-01", description="Another Desc")

    session.add_all([s1, s2])
    session.commit()
    session.close()



if __name__ == "__main__":
    try:
        init_db()
        populate_test_data()
        print("Database initialized and test data populated successfully.")
    except Exception as e:
        print(f"Error occurred: {e}: DATABASE NOT INITIALIZED MAYBE DUE TO MYSQL NOT RUNNING")
        
    app.run(debug=True, port=5000)
    print("Flask app running on port 5000")
