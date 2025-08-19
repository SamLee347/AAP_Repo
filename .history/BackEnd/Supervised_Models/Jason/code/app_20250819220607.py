from flask import Flask, request, render_template
import joblib
import pandas as pd
import os
import numpy as np

app = Flask(__name__)

# Configure paths
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "..", "model", "gradient_boosting_model.pkl")

# Load model with error handling
try:
    model = joblib.load(model_path)
    print("✅ Model loaded successfully!")

    # Get feature names from model
    if hasattr(model, "feature_names_in_"):
        feature_columns = list(model.feature_names_in_)
    else:
        feature_columns = [
            "Price",
            "Sales",
            "Order_Profit",
            "Quantity",
            "ProductWeight",
            # Add all other expected columns
        ]
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    feature_columns = []

# Data specifications
DATA_SPECS = {
    "numerical": {
        "Price": {"type": float, "default": 0.0},
        "Sales": {"type": float, "default": 0.0},
        "Order_Profit": {"type": float, "default": 0.0},
        "Quantity": {"type": int, "default": 1},
        "ProductWeight": {"type": float, "default": 0.0},
        "Dispatched": {"type": int, "default": 0},
        "Scheduled_Shipping": {"type": int, "default": 1},
        "WeekdayOrder": {"type": int, "default": 0},
    },
    "categorical": {
        "Customer_Category": ["Consumer", "Corporate", "Home Office"],
        "Product_type": ["Fragile", "Not Fragile"],
        "Shipping_Class": ["Standard", "2A", "Elite", "First Class"],
        "Cust_State": ["AR", "BR", "CA", "RJ", "UK", "UP", "US"],
        "Warehouse_Region": ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"],
        "Delivery_Review": ["1", "2", "3", "4", "5"],
        "Delivery_Status": ["0", "1"],
    },
}


@app.route("/")
def home():
    return render_template("index.html", data_specs=DATA_SPECS)


@app.route("/predict", methods=["POST"])
def predict():
    if not model:
        return "Model not loaded. Please try again later.", 500

    try:
        # Process form data
        form_data = {}

        # Handle numerical fields
        for field, specs in DATA_SPECS["numerical"].items():
            value = request.form.get(field, "")
            try:
                form_data[field] = specs["type"](value) if value else specs["default"]
            except (ValueError, TypeError):
                form_data[field] = specs["default"]

        # Handle categorical fields
        for field, options in DATA_SPECS["categorical"].items():
            value = request.form.get(field, options[0])
            # Convert to uppercase for specific fields
            if field in ["Cust_State", "Warehouse_Region"]:
                value = value.upper()
            form_data[field] = value if value in options else options[0]

        # Create DataFrame
        input_df = pd.DataFrame([form_data])

        # One-hot encode categorical variables
        input_df = pd.get_dummies(input_df)

        # Ensure all expected columns exist
        for col in feature_columns:
            if col not in input_df.columns:
                input_df[col] = 0

        # Reorder columns to match training data
        input_df = input_df[feature_columns]

        # Final check - ensure all values are numeric
        for col in input_df.columns:
            input_df[col] = pd.to_numeric(input_df[col], errors="coerce").fillna(0)

        # Make prediction
        prediction = model.predict(input_df)[0]

        return render_template("result.html", prediction=prediction, features=form_data)

    except Exception as e:
        return f"Prediction Error: {str(e)}", 400


# Create result.html for displaying the results
with open("templates/result.html", "w") as f:
    f.write(
        """
<!DOCTYPE html>
<html>
<head>
    <title>Prediction Result</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; }
        .result { background-color: #f9f9f9; padding: 15px; border-radius: 4px; margin: 20px 0; }
        .feature-list { background-color: #f0f0f0; padding: 15px; border-radius: 4px; }
        .back-btn { background: #2196F3; color: white; padding: 10px 15px; border: none; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }
        .back-btn:hover { background: #0b7dda; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Prediction Result</h1>
        
        <div class="result">
            <h2>Storage Section: {{ prediction }}</h2>
            
            {% if probabilities %}
            <h3>Prediction Probabilities:</h3>
            <ul>
                {% for class, prob in probabilities.items() %}
                <li>Class {{ class }}: {{ "%.4f"|format(prob) }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        
        <div class="feature-list">
            <h3>Input Features:</h3>
            <ul>
                {% for feature, value in features.items() %}
                <li>{{ feature }}: {{ value }}</li>
                {% endfor %}
                <br>
                <li>Raw Input: {{ raw_input[0] }}</li>
            </ul>
        </div>
        
        <a href="/" class="back-btn">Make Another Prediction</a>
    </div>
</body>
</html>
    """
    )

if __name__ == "__main__":
    app.run(debug=True)
