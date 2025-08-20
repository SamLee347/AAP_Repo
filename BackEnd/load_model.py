# load_model.py (improved version)
import pickle
import joblib
from pathlib import Path
import subprocess

MODEL_DIR = Path(__file__).parent / "Supervised_Models"

def load_disposal_model():
    artifacts = joblib.load(MODEL_DIR / "Kendrick/best_model.joblib")
    return {
        'model': artifacts['model'],
        'threshold': artifacts['threshold'],
        'features': ['ItemQuantity', 'UnitsSold', 'ItemQuantityLag', 'Turnover_Rate']  # Example features
    }

def load_storage_model():
    model = pickle.load(open(MODEL_DIR / "Samuel/storage_prediction_model.pkl", 'rb'))
    return {
        'model': model,
        'features': ['Priority', 'ItemCategory', 'Size', 'OrderQuantity', 'Weight']  # Example features
    }


def load_forecasting_model():
    """Load ShernFai's sales forecasting model"""
    try:
        model = joblib.load(MODEL_DIR / "ShernFai/model/salesforecast(categories).pkl")
        
        # Load preprocessor data
        with open(MODEL_DIR / "ShernFai/model/salesforecast_preprocessor.pkl", 'rb') as f:
            preprocessor_data = pickle.load(f)
        
        return {
            'model': model,
            'preprocessor': preprocessor_data,
            'features': ['Category Name', 'Average Product Price', 'Customer Segment', 'Order Item Discount Rate', 'Year', 'Month', 'Quarter'],
            'feature_columns': preprocessor_data.get('feature_columns', [])  # Add this line
        }
    except Exception as e:
        print(f"Warning: Could not load forecasting model: {e}")
        return None

def load_report_generation_model():
    report_script = MODEL_DIR.parent / "Generative_Models" / "ReportGeneration" / "ReportGeneration.py"
    subprocess.run(
        ["python", str(report_script)],
        check=True,
        cwd=MODEL_DIR.parent / "Generative_Models" / "ReportGeneration"
    )
    return "Report generated successfully!"

# Initialize models at startup
DISPOSAL_MODEL = load_disposal_model()
STORAGE_MODEL = load_storage_model()
FORECAST_MODEL = load_forecasting_model()
CATEGORY_MODEL = pickle.load(open(MODEL_DIR / "Jason/model/gradient_boosting_model.pkl", 'rb'))
REPORT_GENERATION_MODEL = load_report_generation_model