# load_model.py (fixed version)
import pickle
import joblib
from pathlib import Path
import subprocess

MODEL_DIR = Path(__file__).parent / "Supervised_Models"

def load_disposal_model():
    artifacts = joblib.load(MODEL_DIR / "Kendrick/best_model.joblib")
    model = artifacts['model']
    threshold = artifacts['threshold']
    return {
        'model': model,
        'threshold': threshold,
        'features': ['ItemQuantity', 'UnitsSold', 'ItemQuantityLag', 'Turnover_Rate']
    }

def load_storage_model():
    model = pickle.load(open(MODEL_DIR / "Samuel/storage_prediction_model.pkl", 'rb'))
    return {
        'model': model,
        'features': ['Priority', 'ItemCategory', 'Size', 'OrderQuantity', 'Weight']
    }

def load_forecast_model():
    model = joblib.load(MODEL_DIR / "ShernFai/model/salesforecast(categories).pkl")
    return {
        'model': model,
        'type': 'forecasting'
    }

def load_category_model():
    model = joblib.load(MODEL_DIR / "Jason/model/gradient_boosting_model.pkl")
    encoder = joblib.load(MODEL_DIR / "Jason/model/label_encoder.pkl")
    return {
        'model': model,
        'label_encoder': encoder,
        'features': ['Price', 'Sales', 'Order_Profit', 'ProductWeight', 'Quantity'],
        'type': 'classification'
    }

def load_report_generation_model():
    report_script = MODEL_DIR.parent / "Generative_Models" / "ReportGeneration" / "ReportGeneration.py"
    subprocess.run(
        ["python", str(report_script)],
        check=True,
        cwd=MODEL_DIR.parent / "Generative_Models" / "ReportGeneration"
    )
    return "Report generated successfully!"

# Initialize models at startup with consistent structure
DISPOSAL_MODEL = load_disposal_model()
STORAGE_MODEL = load_storage_model()
FORECAST_MODEL = load_forecast_model()
CATEGORY_MODEL = load_category_model()  # Now this is a dict with 'model' key!
REPORT_GENERATION_MODEL = load_report_generation_model