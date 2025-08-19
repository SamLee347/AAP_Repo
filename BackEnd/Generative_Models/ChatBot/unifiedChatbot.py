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
import google.generativeai as genai_legacy  # For embeddings

import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

# Now import the database modules (after sys.path is updated)
from Database.db import SessionLocal
from Database_Table.order import Order
from Database_Table.inventory import Inventory

class DatabaseQueryService:
    """Enhanced database querying with RAG capabilities"""
    
    def __init__(self, api_key: str):
        """Initialize the database query service"""
        # Configure legacy genai for embeddings
        genai_legacy.configure(api_key=api_key)
        self.embedding_model = "models/text-embedding-004"
        self.generation_model = genai_legacy.GenerativeModel("gemini-2.5-flash")
        
    def cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_db_content(self, session=None):
        """Get all database records - NOW accepts optional session"""
        if session:
            # Use provided session
            inventory_records = session.query(Inventory).all()
            order_records = session.query(Order).all()
            return inventory_records, order_records
        else:
            # Fallback to creating own session
            db = SessionLocal()
            try:
                inventory_records = db.query(Inventory).all()
                order_records = db.query(Order).all()
                return inventory_records, order_records
            finally:
                db.close()


    # def get_db_content(self):
    #     """Get all database records"""
    #     session = SessionLocal()
    #     try:
    #         inventory_records = session.query(Inventory).all()
    #         order_records = session.query(Order).all()
    #         return inventory_records, order_records
    #     finally:
    #         session.close()

    def embed_content(self, records):
        """Convert database records to embeddings"""
        embeddings_list = []
        for r in records:
            if isinstance(r, Inventory):
                text = (
                    f"ItemId: {r.ItemId}, Date: {r.Date}, Quantity: {r.ItemQuantity}, "
                    f"Category: {r.ItemCategory}, UnitsSold: {r.UnitsSold}, "
                    f"Weight: {r.Weight}, Size: {r.Size}, Priority: {r.Priority}, "
                    f"Dispose: {r.Dispose}"
                )
                record_id = f"INV_{r.ItemId}"
            elif isinstance(r, Order):
                text = (
                    f"OrderId: {r.OrderId}, ItemId: {r.ItemId}, OrderQuantity: {r.OrderQuantity}, "
                    f"Sales: {r.Sales}, Price: {r.Price}, Discount: {r.Discount}, "
                    f"Profit: {r.Profit}, DateOrdered: {r.DateOrdered}, "
                    f"DateReceived: {r.DateReceived}, CustomerSegment: {r.CustomerSegment}"
                )
                record_id = f"ORD_{r.OrderId}"
            else:
                continue
            
            try:
                embedding = genai_legacy.embed_content(
                    model=self.embedding_model,
                    content=text
                )["embedding"]
                embeddings_list.append({
                    "id": record_id, 
                    "text": text, 
                    "embedding": embedding
                })
            except Exception as e:
                print(f"Warning: Could not embed record {record_id}: {e}")
                continue
        
        return embeddings_list
    
    def query_database(self, question: str, top_k: int = 5, session=None) -> Dict[str, Any]:
        """Query database - NOW accepts optional session"""
        try:
            # Embed the question
            query_emb = np.array(genai_legacy.embed_content(
                model=self.embedding_model, 
                content=question
            )["embedding"])

            # Get and embed database content using shared session
            inventory, order = self.get_db_content(session=session)
            embeddings_list = self.embed_content(inventory + order)
            
            if not embeddings_list:
                return {
                    "success": False,
                    "error": "No database content could be processed",
                    "answer": "I couldn't access the database content."
                }

            # Compute similarity scores
            similarities = []
            for item in embeddings_list:
                emb = np.array(item["embedding"])
                sim_score = self.cosine_similarity(query_emb, emb)
                similarities.append((sim_score, item["text"], item["id"]))

            # Get top_k most relevant records
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_records = similarities[:top_k]
            top_texts = [text for _, text, _ in top_records]

            # Build context for generation
            context = "\n\n".join(top_texts)
            prompt = f"""
You are a data analyst assistant that answers questions based on inventory and order data.
Answer the question using ONLY the provided database context.
If the context doesn't contain enough information, say "I need more specific data to answer that question."

Provide clear, business-focused answers with specific numbers when available.

Database Context:
{context}

Question: {question}

Answer:"""

            # Generate response
            response = self.generation_model.generate_content(prompt)
            
            return {
                "success": True,
                "answer": response.text,
                "sources_used": len(top_records),
                "relevance_scores": [score for score, _, _ in top_records],
                "record_ids": [record_id for _, _, record_id in top_records]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "answer": f"Error querying database: {e}"
            }

class ForecastService:
    """Enhanced forecasting service with semantic mapping"""
    
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
            
            print(f"✅ ForecastService initialized successfully")
            print(f"   Model loaded: {len(self.le_category.classes_)} categories available")
            print(f"   Reference date: {self.reference_date}")
            
        except Exception as e:
            print(f"❌ Error initializing ForecastService: {e}")
            raise

    def semantic_category_mapping(self, category_name: str, gemini_client=None) -> str:
        """
        Simple category mapping using just Gemini
        """
        if not gemini_client:
            return "Other"
        
        try:
            prompt = f"Map '{category_name}' to one of: Technology, Sports and Fitness, Clothing, Other. Reply with only the category name."
            
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            mapped = response.text.strip()
            valid_categories = ["Technology", "Sports and Fitness", "Clothing", "Other"]
            
            return mapped if mapped in valid_categories else "Other"
            
        except:
            return "Other"

    def get_historical_insights(self, category_name: str, months_back: int = 6, 
                               session=None) -> Dict[str, Any]:
        """Get historical data insights - NOW accepts optional session"""
        try:
            # Use provided session or create new one
            db = session if session else SessionLocal()
            should_close = session is None  # Only close if we created it
            
            current_date = datetime.now()
            start_date = pd.Timestamp(current_date) - pd.DateOffset(months=months_back)
            
            orders = db.query(Order).join(Inventory).filter(
                Order.DateOrdered >= start_date.strftime('%Y-%m-%d'),
                Inventory.ItemCategory == category_name
            ).all()
            
            if not orders:
                return {
                    "avg_price": 25.50,
                    "avg_discount_rate": 0.08,
                    "dominant_segment": "Consumer",
                    "total_orders": 0,
                    "data_available": False
                }
            
            # Process data...
            prices = [order.Price for order in orders if order.Price]
            discount_rates = [order.Discount / order.Price for order in orders if order.Discount and order.Price]
            segments = [order.CustomerSegment for order in orders if order.CustomerSegment]
            
            insights = {
                "avg_price": np.mean(prices) if prices else 25.50,
                "avg_discount_rate": np.mean(discount_rates) if discount_rates else 0.08,
                "dominant_segment": max(set(segments), key=segments.count) if segments else "Consumer",
                "total_orders": len(orders),
                "data_available": True
            }
            
            return insights
            
        except Exception as e:
            print(f"Warning: Could not get historical insights: {e}")
            return {
                "avg_price": 25.50,
                "avg_discount_rate": 0.08,
                "dominant_segment": "Consumer",
                "total_orders": 0,
                "data_available": False
            }
        finally:
            if should_close and 'db' in locals():
                db.close()

    def forecast_category_demand(self, category_name: str, future_year_month: str, 
                            scenario: str = "standard", aggregation_method: str = "average", 
                            gemini_client=None, session=None, **kwargs) -> Dict[str, Any]:
        """Forecast function - NOW COMPLETE"""
        try:
            # Use semantic mapping
            mapped_category = self.semantic_category_mapping(category_name, gemini_client)
            print(f"🔄 Semantic mapping: '{category_name}' → '{mapped_category}'")
            
            # Get historical insights using the shared session
            insights = self.get_historical_insights(mapped_category, session=session)
            
            # Use historical insights or kwargs for parameters
            avg_price = kwargs.get('avg_price', insights['avg_price'])
            customer_segment = kwargs.get('customer_segment', insights['dominant_segment'])
            discount_rate = kwargs.get('discount_rate', insights['avg_discount_rate'])
            
            # Apply scenario adjustments
            if scenario == "conservative":
                avg_price *= 0.95
                discount_rate *= 1.2
            elif scenario == "optimistic":
                avg_price *= 1.05
                discount_rate *= 0.8
            
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
                    "error": f"No valid subcategories found for {category_name} (mapped to {mapped_category})",
                    "total_predicted_demand": 0,
                    "semantic_mapping": {
                        "original_category": category_name,
                        "mapped_category": mapped_category,
                        "mapping_successful": False
                    }
                }
            
            # Calculate final aggregation
            if aggregation_method == "median":
                final_prediction = np.median(valid_predictions) * len(valid_predictions)
            elif aggregation_method == "recent":
                final_prediction = total_prediction * 1.1 if scenario == "optimistic" else total_prediction * 0.9
            else:  # average (default)
                final_prediction = total_prediction
            
            return {
                "success": True,
                "category": category_name,
                "mapped_category": mapped_category,
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
                },
                "semantic_mapping": {
                    "original_category": category_name,
                    "mapped_category": mapped_category,
                    "mapping_successful": True
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_predicted_demand": 0,
                "semantic_mapping": {
                    "original_category": category_name,
                    "mapped_category": "Error",
                    "mapping_successful": False
                }
            }

    # Complete the identify_top_selling_categories method:
    def identify_top_selling_categories(self, analysis_months: int = 6, 
                                    top_n: int = 5, session=None) -> Dict[str, Any]:
        """Top selling categories - NOW COMPLETE"""
        try:
            # Use provided session or create new one
            db = session if session else SessionLocal()
            should_close = session is None
            
            current_date = datetime.now()
            start_date = pd.Timestamp(current_date) - pd.DateOffset(months=analysis_months)
            
            print(f"Analyzing top sellers from {start_date.strftime('%Y-%m')} to now")
            
            # Get all orders in the analysis period
            orders = db.query(Order).join(Inventory).filter(
                Order.DateOrdered >= start_date.strftime('%Y-%m-%d')
            ).all()
            
            if not orders:
                return {
                    "success": False,
                    "error": "No sales data found in the analysis period",
                    "top_categories": []
                }
            
            # Group by category and calculate metrics
            category_stats = {}
            
            for order in orders:
                category = order.inventory_item.ItemCategory
                if not category:
                    category = "Unknown"
                
                if category not in category_stats:
                    category_stats[category] = {
                        "total_sales": 0,
                        "total_revenue": 0,
                        "total_profit": 0,
                        "total_quantity": 0,
                        "order_count": 0,
                        "avg_order_value": 0
                    }
                
                # Aggregate metrics
                category_stats[category]["total_sales"] += order.Sales
                category_stats[category]["total_revenue"] += order.Price * order.OrderQuantity
                category_stats[category]["total_profit"] += order.Profit
                category_stats[category]["total_quantity"] += order.OrderQuantity
                category_stats[category]["order_count"] += 1
            
            # Calculate averages and create final results
            top_categories = []
            for category, stats in category_stats.items():
                stats["avg_order_value"] = stats["total_revenue"] / stats["order_count"] if stats["order_count"] > 0 else 0
                stats["profit_margin"] = (stats["total_profit"] / stats["total_revenue"]) * 100 if stats["total_revenue"] > 0 else 0
                
                top_categories.append({
                    "category": category,
                    "total_sales": stats["total_sales"],
                    "total_revenue": round(stats["total_revenue"], 2),
                    "total_profit": round(stats["total_profit"], 2),
                    "total_quantity": stats["total_quantity"],
                    "order_count": stats["order_count"],
                    "avg_order_value": round(stats["avg_order_value"], 2),
                    "profit_margin": round(stats["profit_margin"], 2)
                })
            
            # Sort by total revenue
            top_categories.sort(key=lambda x: x["total_revenue"], reverse=True)
            top_categories = top_categories[:top_n]
            
            return {
                "success": True,
                "analysis_period": f"{analysis_months} months",
                "top_categories": top_categories,
                "total_categories_analyzed": len(category_stats),
                "top_n": top_n,
                "summary": {
                    "best_performer": top_categories[0] if top_categories else None,
                    "total_revenue_analyzed": sum(cat["total_revenue"] for cat in top_categories),
                    "total_orders_analyzed": sum(cat["order_count"] for cat in top_categories)
                }
            }
            
        except Exception as e:
            print(f"❌ Error in top selling analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "top_categories": []
            }
        finally:
            if should_close and 'db' in locals():
                db.close()

    # Original 
    # def get_historical_insights(self, category_name: str, months_back: int = 6, session=None) -> Dict[str, Any]:
    #     """Get historical data insights for intelligent parameter defaults"""
    #     try:
    #         db = session if session else SessionLocal()
    #         should_close = session is None  # Only close if we created it
            
    #         if session:
    #             db = session

    #         current_date = datetime.now()
    #         start_date = pd.Timestamp(current_date) - pd.DateOffset(months=months_back)
            
    #         orders = db.query(Order).join(Inventory).filter(
    #             Order.DateOrdered >= start_date.strftime('%Y-%m-%d'),
    #             Inventory.ItemCategory == category_name
    #         ).all()
            
    #         if not orders:
    #             return {
    #                 "avg_price": 25.50,
    #                 "avg_discount_rate": 0.08,
    #                 "dominant_segment": "Consumer",
    #                 "total_orders": 0,
    #                 "data_available": False
    #             }
            
    #         # Fixed: Use proper Order model fields
    #         prices = [order.Price for order in orders if order.Price]
    #         discount_rates = [order.Discount / order.Price for order in orders if order.Discount and order.Price]
    #         segments = [order.CustomerSegment for order in orders if order.CustomerSegment]
            
    #         insights = {
    #             "avg_price": np.mean(prices) if prices else 25.50,
    #             "avg_discount_rate": np.mean(discount_rates) if discount_rates else 0.08,
    #             "dominant_segment": max(set(segments), key=segments.count) if segments else "Consumer",
    #             "total_orders": len(orders),
    #             "data_available": True
    #         }
            
    #         db.close()
    #         return insights
            
    #     except Exception as e:
    #         if 'db' in locals():
    #             db.close()
    #         return {
    #             "avg_price": 25.50,
    #             "avg_discount_rate": 0.08,
    #             "dominant_segment": "Consumer",
    #             "total_orders": 0,
    #             "data_available": False
    #         }

    # def forecast_category_demand(self, category_name: str, future_year_month: str, 
    #                            scenario: str = "standard", aggregation_method: str = "average", 
    #                            gemini_client=None, **kwargs) -> Dict[str, Any]:
    #     """Unified forecasting function with semantic mapping integration"""
    #     try:
    #         # **KEY UPDATE**: Use semantic mapping with the unified chatbot's client
    #         mapped_category = self.semantic_category_mapping(category_name, gemini_client)
    #         print(f"🔄 Semantic mapping: '{category_name}' → '{mapped_category}'")
            
    #         # Get historical insights using the mapped category
    #         insights = self.get_historical_insights(mapped_category)
            
    #         # Use historical insights or kwargs for parameters
    #         avg_price = kwargs.get('avg_price', insights['avg_price'])
    #         customer_segment = kwargs.get('customer_segment', insights['dominant_segment'])
    #         discount_rate = kwargs.get('discount_rate', insights['avg_discount_rate'])
            
    #         # Apply scenario adjustments
    #         if scenario == "conservative":
    #             avg_price *= 0.95
    #             discount_rate *= 1.2
    #         elif scenario == "optimistic":
    #             avg_price *= 1.05
    #             discount_rate *= 0.8
            
    #         # Parse future date
    #         future_date = pd.to_datetime(future_year_month)
            
    #         # Calculate time features
    #         months_since_start = ((future_date - self.reference_date).days / 30.44)
            
    #         # Get specific categories for the mapped category
    #         specific_categories = self.category_mapping.get(mapped_category, [mapped_category])
            
    #         total_prediction = 0
    #         valid_predictions = []
    #         category_predictions = []
            
    #         for specific_cat in specific_categories:
    #             if specific_cat in self.le_category.classes_:
    #                 # Create test data
    #                 test_data = {
    #                     'Category Name': specific_cat,
    #                     'Average Product Price': avg_price,
    #                     'Customer Segment': customer_segment,
    #                     'Order Item Discount Rate': discount_rate,
    #                     'Year': future_date.year,
    #                     'Month': future_date.month,
    #                     'Quarter': future_date.quarter,
    #                     'Months_Since_Start': int(months_since_start),
    #                     'Month_Sin': np.sin(2 * np.pi * future_date.month / 12),
    #                     'Month_Cos': np.cos(2 * np.pi * future_date.month / 12),
    #                     'Year_Trend': future_date.year - self.reference_date.year
    #                 }
                    
    #                 # Create DataFrame and preprocess
    #                 test_df = pd.DataFrame([test_data])
    #                 test_df['Category Name'] = self.le_category.transform(test_df['Category Name'])
    #                 test_df = pd.get_dummies(test_df, columns=['Customer Segment'], drop_first=True)
    #                 test_df = test_df.reindex(columns=self.feature_columns, fill_value=0)
                    
    #                 # Make prediction
    #                 prediction = self.model.predict(test_df)[0]
    #                 total_prediction += prediction
    #                 valid_predictions.append(prediction)
    #                 category_predictions.append({
    #                     'subcategory': specific_cat,
    #                     'predicted_demand': round(prediction, 2)
    #                 })
            
    #         if not valid_predictions:
    #             return {
    #                 "success": False,
    #                 "error": f"No valid subcategories found for {category_name} (mapped to {mapped_category})",
    #                 "total_predicted_demand": 0,
    #                 "semantic_mapping": {
    #                     "original_category": category_name,
    #                     "mapped_category": mapped_category
    #                 }
    #             }
            
    #         # Calculate final aggregation
    #         if aggregation_method == "median":
    #             final_prediction = np.median(valid_predictions) * len(valid_predictions)
    #         elif aggregation_method == "recent":
    #             final_prediction = total_prediction * 1.1 if scenario == "optimistic" else total_prediction * 0.9
    #         else:  # average (default)
    #             final_prediction = total_prediction
            
    #         return {
    #             "success": True,
    #             "category": category_name,
    #             "mapped_category": mapped_category,  # **ADDED**: Show the mapping result
    #             "target_month": future_year_month,
    #             "scenario": scenario,
    #             "total_predicted_demand": round(final_prediction, 2),
    #             "average_per_subcategory": round(final_prediction / len(valid_predictions), 2),
    #             "subcategory_breakdown": category_predictions,
    #             "parameters_used": {
    #                 "avg_price": round(avg_price, 2),
    #                 "customer_segment": customer_segment,
    #                 "discount_rate": round(discount_rate, 3),
    #                 "historical_data_available": insights['data_available'],
    #                 "historical_orders": insights['total_orders']
    #             },
    #             "model_info": {
    #                 "aggregation_method": aggregation_method,
    #                 "subcategories_predicted": len(valid_predictions),
    #                 "mapped_from": mapped_category
    #             },
    #             "semantic_mapping": {  # **ADDED**: Semantic mapping details
    #                 "original_category": category_name,
    #                 "mapped_category": mapped_category,
    #                 "mapping_successful": True
    #             }
    #         }
            
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "total_predicted_demand": 0,
    #             "semantic_mapping": {
    #                 "original_category": category_name,
    #                 "mapped_category": "Error",
    #                 "mapping_successful": False
    #             }
    #         }

    # def identify_top_selling_categories(self, analysis_months: int = 6, top_n: int = 5) -> Dict[str, Any]:
    #     try:
    #         db = SessionLocal()
            
    #         # Calculate date range
    #         current_date = datetime.now()
    #         start_date = pd.Timestamp(current_date) - pd.DateOffset(months=analysis_months)
            
    #         print(f"Analyzing top sellers from {start_date.strftime('%Y-%m')} to now")
            
    #         # Get all orders in the analysis period
    #         orders = db.query(Order).join(Inventory).filter(
    #             Order.DateOrdered >= start_date.strftime('%Y-%m-%d')
    #         ).all()
            
    #         if not orders:
    #             db.close()
    #             return {
    #                 "success": False,
    #                 "error": "No sales data found in the analysis period",
    #                 "top_categories": []
    #             }
            
    #         # Group by category and calculate metrics
    #         category_stats = {}
            
    #         for order in orders:
    #             category = order.inventory_item.ItemCategory
    #             if not category:
    #                 category = "Unknown"
                
    #             if category not in category_stats:
    #                 category_stats[category] = {
    #                     "total_sales": 0,
    #                     "total_revenue": 0,
    #                     "total_profit": 0,
    #                     "total_quantity": 0,
    #                     "order_count": 0,
    #                     "avg_order_value": 0
    #                 }
                
    #             # Aggregate metrics
    #             category_stats[category]["total_sales"] += order.Sales
    #             category_stats[category]["total_revenue"] += order.Price * order.OrderQuantity
    #             category_stats[category]["total_profit"] += order.Profit
    #             category_stats[category]["total_quantity"] += order.OrderQuantity
    #             category_stats[category]["order_count"] += 1
            
    #         # Calculate averages and create final results
    #         top_categories = []
    #         for category, stats in category_stats.items():
    #             stats["avg_order_value"] = stats["total_revenue"] / stats["order_count"] if stats["order_count"] > 0 else 0
    #             stats["profit_margin"] = (stats["total_profit"] / stats["total_revenue"]) * 100 if stats["total_revenue"] > 0 else 0
                
    #             top_categories.append({
    #                 "category": category,
    #                 "total_sales": stats["total_sales"],
    #                 "total_revenue": round(stats["total_revenue"], 2),
    #                 "total_profit": round(stats["total_profit"], 2),
    #                 "total_quantity": stats["total_quantity"],
    #                 "order_count": stats["order_count"],
    #                 "avg_order_value": round(stats["avg_order_value"], 2),
    #                 "profit_margin": round(stats["profit_margin"], 2)
    #             })
            
    #         # Sort by total revenue (you can change this to total_sales or total_profit)
    #         top_categories.sort(key=lambda x: x["total_revenue"], reverse=True)
            
    #         # Get top N categories
    #         top_categories = top_categories[:top_n]
            
    #         db.close()
            
    #         return {
    #             "success": True,
    #             "analysis_period": f"{analysis_months} months",
    #             "top_categories": top_categories,
    #             "total_categories_analyzed": len(category_stats),
    #             "top_n": top_n,
    #             "summary": {
    #                 "best_performer": top_categories[0] if top_categories else None,
    #                 "total_revenue_analyzed": sum(cat["total_revenue"] for cat in top_categories),
    #                 "total_orders_analyzed": sum(cat["order_count"] for cat in top_categories)
    #             }
    #         }
        
    #     except Exception as e:
    #         if 'db' in locals():
    #             db.close()
    #         print(f"❌ Error in top selling analysis: {e}")
    #         return {
    #             "success": False,
    #             "error": str(e),
    #             "top_categories": []
    #         }
            
class UnifiedGeminiChatbot:
    """Unified chatbot with forecasting AND database querying capabilities"""
    
    def __init__(self, api_key: str, model_path: str, preprocessor_path: str):
        """Initialize unified chatbot"""
        
        # Initialize services
        self.forecast_service = ForecastService(model_path, preprocessor_path)
        self.database_service = DatabaseQueryService(api_key)
        
        # Configure Gemini client for function calling
        self.client = genai.Client(api_key=api_key)
        
        # Define function schemas
        self.function_schemas = [
            {
                "name": "forecast_category_demand",
                "description": "Predicts future demand for specific categories using XGBoost model with database intelligence.",
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
                            "description": "Historical data aggregation method",
                            "enum": ["average", "median", "recent"],
                            "default": "average" 
                        }
                    },
                    "required": ["category_name", "future_year_month"]
                }
            },
            {
                "name": "identify_top_selling_categories",
                "description": "Identifies top performing categories based on sales, revenue, and profit metrics",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "analysis_months": {
                            "type": "integer",
                            "description": "How many months to analyze (default: 6)",
                            "default": 6
                        },
                        "top_n": {
                            "type": "integer", 
                            "description": "Number of top categories to return (default: 5)",
                            "default": 5
                        }
                    }
                }
            },
            
            {
                "name": "query_database",
                "description": "Query the inventory and order database using natural language with semantic search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Natural language question about inventory, orders, sales, or products"
                        },
                        "top_k": {
                            "type": "integer", 
                            "description": "Number of most relevant records to retrieve",
                            "default": 5
                        }
                    },
                    "required": ["question"]
                }
            }
        ]
        
        # Create tools for function calling
        self.tools = [types.Tool(function_declarations=[
            types.FunctionDeclaration(**schema) for schema in self.function_schemas
        ])]
        
        print("✅ UnifiedGeminiChatbot initialized successfully")
        print(f"   Available functions: {len(self.function_schemas)}")
        print("   Capabilities: Forecasting, Trend Analysis, Database Querying")
        
    @contextmanager
    def shared_db_session(self):
        """Context manager for shared database session across all operations"""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def forecast_category_demand(self, category_name: str, future_year_month: str, 
                               scenario: str = "standard", aggregation_method: str = "average",
                               session=None, **kwargs) -> Dict[str, Any]:
        """Forecast function for Gemini to call"""
        return self.forecast_service.forecast_category_demand(
            category_name, future_year_month, scenario,
            aggregation_method, gemini_client=self.client, session=session, **kwargs
        )
    
    def identify_top_selling_categories(self, analysis_months: int = 6, 
                                       top_n: int = 5, session=None) -> Dict[str, Any]:
        """Top selling categories function - NOW accepts session"""
        return self.forecast_service.identify_top_selling_categories(
            analysis_months, top_n, session=session
        )

    def query_database(self, question: str, top_k: int = 5, session=None) -> Dict[str, Any]:
        """Database query function for Gemini to call"""
        return self.database_service.query_database(question, top_k, session=session)

    def determine_query_type(self, user_message: str) -> str:
        """Determine if this is a forecasting or database query"""
        forecast_keywords = ['forecast', 'predict', 'future', 'demand', 'will be', 'next month', 'scenario']
        trend_keywords = ['declining', 'trend', 'falling', 'decrease', 'risk', 'categories at risk']
        database_keywords = ['show me', 'what is', 'find', 'search', 'how many', 'which', 'when was', 'list']
        
        message_lower = user_message.lower()
        
        forecast_score = sum(1 for keyword in forecast_keywords if keyword in message_lower)
        trend_score = sum(1 for keyword in trend_keywords if keyword in message_lower)
        database_score = sum(1 for keyword in database_keywords if keyword in message_lower)
        
        if forecast_score > 0 or 'forecast' in message_lower:
            return "forecasting"
        elif trend_score > 0:
            return "trend_analysis"
        elif database_score > 0:
            return "database_query"
        else:
            return "general"

    def chat_with_unified_intelligence(self, user_message: str) -> str:
        """
        Main chat function with unified forecasting and database capabilities
        **FIXED** - Now properly uses shared session
        """
        try:
            # Use ONE session for the entire conversation
            with self.shared_db_session() as session:
                # Enhanced system prompt
                system_prompt = """You are an expert AI assistant for business intelligence, sales forecasting, and data analysis.

    You have access to multiple powerful capabilities:

    1. **XGBoost Forecasting Model** - Predicts future demand for categories using time series analysis
    - **Smart Category Mapping**: Automatically maps user categories to model categories using semantic analysis
    - Available model categories: Technology, Sports and Fitness, Clothing, Other
    
    2. **Top Selling Categories Analysis** - Identifies best performing categories by revenue and sales
    3. **Database Intelligence** - Query inventory and order data using semantic search

    **Semantic Category Mapping**: When users mention categories like "electronics", "computers", "gadgets" → maps to "Technology"
    When users mention "sports equipment", "fitness gear" → maps to "Sports and Fitness"
    When users mention "clothes", "apparel", "fashion" → maps to "Clothing"

    **Forecasting scenarios:**
    - Conservative: Lower prices, higher discounts (pessimistic market)
    - Standard: Historical averages (normal conditions)
    - Optimistic: Higher prices, lower discounts (strong market)

    **When to use each function:**
    - Future predictions/demand → use forecast_category_demand (with semantic mapping)
    - Top performers/best sellers → use identify_top_selling_categories
    - Historical data questions → use query_database
    - Mixed queries → combine multiple functions

    Always provide actionable business insights and explain the semantic mapping when categories are translated."""

                # Prepare conversation
                full_message = f"{system_prompt}\n\nUser: {user_message}"
                
                # Make request with function calling
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
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
                
                # Handle function calls - ALL using the same session
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_call = part.function_call
                            
                            if function_call.name == "forecast_category_demand":
                                return self._format_forecast_response(function_call, session)
                            elif function_call.name == "identify_top_selling_categories":
                                return self._format_top_categories_response(function_call, session)
                            elif function_call.name == "query_database":
                                return self._format_database_response(function_call, session)
                        
                        elif hasattr(part, 'text') and part.text:
                            return part.text
                
                return "I can help you with sales forecasting, trend analysis, and database queries. What would you like to know?"
                
        except Exception as e:
            return f"Error processing request: {str(e)}"

    def _format_forecast_response(self, function_call, session) -> str:
        """**UPDATED** Format forecasting response with semantic mapping details"""
        try:
            args = function_call.args
            result = self.forecast_category_demand(session=session, **args)
            
            if result["success"]:
                # **ENHANCED**: Show semantic mapping information
                mapping_info = ""
                if result.get('semantic_mapping'):
                    mapping = result['semantic_mapping']
                    if mapping['original_category'] != mapping['mapped_category']:
                        mapping_info = f"""
🔄 **SEMANTIC MAPPING:**
• Your category: "{mapping['original_category']}"
• Mapped to: "{mapping['mapped_category']}"
• This allows the AI to understand your intent and use the correct model category.
"""

                forecast_text = f"""
🔮 **DEMAND FORECAST RESULTS**
{mapping_info}
**Category:** {result['category']} → {result.get('mapped_category', 'N/A')}
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

    **📈 BUSINESS INSIGHTS:**
    Based on this forecast, I recommend:
    1. **Inventory Planning:** Stock approximately {result['total_predicted_demand']} units for {result['target_month']}
    2. **Scenario Analysis:** This {result['scenario']} scenario helps with risk assessment
    3. **Category Focus:** {result['model_info']['subcategories_predicted']} subcategories analyzed"""

                return forecast_text
            else:
                error_text = f"❌ Forecast Error: {result['error']}"
                if result.get('semantic_mapping'):
                    mapping = result['semantic_mapping']
                    error_text += f"\n🔄 Category mapping: '{mapping['original_category']}' → '{mapping['mapped_category']}'"
                return error_text
            
        except Exception as e:
            return f"❌ Error formatting forecast: {e}"
        
    def _format_top_categories_response(self, function_call, session) -> str:
        """Format top categories response using shared session"""
        try:
            args = function_call.args
            result = self.identify_top_selling_categories(session=session, **args)
            
            if result["success"]:
                if not result["top_categories"]:
                    return "📊 No sales data found for the analysis period."
                
                response = f"""🏆 **TOP SELLING CATEGORIES** (Last {result['analysis_period']})

**📈 PERFORMANCE RANKINGS:**
"""
                
                for i, cat in enumerate(result["top_categories"], 1):
                    response += f"""
**#{i}. {cat['category']}**
• Revenue: ${cat['total_revenue']:,}
• Sales: {cat['total_sales']} units
• Profit: ${cat['total_profit']:,}
• Orders: {cat['order_count']}
• Avg Order Value: ${cat['avg_order_value']}
• Profit Margin: {cat['profit_margin']:.1f}%
"""

                response += f"""
**📊 SUMMARY:**
• Best Performer: **{result['summary']['best_performer']['category']}**
• Total Revenue: ${result['summary']['total_revenue_analyzed']:,}
• Total Orders: {result['summary']['total_orders_analyzed']}
• Categories Analyzed: {result['total_categories_analyzed']}
"""
                return response
            else:
                return f"❌ Error analyzing top sellers: {result['error']}"
        except Exception as e:
            return f"❌ Error formatting top categories: {e}"

    def _format_database_response(self, function_call, session) -> str:
        """Format database response using shared session"""
        try:
            args = function_call.args
            result = self.query_database(session=session, **args)
            
            if result["success"]:
                response = f"""
🗄️ **DATABASE QUERY RESULTS**

**📋 Answer:**
{result['answer']}

**📊 Query Details:**
• Records analyzed: {result['sources_used']}
• Relevance scores: {[f"{score:.3f}" for score in result['relevance_scores'][:3]]}
• Data sources: {', '.join(result['record_ids'][:3])}
"""
                return response
            else:
                return f"❌ Database Error: {result['error']}"
        except Exception as e:
            return f"❌ Error formatting database response: {e}"

def create_unified_chatbot(api_key: str) -> UnifiedGeminiChatbot:
    """Create a unified chatbot instance"""
    backend_dir = Path(__file__).parent.parent.parent
    model_path = backend_dir / "Supervised_Models" / "ShernFai" / "model" / "salesforecast(categories).pkl"
    preprocessor_path = backend_dir / "Supervised_Models" / "ShernFai" / "model" / "salesforecast_preprocessor.pkl"
    
    return UnifiedGeminiChatbot(api_key, str(model_path), str(preprocessor_path))

def interactive_unified_chat(chatbot: UnifiedGeminiChatbot):
    """Interactive console for unified chatbot"""
    print("\n" + "="*70)
    print("🤖 UNIFIED GenAI Business Intelligence Assistant")
    print("="*70)
    print("🔮 Forecasting | 📉 Trend Analysis | 🗄️ Database Queries")
    print("\nExample queries:")
    print("• 'Forecast Technology demand for March 2025'")
    print("• 'Which categories are declining?'") 
    print("• 'Show me recent orders for electronics'")
    print("• 'What's the average price for sporting goods?'")
    print("\nType 'quit', 'exit', or 'bye' to end.")
    print("="*70)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Thanks for using the Unified GenAI Assistant! Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or type 'quit' to exit.")
                continue
            
            print("\n🤖 AI: Processing...")
            response = chatbot.chat_with_unified_intelligence(user_input)
            print(f"\n🤖 AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


# Example usage
if __name__ == "__main__":
    API_KEY = "AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw"
    
    if not API_KEY:
        print("❌ Error: API key not found")
        exit(1)
    
    try:
        print("🚀 Initializing Unified GenAI Business Intelligence Assistant...")
        chatbot = create_unified_chatbot(API_KEY)
        
        print("\nChoose testing mode:")
        print("1. Single test question")
        print("2. Interactive chat (recommended)")
        
        choice = input("\nEnter 1 or 2 (default: 2): ").strip()
        
        if choice == "1":
            # Test each capability
            print("\n🧪 TESTING FORECASTING:")
            response = chatbot.chat_with_unified_intelligence(
                "What will be the demand for Technology in March 2025?"
            )
            print(response)
            
            print("\n🧪 TESTING DATABASE QUERY:")
            response = chatbot.chat_with_unified_intelligence(
                "Show me information about recent electronics orders"
            )
            print(response)
            
            print("\n🧪 TESTING TREND ANALYSIS:")
            response = chatbot.chat_with_unified_intelligence(
                "Which categories are showing declining trends?"
            )
            print(response)
        else:
            interactive_unified_chat(chatbot)
        
    except Exception as e:
        print(f"❌ Error: {e}")