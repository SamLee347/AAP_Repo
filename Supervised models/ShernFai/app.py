from flask import Flask, render_template, request, jsonify
import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

app = Flask(__name__)

try:
    model_timeseries = joblib.load('model\salesforecast_model.pkl')
    with open('model\salesforecast_preprocessor.pkl', 'rb') as f:
        preprocessor_data = pickle.load(f)
    
    le_category = preprocessor_data['label_encoder_category']
    reference_date = preprocessor_data['reference_date']
    unique_categories = preprocessor_data['unique_categories']
    feature_columns = preprocessor_data['feature_columns']
    
    print("✅ Model loaded successfully!")
    # print(f"Available categories: {unique_categories}")
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model_timeseries = None

def forecast_future_demand(model, le_category, reference_date, future_year_month, 
                          category_name, product_category_id, avg_price, 
                          customer_segment, discount_rate):
    """Your existing forecast function from the notebook"""
    
    # Parse the future date
    future_date = pd.to_datetime(future_year_month)
    
    # Calculate time features for the future date
    months_since_start = ((future_date - reference_date).days / 30.44)
    
    # Create test data with numerical time features
    test_data = {
        'Category Name': category_name,
        'Product Category Id': product_category_id,
        'Average Product Price': avg_price,
        'Customer Segment': customer_segment,
        'Order Item Discount Rate': discount_rate,
        # Time features (numerical - can handle ANY future date!)
        'Year': future_date.year,
        'Month': future_date.month,
        'Quarter': future_date.quarter,
        'Months_Since_Start': int(months_since_start),
        'Month_Sin': np.sin(2 * np.pi * future_date.month / 12),
        'Month_Cos': np.cos(2 * np.pi * future_date.month / 12),
        'Year_Trend': future_date.year - reference_date.year
    }
    
    # Create DataFrame
    test_df = pd.DataFrame([test_data])
    
    # Handle unknown category
    if category_name not in le_category.classes_:
        print(f"Unknown category '{category_name}' - using default: {le_category.classes_[0]}")
        test_df['Category Name'] = le_category.classes_[0]
        category_name = le_category.classes_[0]
    
    # Encode category
    test_df['Category Name'] = le_category.transform(test_df['Category Name'])
    
    # One-hot encode customer segment
    test_df = pd.get_dummies(test_df, columns=['Customer Segment'], drop_first=True)
    
    # Ensure same columns as training (crucial!)
    test_df = test_df.reindex(columns=feature_columns, fill_value=0)
    
    # Make prediction
    prediction = model.predict(test_df)[0]
    
    return prediction, category_name

@app.route('/')
def index():
    return render_template('predict.html', 
                         categories=unique_categories if model_timeseries else [],
                         model_loaded=model_timeseries is not None)

@app.route('/predict', methods=['POST'])
def predict():
    if not model_timeseries:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        # Get form data
        category_name = request.form.get('category', unique_categories[0])
        future_month = request.form.get('month', '2025-03')
        product_category_id = int(request.form.get('product_category_id', 40))
        avg_price = float(request.form.get('avg_price', 25.50))
        customer_segment = request.form.get('customer_segment', 'Consumer')
        discount_rate = float(request.form.get('discount_rate', 0.08))
        
        # Make prediction using your function
        prediction, actual_category = forecast_future_demand(
            model=model_timeseries,
            le_category=le_category,
            reference_date=reference_date,
            future_year_month=future_month,
            category_name=category_name,
            product_category_id=product_category_id,
            avg_price=avg_price,
            customer_segment=customer_segment,
            discount_rate=discount_rate
        )
        
        result = {
            'prediction': round(prediction, 2),
            'category': actual_category,
            'month': future_month,
            'inputs': {
                'product_category_id': product_category_id,
                'avg_price': avg_price,
                'customer_segment': customer_segment,
                'discount_rate': discount_rate
            },
            'model_performance': preprocessor_data['model_performance']
        }
        
        return render_template('result.html', result=result)
        
    except Exception as e:
        return render_template('predict.html', 
                             categories=unique_categories,
                             error=str(e),
                             model_loaded=True)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
