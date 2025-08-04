from flask import Flask, request, render_template, jsonify
import joblib
import numpy as np
import pandas as pd
import pickle

app = Flask(__name__)

# Load model and preprocessor
model = joblib.load('model/best_model.pkl')
with open('model/preprocessor.pkl', 'rb') as f:
    preprocessor_data = pickle.load(f)

# Extract preprocessor components
label_encoder = preprocessor_data['label_encoder']
feature_columns = preprocessor_data['feature_columns']
top_products = preprocessor_data['top_products']
product_mapping = preprocessor_data['product_mapping']
unique_segments = preprocessor_data['unique_segments']
unique_countries = preprocessor_data['unique_countries']
sample_data = preprocessor_data['sample_data']

@app.route('/')
def home():
    return render_template('index.html', 
                         products=top_products,
                         segments=unique_segments,
                         countries=unique_countries)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from form
        order_year = int(request.form['order_year'])
        order_month = int(request.form['order_month'])
        product_name = request.form['product_name']
        order_country = request.form['order_country']
        customer_segment = request.form['customer_segment']
        
        # Calculate Order YearMonth
        order_yearmonth = order_year * 100 + order_month
        
        # Get product stats from sample data
        product_stats = sample_data[sample_data['Product Name'] == product_name].iloc[0]
        
        # Create input data
        input_data = {
            'Order YearMonth': order_yearmonth,
            'Product Name': product_mapping[product_name],
            'Mean Discount Rate': product_stats['Mean Discount Rate'],
            'Total Discount Given': product_stats['Total Discount Given'],
            'Order Frequency': product_stats['Order Frequency'],
            'Avg Quantity per Order': product_stats['Avg Quantity per Order']
        }
        
        # Add Customer Segment one-hot encoding
        input_data['Customer Segment_Corporate'] = 1 if customer_segment == 'Corporate' else 0
        input_data['Customer Segment_Home Office'] = 1 if customer_segment == 'Home Office' else 0
        
        # Add Order Country one-hot encoding (initialize all to 0)
        for col in feature_columns:
            if col.startswith('Order Country_'):
                input_data[col] = 0
        
        # Set the correct country to 1
        country_col = f'Order Country_{order_country}'
        if country_col in feature_columns:
            input_data[country_col] = 1
        
        # Create DataFrame with correct column order
        input_df = pd.DataFrame([input_data])
        input_df = input_df.reindex(columns=feature_columns, fill_value=0)
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        
        return render_template('index.html', 
                             prediction=round(prediction, 2),
                             products=top_products,
                             segments=unique_segments,
                             countries=unique_countries)
    
    except Exception as e:
        return render_template('index.html', 
                             error=f"Error: {str(e)}",
                             products=top_products,
                             segments=unique_segments,
                             countries=unique_countries)

if __name__ == '__main__':
    app.run(debug=True)
