from flask import Flask, render_template, request, jsonify
import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Import your functions from the model_functions.py file
from model_functions import forecast_generalized_category, forecast_generalized_category_auto, category_mapping

app = Flask(__name__)

# Load model and preprocessor on startup
try:
    # Load the XGBoost model (matching your LSFModel3.ipynb filename)
    loaded_model = joblib.load('model/salesforecast(categories).pkl')
    with open('model/salesforecast_preprocessor.pkl', 'rb') as f:
        preprocessor_data = pickle.load(f)
    
    print("✅ Model loaded successfully!")
    print(f"Model type: {preprocessor_data['model_type']}")
    print(f"Available categories: {preprocessor_data['unique_categories']}")
    print(f"Reference date: {preprocessor_data['reference_date']}")
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    loaded_model = None
    preprocessor_data = None

@app.route('/')
def home():
    """Home page with hierarchical forecasting"""
    if not loaded_model or not preprocessor_data:
        return render_template('error.html', error="Model not loaded. Please check model files.")
    
    # Create category info for display
    available_categories = preprocessor_data['unique_categories']
    category_info = {}
    
    for main_cat, subcats in category_mapping.items():
        available_subcats = [cat for cat in subcats if cat in available_categories]
        category_info[main_cat] = {
            'subcategories': subcats,
            'available': available_subcats,
            'coverage': len(available_subcats) / len(subcats) * 100
        }
    
    return render_template('forecast.html', 
                         category_mapping=category_mapping,
                         category_info=category_info)

@app.route('/predict', methods=['POST'])
def predict():
    """API endpoint for hierarchical predictions with auto-calculated parameters"""
    try:
        data = request.get_json()
        
        # Use the new auto-calculation function
        result = forecast_generalized_category_auto(
            model=loaded_model,
            le_category=preprocessor_data['label_encoder_category'],
            reference_date=preprocessor_data['reference_date'],
            future_year_month=data['month'],
            generalized_category=data['category'],
            category_mapping=category_mapping,
            feature_columns=preprocessor_data['feature_columns'],
            description=data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'result': {
                'generalized_category': result['generalized_category'],
                'total_prediction': round(result['total_prediction'], 2),
                'mean_prediction': round(result['mean_prediction'], 2),
                'subcategory_predictions': result['subcategory_predictions'],
                'num_subcategories': result['num_subcategories'],
                'description': result['description'],
                'formatted_month': pd.to_datetime(data['month']).strftime('%B %Y'),
                'success_message': f"✅ SUCCESS: {result['total_prediction']:.2f} total units predicted"
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/model_info')
def get_model_info():
    """API endpoint to get model information"""
    if not preprocessor_data:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'model_type': preprocessor_data['model_type'],
        'performance': preprocessor_data['model_performance'],
        'categories': preprocessor_data['unique_categories'],
        'reference_date': preprocessor_data['reference_date'].isoformat(),
        'feature_count': len(preprocessor_data['feature_columns'])
    })

if __name__ == '__main__':
    app.run(debug=True)
