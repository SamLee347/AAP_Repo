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
        try:
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
            
            print("✅ ForecastService initialized successfully")
            print(f"   Model loaded: {len(self.le_category.classes_)} categories available")
            print(f"   Reference date: {self.reference_date}")
            
        except Exception as e:
            print(f"❌ Error initializing ForecastService: {e}")
            raise

    def get_historical_insights(self, category_name: str, months_back: int = 6) -> Dict[str, Any]:
        """Get historical data insights for intelligent parameter defaults"""
        try:
            db = SessionLocal()
            
            # Calculate date range
            current_date = datetime.now()
            start_date = pd.Timestamp(current_date) - pd.DateOffset(months=months_back)
            
            # Query historical data
            orders = db.query(Order).join(Inventory).filter(
                Order.DateOrdered >= start_date.strftime('%Y-%m-%d'),
                Inventory.ItemCategory == category_name
            ).all()
            
            if not orders:
                # Return default values if no historical data
                return {
                    "avg_price": 25.50,
                    "avg_discount_rate": 0.08,
                    "dominant_segment": "Consumer",
                    "total_orders": 0,
                    "data_available": False
                }
            
            # Calculate insights
            prices = [order.Price for order in orders if order.Price]
            discount_rates = [order.OrderItemDiscountRate for order in orders if order.OrderItemDiscountRate]
            segments = [order.CustomerSegment for order in orders if order.CustomerSegment]
            
            insights = {
                "avg_price": np.mean(prices) if prices else 25.50,
                "avg_discount_rate": np.mean(discount_rates) if discount_rates else 0.08,
                "dominant_segment": max(set(segments), key=segments.count) if segments else "Consumer",
                "total_orders": len(orders),
                "data_available": True
            }
            
            db.close()
            return insights
            
        except Exception as e:
            db.close()
            print(f"Warning: Could not get historical insights: {e}")
            return {
                "avg_price": 25.50,
                "avg_discount_rate": 0.08,
                "dominant_segment": "Consumer",
                "total_orders": 0,
                "data_available": False
            }

    def forecast_category_demand(self, category_name: str, future_year_month: str, 
                               scenario: str = "standard", aggregation_method: str = "average",
                               **kwargs) -> Dict[str, Any]:
        """
        Single unified forecasting function with database intelligence and scenario support
        
        Args:
            category_name: Product category name
            future_year_month: Target month in YYYY-MM format
            scenario: "conservative", "standard", or "optimistic"
            aggregation_method: "average", "median", or "recent"
            **kwargs: Override parameters (avg_price, customer_segment, discount_rate)
        """
        try:
            # Map user category to model category
            mapped_category = self.user_category_mapping.get(category_name, "Other")
            
            # Get historical insights for intelligent defaults
            insights = self.get_historical_insights(category_name)
            
            # Use historical insights or kwargs for parameters
            avg_price = kwargs.get('avg_price', insights['avg_price'])
            customer_segment = kwargs.get('customer_segment', insights['dominant_segment'])
            discount_rate = kwargs.get('discount_rate', insights['avg_discount_rate'])
            
            # Apply scenario adjustments
            if scenario == "conservative":
                avg_price *= 0.95  # Lower price expectation
                discount_rate *= 1.2  # Higher discount expectation
            elif scenario == "optimistic":
                avg_price *= 1.05  # Higher price expectation
                discount_rate *= 0.8  # Lower discount expectation
            
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
            
            # Calculate final aggregation
            if aggregation_method == "median":
                final_prediction = np.median(valid_predictions) * len(valid_predictions)
            elif aggregation_method == "recent":
                # Weight recent predictions more heavily (simple approach)
                final_prediction = total_prediction * 1.1 if scenario == "optimistic" else total_prediction * 0.9
            else:  # average (default)
                final_prediction = total_prediction
            
            return {
                "success": True,
                "category": category_name,
                "target_month": future_year_month,
                "scenario": scenario,
                "total_predicted_demand": round(final_prediction, 2),
                "average_per_subcategory": round(final_prediction / len(valid_predictions), 2),
                "subcategory_breakdown": category_predictions,
                "parameters_used": {
                    "avg_price": round(avg_price, 2),
                    "customer_segment": customer_segment,
                    "discount_rate": round(discount_rate, 3),
                    "historical_data_available": insights['data_available'],
                    "historical_orders": insights['total_orders']
                },
                "model_info": {
                    "aggregation_method": aggregation_method,
                    "subcategories_predicted": len(valid_predictions),
                    "mapped_from": mapped_category
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_predicted_demand": 0
            }


class GeminiForecaster:
    def __init__(self, api_key: str, model_path: str, preprocessor_path: str):
        """Initialize Gemini with forecasting capabilities"""
        
        # Initialize forecast service
        self.forecast_service = ForecastService(model_path, preprocessor_path)
        
        # Configure Gemini client
        client = genai.Client(api_key=api_key)
        self.model = client.models.generate_content(model="gemini-2.0-flash-exp")
        
        # Define function schemas for Gemini
        self.function_schemas = [
            {
                "name": "forecast_category_demand",
                "description": "Predicts future demand for a specific category using XGBoost time series model with intelligent database parameter learning and scenario support.",
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
                        "scenario": { 
                            "type": "string", 
                            "description": "Forecasting scenario",
                            "enum": ["conservative", "standard", "optimistic"],
                            "default": "standard" 
                        },
                        "aggregation_method": { 
                            "type": "string", 
                            "description": "How to aggregate historical data for parameter learning",
                            "enum": ["average", "median", "recent"],
                            "default": "average" 
                        }
                    },
                    "required": ["category_name", "future_year_month"]
                }
            }
        ]
        
        # Create tools for function calling
        self.tools = [types.Tool(function_declarations=[
            types.FunctionDeclaration(**schema) for schema in self.function_schemas
        ])]
        
        print("✅ GeminiForecaster initialized successfully")
        print(f"   Available functions: {len(self.function_schemas)}")
        print(f"   Categories supported: Office Supplies, Technology, Furniture, Sporting")

    def forecast_category_demand(self, category_name: str, future_year_month: str, 
                               scenario: str = "standard", aggregation_method: str = "average",
                               **kwargs) -> Dict[str, Any]:
        """Call the forecast service - this is what Gemini will invoke"""
        return self.forecast_service.forecast_category_demand(
            category_name, future_year_month, scenario, aggregation_method, **kwargs
        )

    def chat_with_forecasting(self, user_message: str) -> str:
        """
        Chat with Gemini while having access to forecasting functions
        """
        try:
            # System prompt for forecasting context
            system_prompt = """You are an expert AI assistant for sales forecasting and inventory management. 

You have access to a sophisticated XGBoost time series forecasting model that can predict demand for different product categories. The model was trained on historical sales data and uses features like:
- Category-specific patterns
- Time series features (seasonality, trends)
- Price and discount information  
- Customer segment data
- Historical purchasing patterns

Available categories: Office Supplies, Technology, Furniture, Sporting

You can forecast demand using different scenarios:
- Conservative: Assumes lower prices and higher discounts
- Standard: Uses historical averages
- Optimistic: Assumes higher prices and lower discounts

When users ask about forecasting, demand prediction, sales trends, or inventory planning, use the forecast_category_demand function to provide accurate predictions.

Always explain your forecasts in business terms and provide actionable insights."""

            # Prepare the conversation
            messages = [
                {"role": "user", "content": f"{system_prompt}\n\nUser: {user_message}"}
            ]
            
            # Make request with function calling capability
            response = self.model.generate_content(
                messages,
                config=types.GenerateContentConfig(
                    tools=self.tools,
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode="ANY"
                        )
                    )
                )
            )
            
            # Handle function calls
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        
                        if function_call.name == "forecast_category_demand":
                            # Execute the forecast
                            args = function_call.args
                            result = self.forecast_category_demand(**args)
                            
                            # Format the response
                            if result["success"]:
                                forecast_text = f"""
🔮 **DEMAND FORECAST RESULTS**

**Category:** {result['category']}
**Target Month:** {result['target_month']}
**Scenario:** {result['scenario'].title()}

**📊 PREDICTION:**
• **Total Predicted Demand:** {result['total_predicted_demand']} units
• **Average per Subcategory:** {result['average_per_subcategory']} units

**📋 SUBCATEGORY BREAKDOWN:**"""
                                for sub in result['subcategory_breakdown']:
                                    forecast_text += f"\n• {sub['subcategory']}: {sub['predicted_demand']} units"
                                
                                forecast_text += f"""

**⚙️ PARAMETERS USED:**
• Average Price: ${result['parameters_used']['avg_price']}
• Customer Segment: {result['parameters_used']['customer_segment']}
• Discount Rate: {result['parameters_used']['discount_rate']*100:.1f}%
• Historical Data: {'✅ Available' if result['parameters_used']['historical_data_available'] else '❌ Not Available'}
• Historical Orders: {result['parameters_used']['historical_orders']}

**📈 BUSINESS INSIGHTS:**
Based on this forecast, I recommend:
1. **Inventory Planning:** Stock approximately {result['total_predicted_demand']} units for {result['target_month']}
2. **Scenario Analysis:** This {result['scenario']} scenario prediction helps with risk assessment
3. **Category Focus:** {result['model_info']['subcategories_predicted']} subcategories were analyzed for comprehensive coverage

The model used {result['model_info']['aggregation_method']} aggregation method and mapped your category to {result['model_info']['mapped_from']} for prediction."""

                                return forecast_text
                            else:
                                return f"❌ Forecast Error: {result['error']}"
                    
                    elif hasattr(part, 'text') and part.text:
                        return part.text
            
            return "I can help you with sales forecasting and demand prediction. Please ask me about predicting demand for specific categories or time periods!"
            
        except Exception as e:
            return f"Error processing request: {str(e)}"


# Initialize the service
def create_forecaster(api_key: str) -> GeminiForecaster:
    """Create a GeminiForecaster instance with proper model paths"""
    
    # Update these paths to match your model location
    model_path = "Supervised models/ShernFai/model/salesforecast(categories).pkl"
    preprocessor_path = "Supervised models/ShernFai/model/salesforecast_preprocessor.pkl"
    
    return GeminiForecaster(api_key, model_path, preprocessor_path)


# Example usage
if __name__ == "__main__":
    # Example of how to use the forecaster
    API_KEY = "your-api-key-here"  # Replace with your actual API key
    
    try:
        forecaster = create_forecaster(API_KEY)
        
        # Test direct forecasting
        print("🧪 TESTING DIRECT FORECAST:")
        result = forecaster.forecast_category_demand(
            category_name="Technology",
            future_year_month="2025-03",
            scenario="optimistic"
        )
        print(f"Result: {result}")
        
        # Test chat interface
        print("\n💬 TESTING CHAT INTERFACE:")
        response = forecaster.chat_with_forecasting(
            "What will be the demand for Technology products in March 2025?"
        )
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to:")
        print("1. Set your actual Google AI API key")
        print("2. Verify model file paths are correct")
        print("3. Install required dependencies: pip install google-genai")
    # def identify_declining_categories(self, analysis_months: int = 6, 
    #                                 decline_threshold: float = -10.0, 
    #                                 forecast_months: int = 3) -> Dict[str, Any]:
    #     """Identify categories with declining trends"""
    #     try:
    #         db = SessionLocal()
            
    #         # Get historical data from database
    #         current_date = datetime.now()
    #         analysis_start = pd.Timestamp(current_date) - pd.DateOffset(months=analysis_months)
            
    #         # Query order data for trend analysis
    #         orders = db.query(Order).join(Inventory).filter(
    #             Order.DateOrdered >= analysis_start.strftime('%Y-%m-%d')
    #         ).all()
            
    #         if not orders:
    #             return {
    #                 "success": False,
    #                 "error": "No historical data available for analysis",
    #                 "declining_categories": []
    #             }
            
    #         # Analyze trends (simplified version)
    #         category_trends = {}
    #         declining_categories = []
            
    #         # Group by category and calculate trends
    #         for order in orders:
    #             category = order.inventory_item.ItemCategory
    #             if category not in category_trends:
    #                 category_trends[category] = []
    #             category_trends[category].append(order.OrderQuantity)
            
    #         # Calculate decline percentage
    #         for category, quantities in category_trends.items():
    #             if len(quantities) >= 2:
    #                 recent_avg = np.mean(quantities[-2:])
    #                 early_avg = np.mean(quantities[:2])
                    
    #                 if early_avg > 0:
    #                     decline_percent = ((recent_avg - early_avg) / early_avg) * 100
                        
    #                     if decline_percent <= decline_threshold:
    #                         declining_categories.append({
    #                             "category": category,
    #                             "decline_percentage": round(decline_percent, 2),
    #                             "recent_average_demand": round(recent_avg, 2),
    #                             "early_average_demand": round(early_avg, 2)
    #                         })
            
    #         db.close()
            
    #         return {
    #             "success": True,
    #             "analysis_period_months": analysis_months,
    #             "decline_threshold": decline_threshold,
    #             "declining_categories": declining_categories,
    #             "total_categories_analyzed": len(category_trends)
    #         }
            
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "declining_categories": []
    #         }

    # def get_most_used_category(self, start_date: str, end_date: str, 
    #                          metric: str = "total_quantity") -> Dict[str, Any]:
    #     """Get the most used category in a time period"""
    #     try:
    #         db = SessionLocal()
            
    #         # Query orders in the date range
    #         orders = db.query(Order).join(Inventory).filter(
    #             Order.DateOrdered >= start_date + '-01',
    #             Order.DateOrdered <= end_date + '-31'
    #         ).all()
            
    #         if not orders:
    #             return {
    #                 "success": False,
    #                 "error": "No data available for the specified period",
    #                 "top_category": None
    #             }
            
    #         # Calculate metrics by category
    #         category_metrics = {}
            
    #         for order in orders:
    #             category = order.inventory_item.ItemCategory
    #             if category not in category_metrics:
    #                 category_metrics[category] = {
    #                     "total_quantity": 0,
    #                     "order_count": 0,
    #                     "total_sales": 0
    #                 }
                
    #             category_metrics[category]["total_quantity"] += order.OrderQuantity
    #             category_metrics[category]["order_count"] += 1
    #             category_metrics[category]["total_sales"] += order.Sales
            
    #         # Calculate the requested metric
    #         for category in category_metrics:
    #             data = category_metrics[category]
    #             if metric == "average_monthly":
    #                 # Calculate months between dates
    #                 start_dt = pd.to_datetime(start_date)
    #                 end_dt = pd.to_datetime(end_date)
    #                 months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
    #                 data["average_monthly"] = data["total_quantity"] / months
    #             elif metric == "growth_rate":
    #                 # Simplified growth rate calculation
    #                 data["growth_rate"] = data["total_quantity"] / data["order_count"]
            
    #         # Find top category
    #         if metric == "total_quantity":
    #             top_category = max(category_metrics.items(), 
    #                              key=lambda x: x[1]["total_quantity"])
    #         elif metric == "average_monthly":
    #             top_category = max(category_metrics.items(), 
    #                              key=lambda x: x[1]["average_monthly"])
    #         else:  # growth_rate
    #             top_category = max(category_metrics.items(), 
    #                              key=lambda x: x[1]["growth_rate"])
            
    #         db.close()
            
    #         return {
    #             "success": True,
    #             "period": f"{start_date} to {end_date}",
    #             "metric_used": metric,
    #             "top_category": {
    #                 "name": top_category[0],
    #                 "metrics": top_category[1]
    #             },
    #             "all_categories": category_metrics
    #         }
            
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "top_category": None
    #         }

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
            
            # # Declining Categories
            # {
            #     "name": "identify_declining_categories",
            #     "description": "Identifies categories with declining demand trends based on historical data.",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "analysis_months": { 
            #                 "type": "integer", 
            #                 "description": "Number of historical months to analyze for trend",
            #                 "default": 6 
            #             },
            #             "decline_threshold": { 
            #                 "type": "number", 
            #                 "description": "Minimum decline percentage to consider as declining",
            #                 "default": -10.0 
            #             },
            #             "forecast_months": { 
            #                 "type": "integer", 
            #                 "description": "Number of future months to predict for trend confirmation",
            #                 "default": 3 
            #             }
            #         }
            #     }
            # },
            
            # # Most Used Categories
            # {
            #     "name": "get_most_used_category",
            #     "description": "Returns the most used category within a given time period with statistical backing.",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "start_date": { "type": "string", "description": "Start date in YYYY-MM format" },
            #             "end_date": { "type": "string", "description": "End date in YYYY-MM format" },
            #             "metric": { 
            #                 "type": "string", 
            #                 "enum": ["total_quantity", "average_monthly", "growth_rate"],
            #                 "default": "total_quantity" 
            #             }
            #         },
            #         "required": ["start_date", "end_date"]
            #     }
            # }
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
def generate():
    client = genai.Client(api_key="AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw")
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Write me a short poem about coffee."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
