import joblib

# Load the label encoder
encoder = joblib.load('Supervised_Models/Jason/model/label_encoder.pkl')
print("Label encoder classes:", encoder.classes_)
print("Encoder type:", type(encoder))

# Test inverse transform with a few numbers
for i in range(len(encoder.classes_)):
    try:
        category = encoder.inverse_transform([i])[0]
        print(f"Index {i} -> Category: {category}")
    except Exception as e:
        print(f"Error with index {i}: {e}")

# Test the specific case that's showing as "6"
try:
    category_6 = encoder.inverse_transform([6])[0]
    print(f"Index 6 specifically maps to: {category_6}")
except Exception as e:
    print(f"Error with index 6: {e}")
