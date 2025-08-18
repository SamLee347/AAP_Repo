import pandas as pd
import numpy as np

def load_dataset_stats():
    """
    Load the original dataset and calculate average statistics for each category
    Returns: Dictionary with category statistics
    """
    try:
        # Load the dataset
        df = pd.read_csv('dataset/supplychain.csv')
        
        # Calculate statistics for each category
        category_stats = {}
        for category in df['Category Name'].unique():
            cat_data = df[df['Category Name'] == category]
            category_stats[category] = {
                'avg_price': cat_data['Average Product Price'].mean(),
                'most_common_segment': cat_data['Customer Segment'].mode()[0],
                'avg_discount_rate': cat_data['Order Item Discount Rate'].mean()
            }
        
        return category_stats
    except Exception as e:
        print(f"Warning: Could not load dataset stats: {e}")
        # Return default values if dataset can't be loaded
        return {
            'default': {
                'avg_price': 25.50,
                'most_common_segment': 'Consumer',
                'avg_discount_rate': 0.08
            }
        }

def forecast_generalized_category_auto(model, le_category, reference_date, future_year_month, 
                                     generalized_category, category_mapping, feature_columns, description=""):
    """
    Forecast demand for a generalized category with automatic parameter calculation
    """
    # Load dataset statistics
    dataset_stats = load_dataset_stats()
    
    # Get subcategories for this generalized category
    subcategories = category_mapping.get(generalized_category, [])
    
    predictions = {}
    total_demand = 0
    
    for subcategory in subcategories:
        # Get statistics for this subcategory (or use defaults)
        if subcategory in dataset_stats:
            stats = dataset_stats[subcategory]
        else:
            stats = dataset_stats.get('default', {
                'avg_price': 25.50,
                'most_common_segment': 'Consumer', 
                'avg_discount_rate': 0.08
            })
        
        # Use the existing forecast function with calculated parameters
        prediction = forecast_future_demand(
            model=model,
            le_category=le_category,
            reference_date=reference_date,
            future_year_month=future_year_month,
            category_name=subcategory,
            avg_price=stats['avg_price'],
            customer_segment=stats['most_common_segment'],
            discount_rate=stats['avg_discount_rate'],
            feature_columns=feature_columns
        )
        
        predictions[subcategory] = {
            'prediction': round(float(prediction), 2),
            'avg_price': round(float(stats['avg_price']), 2),
            'customer_segment': str(stats['most_common_segment']),
            'discount_rate': round(float(stats['avg_discount_rate']), 3)
        }
        total_demand += prediction
    
    # Calculate mean prediction
    mean_prediction = total_demand / len(subcategories) if subcategories else 0
    
    return {
        'generalized_category': str(generalized_category),
        'total_prediction': round(float(total_demand), 2),
        'mean_prediction': round(float(mean_prediction), 2),
        'subcategory_predictions': predictions,
        'num_subcategories': int(len(subcategories)),
        'description': str(description)
    }

def forecast_future_demand(model, le_category, reference_date, future_year_month, 
                          category_name, avg_price, customer_segment, discount_rate, feature_columns):
    """
    Forecast demand for individual category (copied from LSFModel3.ipynb)
    """
    # Parse the future date
    future_date = pd.to_datetime(future_year_month)
    
    # Calculate time features for the future date
    months_since_start = ((future_date - reference_date).days / 30.44)
    
    # Create test data with numerical time features (removed Product Category Id)
    test_data = {
        'Category Name': category_name,
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
    
    # Encode category
    test_df['Category Name'] = le_category.transform(test_df['Category Name'])
    
    # One-hot encode customer segment
    test_df = pd.get_dummies(test_df, columns=['Customer Segment'], drop_first=True)
    
    # Ensure same columns as training (crucial!)
    test_df = test_df.reindex(columns=feature_columns, fill_value=0)
    
    # Make prediction
    prediction = model.predict(test_df)[0]
    
    return float(max(0, prediction))

def forecast_generalized_category(model, le_category, reference_date, future_year_month,
                                generalized_category, avg_price, customer_segment, 
                                discount_rate, category_mapping, feature_columns):
    """
    Forecast demand for a generalized category (copied from LSFModel3.ipynb)
    """
    if generalized_category not in category_mapping:
        raise ValueError(f"Unknown generalized category: {generalized_category}")
    
    specific_categories = category_mapping[generalized_category]
    predictions = []
    valid_predictions = []
    
    print(f"\n🔮 Forecasting for {generalized_category}")
    print(f"📋 Subcategories: {specific_categories}")
    print("="*50)
    
    for specific_cat in specific_categories:
        try:
            # Check if specific category exists in trained model
            if specific_cat in le_category.classes_:
                prediction = forecast_future_demand(
                    model=model,
                    le_category=le_category,
                    reference_date=reference_date,
                    future_year_month=future_year_month,
                    category_name=specific_cat,
                    avg_price=avg_price,
                    customer_segment=customer_segment,
                    discount_rate=discount_rate,
                    feature_columns=feature_columns
                )
                predictions.append({
                    'category': specific_cat,
                    'prediction': prediction
                })
                valid_predictions.append(prediction)
                print(f"✅ {specific_cat}: {prediction:.2f} units")
            else:
                print(f"⚠️  {specific_cat}: Not in trained categories, skipping")
                
        except Exception as e:
            print(f"❌ {specific_cat}: Error - {e}")
    
    if not valid_predictions:
        raise ValueError(f"No valid predictions for {generalized_category}")
    
    # Calculate aggregated metrics
    total_prediction = sum(valid_predictions)
    mean_prediction = total_prediction / len(valid_predictions)
    
    print("="*50)
    print(f"📊 AGGREGATED RESULTS for {generalized_category}:")
    print(f"   • Total predicted demand: {total_prediction:.2f} units")
    print(f"   • Average per subcategory: {mean_prediction:.2f} units")
    print(f"   • Number of subcategories: {len(valid_predictions)}")
    
    return {
        'generalized_category': str(generalized_category),
        'total_prediction': float(total_prediction),
        'mean_prediction': float(mean_prediction),
        'subcategory_predictions': predictions,
        'num_subcategories': int(len(valid_predictions))
    }

# Category mapping from your LSFModel3.ipynb
category_mapping = {
    "Clothing": ["Cleats", "Men's Footwear", "Women's Apparel"],
    "Technology": ["Electronics", "Computers", "Cameras", "Video Games"],
    "Sports and Fitness": ["Cardio Equipment", "Shop By Sport", "Camping & Hiking", 
                          "Fishing", "Water Sports", "Indoor/Outdoor Games"],
    "Other": ["Garden", "Pet Supplies"]
}
