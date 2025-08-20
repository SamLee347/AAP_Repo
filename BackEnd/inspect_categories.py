#!/usr/bin/env python3
"""
Quick script to inspect the actual categories in the trained model's label encoder
"""
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "Supervised_Models"

def inspect_label_encoder():
    try:
        encoder = joblib.load(MODEL_DIR / "Jason/model/label_encoder.pkl")
        print("=== ACTUAL CATEGORIES FROM TRAINED MODEL ===")
        print(f"Label Encoder Type: {type(encoder)}")
        print(f"Number of classes: {len(encoder.classes_)}")
        print("\nCategories mapping:")
        for i, category in enumerate(encoder.classes_):
            print(f"{i}: '{category}'")
        print("\n" + "="*50)
        return encoder.classes_
    except Exception as e:
        print(f"Error loading label encoder: {e}")
        return None

if __name__ == "__main__":
    inspect_label_encoder()
