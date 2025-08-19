
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

def simple_console_test():
    """Simple console interface to test the GenAI model"""
    print("🤖 GenAI Forecasting Console Test")
    print("="*50)
    print("Type your questions and press Enter.")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'examples' to see sample queries.")
    print("="*50)
    
    # Sample queries for reference
    examples = [
        "Predict Sporting demand for March 2025",
        "Which categories are declining?",
        "What was the most used category in 2024?",
        "Forecast Technology demand for June 2025",
        "Show me categories that need inventory reduction"
    ]
    
    while True:
        try:
            # Get user input
            user_input = input("\n🔍 Your query: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'examples':
                print("\n📝 Example queries you can try:")
                for i, example in enumerate(examples, 1):
                    print(f"   {i}. {example}")
                continue
            elif not user_input:
                print("Please enter a query or type 'exit' to quit.")
                continue
            
            # Process the query
            print(f"\n🤔 Processing: {user_input}")
            print("⏳ Please wait...")
            
            # Import and use the GenAI function
            try:
                from BackEnd.Generative_Models.ChatBot.DONOTRUNTHIS import query_gemini
                response = query_gemini(user_input)
                
                print(f"\n🤖 AI Response:")
                print("-" * 60)
                print(response)
                print("-" * 60)
                
            except ImportError as e:
                print(f"❌ Import Error: {e}")
                print("Make sure genaiChatbot.py is properly configured.")
                break
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                print("Try rephrasing your question or check your configuration.")
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def quick_test_queries():
    """Run a few test queries automatically"""
    print("🚀 Running Quick Test Queries...")
    print("="*50)
    
    test_queries = [
        "Predict Office Supplies demand for March 2025",
        "Which categories are declining?",
        "Top performing category"
    ]
    
    try:
        from BackEnd.Generative_Models.ChatBot.DONOTRUNTHIS import query_gemini
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📊 Test {i}: {query}")
            print("-" * 40)
            
            try:
                response = query_gemini(query)
                print(f"Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            except Exception as e:
                print(f"Error: {e}")
            
            print("-" * 40)
            
    except ImportError:
        print("❌ Could not import genaiChatbot. Check your setup.")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function - choose test mode"""
    print("Choose testing mode:")
    print("1. Interactive Console Chat")
    print("2. Quick Test Queries")
    print("3. Both")
    
    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            simple_console_test()
            break
        elif choice == "2":
            quick_test_queries()
            break
        elif choice == "3":
            quick_test_queries()
            print("\n" + "="*50)
            simple_console_test()
            break
        else:
            print("Please enter 1, 2, or 3")

if __name__ == "__main__":
    main()