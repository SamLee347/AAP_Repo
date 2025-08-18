# imports
import base64
import os
import sys
from pathlib import Path

# Add the BackEnd directory to Python path so we can import Database modules
backend_dir = Path(__file__).parent.parent.parent
sys.path.append(str(backend_dir))

from google import genai
from google.genai import types

import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any

# Now import the database modules (after sys.path is updated)
from Database.db import SessionLocal
from Database_Table.order import Order
from Database_Table.inventory import Inventory

class ForecastService:
    def __init__(self, model_path: str, preprocessor_path: str, api_key: str=None):
        """Initialize the forecasting service with trained model"""
        try:
            self.model = joblib.load(model_path)
            
            with open(preprocessor_path, 'rb') as f:
                self.preprocessor_data = pickle.load(f)
            
            self.le_category = self.preprocessor_data['label_encoder_category']
            self.feature_columns = self.preprocessor_data['feature_columns']
            self.reference_date = self.preprocessor_data['reference_date']
            
            # Category mapping from your notebook - this maps general categories to specific subcategories
            self.category_mapping = {
                "Clothing": ["Cleats", "Men's Footwear", "Women's Apparel"],
                "Technology": ["Electronics", "Computers", "Cameras", "Video Games"],
                "Sports and Fitness": ["Cardio Equipment", "Shop By Sport", "Camping & Hiking", 
                                      "Fishing", "Water Sports", "Indoor/Outdoor Games"],
                "Other": ["Garden", "Pet Supplies"]
            }
            print(f"   Model loaded: {len(self.le_category.classes_)} categories available")
            print(f"   Reference date: {self.reference_date}")
            
        except Exception as e:
            print(f"❌ Error initializing ForecastService: {e}")
            raise

    # Adding semantic category mapping to be more intuitive instead of having fixed mapping
    # --------------------------------------------------------------------------------------
    def semantic_category_mapping(self, category_name: str, gemini_client=None) -> str:
        """
        Lightweight category mapping - tries Gemini briefly, falls back to keywords
        """
        # First try simple keyword matching (fastest)
        keyword_result = self._keyword_mapping(category_name)
        
        # If keyword mapping gives "Other", try Gemini for a smarter guess
        if keyword_result == "Other" and gemini_client:
            return self._gemini_semantic_mapping(category_name, gemini_client)
        
        return keyword_result

    def _gemini_semantic_mapping(self, category_name: str, gemini_client) -> str:
        """
        Simple, lightweight category mapping using passed Gemini client
        """
        try:
            # Very short, focused prompt that won't interfere with chat
            quick_prompt = f"""Map "{category_name}" to: Technology, Sports and Fitness, Clothing, or Other. Answer with just the category name."""
            
            # Quick, simple API call using passed client
            response = gemini_client.models.generate_content(
                model="models/gemini-1.5-flash-latest",
                contents=quick_prompt
            )
            
            mapped = response.text.strip()
            
            # Quick validation
            if mapped in ["Technology", "Sports and Fitness", "Clothing", "Other"]:
                return mapped
            else:
                return "Other"
                
        except:
            return "Other"

    def _keyword_mapping(self, category_name: str) -> str:
        """
        Simple keyword-based fallback (very lightweight)
        """
        category_lower = category_name.lower()
        
        # Simple keyword checks
        if any(word in category_lower for word in ['tech', 'computer', 'electronic', 'gaming']):
            return "Technology"
        elif any(word in category_lower for word in ['sport', 'fitness', 'outdoor', 'athletic']):
            return "Sports and Fitness"
        elif any(word in category_lower for word in ['cloth', 'apparel', 'fashion', 'shoe']):
            return "Clothing"
        else:
            return "Other"
    # --------------------------------------------------------------------------------------

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
                               scenario: str = "standard", aggregation_method: str = "average", gemini_client = None,
                               **kwargs) -> Dict[str, Any]:
        """
        Single unified forecasting function with database intelligence and scenario support
        
        Args:
            category_name: Product category name (Office Supplies, Technology, Furniture, Sporting)
            future_year_month: Target month in YYYY-MM format
            scenario: "conservative", "standard", or "optimistic"
            aggregation_method: "average", "median", or "recent"
            **kwargs: Override parameters (avg_price, customer_segment, discount_rate)
        """
        try:
            # Map user category to model category
            mapped_category = self.semantic_category_mapping(category_name, gemini_client)
            
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
                    # Create test data using your notebook's exact approach
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
                    
                    # Create DataFrame and preprocess exactly like your notebook
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
        self.client = genai.Client(api_key=api_key)
        
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
            category_name, future_year_month, scenario,
            aggregation_method, gemini_client=self.client, **kwargs
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

            # Prepare the conversation using simple string format
            full_message = f"{system_prompt}\n\nUser: {user_message}"
            
            # Make request with function calling capability
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_message,
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
    
    # Get absolute paths to the model files
    backend_dir = Path(__file__).parent.parent.parent
    model_path = backend_dir / "Supervised models" / "ShernFai" / "model" / "salesforecast(categories).pkl"
    preprocessor_path = backend_dir / "Supervised models" / "ShernFai" / "model" / "salesforecast_preprocessor.pkl"
    
    return GeminiForecaster(api_key, str(model_path), str(preprocessor_path))


def interactive_chat(forecaster: GeminiForecaster):
    """
    Interactive console chat with the GenAI forecasting system
    """
    print("\n" + "="*60)
    print("🤖 GenAI Forecasting Assistant")
    print("="*60)
    print("Ask me about sales forecasting and demand predictions!")
    print("Available categories: Office Supplies, Technology, Furniture, Sporting")
    print("Type 'quit', 'exit', or 'bye' to end the conversation.")
    print("="*60)
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Thanks for using GenAI Forecasting! Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or type 'quit' to exit.")
                continue
            
            # Get AI response
            print("\n🤖 AI: Thinking...")
            response = forecaster.chat_with_forecasting(user_input)
            print(f"\n🤖 AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")


# Example usage and testing
if __name__ == "__main__":
    # Load API key from environment variable
    API_KEY = "AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw"
    
    if not API_KEY:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables")
        print("Make sure you have a .env file with:")
        print("GOOGLE_API_KEY=your_actual_api_key_here")
        print("\nOr set it manually:")
        print("API_KEY = 'your_actual_api_key_here'")
        exit(1)
    
    try:
        # Test direct forecasting without GenAI first
        print("🧪 TESTING DIRECT FORECAST (without GenAI):")
        
        # Get absolute paths to the model files
        backend_dir = Path(__file__).parent.parent.parent
        model_path = backend_dir / "Supervised models" / "ShernFai" / "model" / "salesforecast(categories).pkl"
        preprocessor_path = backend_dir / "Supervised models" / "ShernFai" / "model" / "salesforecast_preprocessor.pkl"
        
        forecast_service = ForecastService(
            str(model_path),
            str(preprocessor_path)
        )
        
        result = forecast_service.forecast_category_demand(
            category_name="Technology",
            future_year_month="2025-03",
            scenario="optimistic"
        )
        print(f"Direct forecast result: {result}")
        
        # Initialize GenAI forecaster
        print("\n💬 INITIALIZING GENAI CHAT INTERFACE:")
        forecaster = create_forecaster(API_KEY)
        
        # Ask user if they want to test with a single question or interactive chat
        print("\nChoose your testing mode:")
        print("1. Single test question")
        print("2. Interactive chat (recommended)")
        
        choice = input("\nEnter 1 or 2 (default: 2): ").strip()
        
        if choice == "1":
            # Single test question
            response = forecaster.chat_with_forecasting(
                "What will be the demand for Technology products in March 2025?"
            )
            print(f"\n🤖 AI Response:\n{response}")
        else:
            # Interactive chat mode
            interactive_chat(forecaster)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your model files exist at:")
        backend_dir = Path(__file__).parent.parent.parent
        model_path = backend_dir / "Supervised models" / "ShernFai" / "model" / "salesforecast(categories).pkl"
        preprocessor_path = backend_dir / "Supervised models" / "ShernFai" / "model" / "salesforecast_preprocessor.pkl"
        print(f"   - {model_path}")
        print(f"   - {preprocessor_path}")
        print("2. Install required dependencies: pip install google-genai")
        print("3. Ensure your database connection is working")
        print("4. Make sure you have mysql-connector-python installed: pip install mysql-connector-python")
