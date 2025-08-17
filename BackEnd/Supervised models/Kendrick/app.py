from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib
import numpy as np
import xgboost
# Load model
# Load artifacts
artifacts = joblib.load('best_model.joblib')
model = artifacts['model']
threshold = artifacts['threshold']

# Feature list
FEATURES = [
    'Inventory_Level',
    'Inventory_Turnover',
    'Units_Sold',
    'Demand_Forecast',
    'Inventory_Lag_1',
    'Turnover_Lag_1'
]

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template("index.html", features=FEATURES, result=None)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Collect inputs from form
        input_data = {}
        for feature in FEATURES:
            value = request.form.get(feature)
            input_data[feature] = np.nan if not value or value.strip() == '' else float(value)

        # Convert to DataFrame
        df = pd.DataFrame([input_data], columns=FEATURES)

        # Make prediction
        prediction = model.predict(df)[0]
        # Apply threshold
        if prediction >= threshold:
            prediction = 1  # Dispose
        else:
            prediction = 0  # Keep
        print(f"Prediction: {prediction}")  # Debugging line
        result = "Keep" if prediction == 0 else "Dispose"

        return render_template("index.html", features=FEATURES, result=result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
