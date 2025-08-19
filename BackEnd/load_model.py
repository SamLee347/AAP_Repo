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

def load_report_generation_model():
    report_script = MODEL_DIR.parent / "Generative_Models" / "ReportGeneration" / "ReportGeneration.py"
    subprocess.run(
        ["python", str(report_script)],
        check=True,
        cwd=MODEL_DIR.parent / "Generative_Models" / "ReportGeneration"
    )
    return "Report generation script executed."

# Initialize models at startup
DISPOSAL_MODEL = load_disposal_model()
STORAGE_MODEL = load_storage_model()
FORECAST_MODEL = joblib.load(MODEL_DIR / "ShernFai/model/salesforecast(categories).pkl")
CATEGORY_MODEL = pickle.load(open(MODEL_DIR / "Jason/model/gradient_boosting_model.pkl", 'rb'))
REPORT_GENERATION_MODEL = load_report_generation_model