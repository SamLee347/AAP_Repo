# imports
import base64
import os
from google import genai
from google.genai import types

import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from Database.db import SessionLocal
from Database_Table.order import Order
from Database_Table.inventory import Inventory

# GenAI integration

# To run this code you need to install the following dependencies:
# pip install google-genai

class ForecastService:
    def __init__(self, model_path: str, preprocessor_path: str):
        """Initialize the forecasting service with trained model"""
        self.model = joblib.load(model_path)
        
        with open(preprocessor_path, 'rb') as f:
            self.preprocessor_data = pickle.load(f)
        
        self.le_category = self.preprocessor_data['label_encoder_category']
        self.feature_columns = self.preprocessor_data['feature_columns']
        self.reference_date = self.preprocessor_data['reference_date']
        
        # Category mapping from your notebook
        self.category_mapping = {
            "Clothing": ["Cleats", "Men's Footwear", "Women's Apparel"],
            "Technology": ["Electronics", "Computers", "Cameras", "Video Games"],
            "Sports and Fitness": ["Cardio Equipment", "Shop By Sport", "Camping & Hiking", 
                                  "Fishing", "Water Sports", "Indoor/Outdoor Games"],
            "Other": ["Garden", "Pet Supplies"]
        }
        
        # Map user categories to your model categories
        self.user_category_mapping = {
            "Office Supplies": "Other",
            "Technology": "Technology", 
            "Furniture": "Other",
            "Sporting": "Sports and Fitness"
        }

    def forecast_category_demand(self, category_name: str, future_year_month: str, 
                               product_category_id: int = 40, avg_price: float = 25.50,
                               customer_segment: str = "Consumer", discount_rate: float = 0.08) -> Dict[str, Any]:
        """Forecast demand for a specific category"""
        try:
            # Map user category to model category
            mapped_category = self.user_category_mapping.get(category_name, "Other")
            
            # Parse future date
            future_date = pd.to_datetime(future_year_month)
            
            # Calculate time features
            months_since_start = ((future_date - self.reference_date).days / 30.44)
            
            # Get specific categories for the mapped category
            specific_categories = self.category_mapping.get(mapped_category, [mapped_category])
            
            total_prediction = 0
            valid_predictions = []
            category_predictions = []
            
            for specific_cat in specific_categories:
                if specific_cat in self.le_category.classes_:
                    # Create test data
                    test_data = {
                        'Category Name': specific_cat,
                        'Average Product Price': avg_price,
                        'Customer Segment': customer_segment,
                        'Order Item Discount Rate': discount_rate,
                        'Year': future_date.year,
                        'Month': future_date.month,
                        'Quarter': future_date.quarter,
                        'Months_Since_Start': int(months_since_start),
                        'Month_Sin': np.sin(2 * np.pi * future_date.month / 12),
                        'Month_Cos': np.cos(2 * np.pi * future_date.month / 12),
                        'Year_Trend': future_date.year - self.reference_date.year
                    }
                    
                    # Create DataFrame and preprocess
                    test_df = pd.DataFrame([test_data])
                    test_df['Category Name'] = self.le_category.transform(test_df['Category Name'])
                    test_df = pd.get_dummies(test_df, columns=['Customer Segment'], drop_first=True)
                    test_df = test_df.reindex(columns=self.feature_columns, fill_value=0)
                    
                    # Make prediction
                    prediction = self.model.predict(test_df)[0]
                    total_prediction += prediction
                    valid_predictions.append(prediction)
                    category_predictions.append({
                        'subcategory': specific_cat,
                        'predicted_demand': round(prediction, 2)
                    })
            
            if not valid_predictions:
                return {
                    "success": False,
                    "error": f"No valid subcategories found for {category_name}",
                    "total_predicted_demand": 0
                }
            
            return {
                "success": True,
                "category": category_name,
                "target_month": future_year_month,
                "total_predicted_demand": round(total_prediction, 2),
                "average_per_subcategory": round(total_prediction / len(valid_predictions), 2),
                "subcategory_breakdown": category_predictions,
                "parameters_used": {
                    "avg_price": avg_price,
                    "customer_segment": customer_segment,
                    "discount_rate": discount_rate
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_predicted_demand": 0
            }

    def identify_declining_categories(self, analysis_months: int = 6, 
                                    decline_threshold: float = -10.0, 
                                    forecast_months: int = 3) -> Dict[str, Any]:
        """Identify categories with declining trends"""
        try:
            db = SessionLocal()
            
            # Get historical data from database
            current_date = datetime.now()
            analysis_start = pd.Timestamp(current_date) - pd.DateOffset(months=analysis_months)
            
            # Query order data for trend analysis
            orders = db.query(Order).join(Inventory).filter(
                Order.DateOrdered >= analysis_start.strftime('%Y-%m-%d')
            ).all()
            
            if not orders:
                return {
                    "success": False,
                    "error": "No historical data available for analysis",
                    "declining_categories": []
                }
            
            # Analyze trends (simplified version)
            category_trends = {}
            declining_categories = []
            
            # Group by category and calculate trends
            for order in orders:
                category = order.inventory_item.ItemCategory
                if category not in category_trends:
                    category_trends[category] = []
                category_trends[category].append(order.OrderQuantity)
            
            # Calculate decline percentage
            for category, quantities in category_trends.items():
                if len(quantities) >= 2:
                    recent_avg = np.mean(quantities[-2:])
                    early_avg = np.mean(quantities[:2])
                    
                    if early_avg > 0:
                        decline_percent = ((recent_avg - early_avg) / early_avg) * 100
                        
                        if decline_percent <= decline_threshold:
                            declining_categories.append({
                                "category": category,
                                "decline_percentage": round(decline_percent, 2),
                                "recent_average_demand": round(recent_avg, 2),
                                "early_average_demand": round(early_avg, 2)
                            })
            
            db.close()
            
            return {
                "success": True,
                "analysis_period_months": analysis_months,
                "decline_threshold": decline_threshold,
                "declining_categories": declining_categories,
                "total_categories_analyzed": len(category_trends)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "declining_categories": []
            }

    def get_most_used_category(self, start_date: str, end_date: str, 
                             metric: str = "total_quantity") -> Dict[str, Any]:
        """Get the most used category in a time period"""
        try:
            db = SessionLocal()
            
            # Query orders in the date range
            orders = db.query(Order).join(Inventory).filter(
                Order.DateOrdered >= start_date + '-01',
                Order.DateOrdered <= end_date + '-31'
            ).all()
            
            if not orders:
                return {
                    "success": False,
                    "error": "No data available for the specified period",
                    "top_category": None
                }
            
            # Calculate metrics by category
            category_metrics = {}
            
            for order in orders:
                category = order.inventory_item.ItemCategory
                if category not in category_metrics:
                    category_metrics[category] = {
                        "total_quantity": 0,
                        "order_count": 0,
                        "total_sales": 0
                    }
                
                category_metrics[category]["total_quantity"] += order.OrderQuantity
                category_metrics[category]["order_count"] += 1
                category_metrics[category]["total_sales"] += order.Sales
            
            # Calculate the requested metric
            for category in category_metrics:
                data = category_metrics[category]
                if metric == "average_monthly":
                    # Calculate months between dates
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
                    data["average_monthly"] = data["total_quantity"] / months
                elif metric == "growth_rate":
                    # Simplified growth rate calculation
                    data["growth_rate"] = data["total_quantity"] / data["order_count"]
            
            # Find top category
            if metric == "total_quantity":
                top_category = max(category_metrics.items(), 
                                 key=lambda x: x[1]["total_quantity"])
            elif metric == "average_monthly":
                top_category = max(category_metrics.items(), 
                                 key=lambda x: x[1]["average_monthly"])
            else:  # growth_rate
                top_category = max(category_metrics.items(), 
                                 key=lambda x: x[1]["growth_rate"])
            
            db.close()
            
            return {
                "success": True,
                "period": f"{start_date} to {end_date}",
                "metric_used": metric,
                "top_category": {
                    "name": top_category[0],
                    "metrics": top_category[1]
                },
                "all_categories": category_metrics
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "top_category": None
            }

# Initialize the service
forecast_service = ForecastService(
    model_path="Supervised models/ShernFai/model/salesforecast(categories).pkl",
    preprocessor_path="Supervised models/ShernFai/model/salesforecast_preprocessor.pkl"
)


class GeminiForecaster:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.forecast_service = forecast_service
        
        # Define function schemas
        self.function_schemas = [
            {
                "name": "forecast_category_demand",
                "description": "Predicts future demand for a specific category using the XGBoost time series model.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category_name": { 
                            "type": "string", 
                            "description": "Product category name",
                            "enum": ["Office Supplies", "Technology", "Furniture", "Sporting"] 
                        },
                        "future_year_month": { 
                            "type": "string", 
                            "description": "Target month for prediction in YYYY-MM format" 
                        },
                        "product_category_id": { "type": "integer", "default": 40 },
                        "avg_price": { "type": "number", "default": 25.50 },
                        "customer_segment": { 
                            "type": "string", 
                            "enum": ["Consumer", "Corporate", "Home Office"],
                            "default": "Consumer" 
                        },
                        "discount_rate": { "type": "number", "default": 0.08 }
                    },
                    "required": ["category_name", "future_year_month"]
                }
            },
            {
                "name": "identify_declining_categories",
                "description": "Identifies categories with declining demand trends based on historical data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "analysis_months": { 
                            "type": "integer", 
                            "description": "Number of historical months to analyze for trend",
                            "default": 6 
                        },
                        "decline_threshold": { 
                            "type": "number", 
                            "description": "Minimum decline percentage to consider as declining",
                            "default": -10.0 
                        },
                        "forecast_months": { 
                            "type": "integer", 
                            "description": "Number of future months to predict for trend confirmation",
                            "default": 3 
                        }
                    }
                }
            },
            {
                "name": "get_most_used_category",
                "description": "Returns the most used category within a given time period with statistical backing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": { "type": "string", "description": "Start date in YYYY-MM format" },
                        "end_date": { "type": "string", "description": "End date in YYYY-MM format" },
                        "metric": { 
                            "type": "string", 
                            "enum": ["total_quantity", "average_monthly", "growth_rate"],
                            "default": "total_quantity" 
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            }
        ]

    def execute_function(self, function_name: str, parameters: Dict) -> Dict:
        """Execute the requested function with parameters"""
        if function_name == "forecast_category_demand":
            return self.forecast_service.forecast_category_demand(**parameters)
        elif function_name == "identify_declining_categories":
            return self.forecast_service.identify_declining_categories(**parameters)
        elif function_name == "get_most_used_category":
            return self.forecast_service.get_most_used_category(**parameters)
        else:
            return {"error": f"Unknown function: {function_name}"}

    def chat_with_functions(self, user_message: str) -> str:
        """Chat with function calling capabilities"""
        try:
            # Create the conversation with system prompt
            contents = [
                types.Content(
                    role="system",
                    parts=[types.Part.from_text(
                        "You are an AI assistant that helps users understand product usage trends and statistics through function calling. "
                        "When users ask for predictions, trends, or category analysis, use the appropriate functions to provide accurate data-driven insights. "
                        "Always interpret the results and provide meaningful business insights."
                    )]
                ),
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(user_message)]
                )
            ]

            # Configure generation with function calling
            config = types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=self.function_schemas)],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfig.Mode.AUTO
                    )
                )
            )

            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )

            # Check if function calls were made
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Execute the function call
                        function_name = part.function_call.name
                        parameters = dict(part.function_call.args) if part.function_call.args else {}
                        
                        # Execute function
                        function_result = self.execute_function(function_name, parameters)
                        
                        # Add function result to conversation and get final response
                        contents.append(types.Content(
                            role="function",
                            parts=[types.Part.from_function_response(
                                name=function_name,
                                response=function_result
                            )]
                        ))
                        
                        # Get final interpretation
                        final_response = self.client.models.generate_content(
                            model=self.model,
                            contents=contents,
                            config=config
                        )
                        
                        return final_response.text
                    else:
                        return response.text
            
            return response.text if response.text else "I couldn't process your request. Please try again."

        except Exception as e:
            return f"Error processing your request: {str(e)}"

# Initialize the forecaster
def create_forecaster():
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw")
    return GeminiForecaster(api_key)

def query_gemini(user_query: str) -> str:
    """Main function to query the Gemini forecaster"""
    forecaster = create_forecaster()
    return forecaster.chat_with_functions(user_query)

# Test function
def test_forecasting_queries():
    """Test various forecasting queries"""
    test_queries = [
        "Predict the amount of quantity I would need for the Sporting Category for March 2025",
        "Which categories are declining in demand?",
        "What was the most used category between 2024-01 and 2024-12?",
        "Forecast Technology demand for June 2025 with high-end pricing",
        "Show me categories that might need inventory reduction"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("="*60)
        response = query_gemini(query)
        print(f"📊 Response: {response}")
        print("="*60)

if __name__ == "__main__":
    test_forecasting_queries()
