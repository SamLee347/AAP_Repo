from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np
import pandas as pd
import os

# Initialize Flask app
app = Flask(__name__)

# Load the trained model
with open('storage_prediction_model.pkl', 'rb') as file:
    model = pickle.load(file)

# Define your original categorical features and their possible values
# Replace these with your actual categorical features and their values
categorical_features = {
    'Priority': ['High','Low','Medium'],
    'Product_Type': ['Clothing','Technology','Other','Sports and Fitness'],
    'Size': ['Large','Medium','Small']
}

# Define any numerical features that aren't one-hot encoded
numerical_features = ['Order_Quantity', 'Weight']  # Replace with your actual numerical features

# Generate all one-hot encoded column names
one_hot_columns = []
for feature, values in categorical_features.items():
    for value in values:
        one_hot_columns.append(f"{feature}_{value}")

# Combine with numerical features to get all feature names
all_feature_names = one_hot_columns + numerical_features

@app.route('/')
def home():
    """Render the home page with a prediction form"""
    return render_template('index.html', 
                          categorical_features=categorical_features,
                          numerical_features=numerical_features)

@app.route('/predict', methods=['POST'])
def predict():
    """API endpoint for making predictions"""
    if request.is_json:
        # Handle API requests (JSON)
        data = request.get_json()
        features_array = process_input_to_features(data)
        
        # Make prediction
        prediction = model.predict(features_array).tolist()
        
        # Get prediction probabilities if it's a classification task
        try:
            probabilities = model.predict_proba(features_array).tolist()
            return jsonify({
                'prediction': prediction,
                'probability': probabilities
            })
        except:
            return jsonify({'prediction': prediction})
    else:
        # Handle form submissions
        form_data = {}
        # Get numerical features
        for feature in numerical_features:
            form_data[feature] = request.form.get(feature, 0)
        
        # Get categorical features
        for feature in categorical_features:
            form_data[feature] = request.form.get(feature)
        
        # Process the input
        features_array = process_input_to_features(form_data)
        
        # Make prediction
        prediction = model.predict(features_array)[0]
        
        # Get prediction probabilities if it's a classification task
        try:
            probabilities = model.predict_proba(features_array)[0]
            class_labels = model.classes_
            prob_dict = {str(label): float(prob) for label, prob in zip(class_labels, probabilities)}
            
            # Create a readable version of the input for display
            readable_input = {**{f: form_data[f] for f in numerical_features},
                             **{f: form_data[f] for f in categorical_features}}
            
            return render_template('result.html', 
                                  prediction=prediction, 
                                  probabilities=prob_dict,
                                  features=readable_input,
                                  raw_input=features_array)
        except:
            # Create a readable version of the input for display
            readable_input = {**{f: form_data[f] for f in numerical_features},
                             **{f: form_data[f] for f in categorical_features}}
            
            return render_template('result.html', 
                                  prediction=prediction,
                                  features=readable_input,
                                  raw_input=features_array)

def process_input_to_features(input_data):
    """Convert input data to one-hot encoded features array"""
    # Initialize a dictionary with all one-hot features set to 0
    features_dict = {col: 0 for col in all_feature_names}
    
    # Set one-hot encoded features
    for feature, values in categorical_features.items():
        if feature in input_data:
            selected_value = input_data[feature]
            one_hot_col = f"{feature}_{selected_value}"
            if one_hot_col in features_dict:
                features_dict[one_hot_col] = 1

    # Set numerical features
    for feature in numerical_features:
        if feature in input_data:
            features_dict[feature] = float(input_data[feature])
    
    # Convert to array in the correct order
    features_array = np.array([features_dict[col] for col in all_feature_names]).reshape(1, -1)
    return features_array


# Create result.html
with open('templates/result.html', 'w') as f:
    f.write('''
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
    ''')

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)