# Supply Chain Sales Prediction Flask App

This Flask application deploys a Random Forest Regression model to predict order quantities for supply chain management.

## Features

- **Machine Learning Model**: Random Forest Regression trained on supply chain data
- **Web Interface**: Clean, responsive web interface for making predictions
- **Real-time Predictions**: Instant forecasting based on user inputs
- **Top Products**: Model trained on the top 10 most popular products
- **Multiple Countries**: Supports predictions for various international markets

## Model Information

- **Algorithm**: Random Forest Regression
- **Training Data**: 3+ years of historical supply chain data
- **Features**: Order date, product information, customer segment, country, discounts
- **Target**: Order Item Quantity (number of units ordered)

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   Open your web browser and go to: `http://127.0.0.1:5000`

### Alternative: Use the batch file (Windows)
Double-click `run_app.bat` to automatically install dependencies and start the server.

## Usage

1. **Open the web interface** at `http://127.0.0.1:5000`

2. **Fill out the prediction form**:
   - **Order Year**: Select the year for the prediction (2015-2025)
   - **Order Month**: Choose the month (January-December)
   - **Product Name**: Select from the top 10 products in the dataset
   - **Order Country**: Choose the destination country
   - **Customer Segment**: Select Consumer, Corporate, or Home Office

3. **Click "Predict Order Quantity"** to get the forecast

4. **View the prediction**: The model will display the predicted number of units

## Available Products

The model supports predictions for these top 10 products:
- Nike Men's Free 5.0+ Running Shoe
- Nike Men's CJ Elite 2 TD Football Cleat
- Perfect Fitness Perfect Rip Deck
- Nike Men's Dri-FIT Victory Golf Polo
- Under Armour Girls' Toddler Spine Surge Running Shoe
- Diamondback Women's Serene Classic Comfort Bike
- Field & Stream Sportsman 16 Gun Fire Safe
- Fighting video games
- Pelican Sunstream 100 Kayak
- O'Brien Men's Neoprene Life Vest

## Customer Segments
- **Consumer**: Individual customers
- **Corporate**: Business customers
- **Home Office**: Small business/home office customers

## File Structure

```
AAP Project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── run_app.bat           # Windows startup script
├── README.md             # This file
├── templates/
│   └── index.html        # Web interface template
├── model/
│   ├── model.pkl         # Trained Random Forest model
│   └── preprocessor.pkl  # Data preprocessing components
├── dataset/              # Training data
└── LSFmodel.ipynb       # Jupyter notebook for model development
```

## Technical Details

### Model Features (70 total features):
- Order YearMonth (encoded date)
- Product Name (label encoded)
- Mean Discount Rate
- Total Discount Given
- Order Frequency
- Average Quantity per Order
- Customer Segment (one-hot encoded)
- Order Country (one-hot encoded for 65+ countries)

### API Endpoints

- `GET /`: Main page with prediction form
- `POST /predict`: Submit prediction request and get results

## Troubleshooting

### Common Issues:

1. **Import errors**: Make sure all packages are installed:
   ```bash
   pip install Flask joblib pandas scikit-learn numpy
   ```

2. **Model file not found**: Ensure `model/model.pkl` and `model/preprocessor.pkl` exist

3. **Port already in use**: Flask runs on port 5000 by default. Change the port by modifying `app.py`:
   ```python
   app.run(debug=True, port=5001)
   ```

### Error Messages:
- If you see prediction errors, ensure all form fields are filled correctly
- Product names must match exactly with the available options
- Year should be between 2015-2025

## Development

To modify or retrain the model:
1. Open `LSFmodel.ipynb` in Jupyter Notebook
2. Make your changes to the data processing or model training
3. Re-run the notebook to generate new model files
4. Restart the Flask app to use the updated model

## Performance Notes

- The model achieves good performance on the training data
- Predictions are based on historical patterns in the supply chain data
- Results should be used as guidance for inventory planning decisions

## Security Notes

- This is a development/demo application
- For production use, add proper authentication and input validation
- Consider using HTTPS and secure configurations

## Support

For issues or questions about the model or application, check:
1. The Jupyter notebook for model details
2. Flask documentation for web framework questions
3. Scikit-learn documentation for machine learning details
