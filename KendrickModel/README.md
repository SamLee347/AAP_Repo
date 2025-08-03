# ML Model Flask Showcase App

This is a Flask web application that showcases your machine learning model for predicting product usage.

## Features

- 🌐 **Web Interface**: User-friendly form to input data and get predictions
- 🔗 **REST API**: JSON endpoint for programmatic access
- 📊 **Model Information**: Endpoint to get model details
- ⚠️ **Error Handling**: Comprehensive error handling and validation
- 🎨 **Responsive Design**: Clean, modern UI that works on all devices

## Setup

1. **Install Dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

2. **Ensure Model File**
   Make sure your `best_model.joblib` file is in the same directory as `app.py`

3. **Run the Application**
   ```cmd
   python app.py
   ```

4. **Access the Application**
   Open your browser to: `http://localhost:5000`

## API Endpoints

### Web Interface
- `GET /` - Home page with prediction form
- `POST /predict_form` - Handle form submissions

### API Endpoints
- `POST /predict` - Make predictions via JSON
- `GET /model_info` - Get model information

### Example API Usage

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Store ID": 1,
    "Product ID": 100,
    "Inventory Level": 50,
    "Units Sold": 25,
    "Units Ordered": 30,
    "Demand Forecast": 40
  }'
```

## Model Features

Your model expects these 6 features:
1. Store ID
2. Product ID  
3. Inventory Level
4. Units Sold
5. Units Ordered
6. Demand Forecast

## Customization

To adapt this for your own model:
1. Update `feature_cols` in `app.py` with your model's features
2. Modify the prediction logic if needed (binary vs multi-class, etc.)
3. Update the HTML template with relevant descriptions
4. Add your model file as `best_model.joblib`

## Deployment

For production deployment, consider:
- Using a production WSGI server like Gunicorn
- Setting up proper environment variables
- Adding authentication if needed
- Implementing logging
- Using a reverse proxy like nginx
