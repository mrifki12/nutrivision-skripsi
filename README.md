# NutriVision AI

Web app for estimating the nutrition of Indonesian food from a photo. Upload a food image and the app identifies the dish with an EfficientNetB0 model, then shows its nutrition per 100 g — calories, protein, fat and carbohydrates — along with a short Nutrition Coach tip. This project was built as a thesis (skripsi) project.

## Features

- Upload a food photo (JPG, PNG or JPEG, up to 16 MB) and get an instant prediction
- Recognizes 15 Indonesian dishes: Ayam Goreng, Bakso, Gado-Gado, Kentang Goreng, Martabak, Mie Goreng, Nasi Goreng, Nasi Padang, Pisang Goreng, Rendang, Sate, Seblak, Siomay, Soto, and Tempe Tahu Goreng
- Nutrition breakdown per 100 g for each recognized dish (calories, protein, fat, carbohydrates)
- Nutrition Coach tips and suggestions for each dish, e.g. adding vegetables or choosing a lighter alternative
- Rejects non-food images: predictions with confidence below 45% are reported as not a recognized food photo
- Simple web interface served from the `templates/` folder, with styles and uploaded images in `static/`

## Tech Stack

- Python, Flask 3
- TensorFlow / Keras — EfficientNetB0 image classification model (`output_EfficientNetB0/best_model_EfficientNetB0.keras`)
- Pillow and NumPy for image preprocessing
- HTML, CSS and JavaScript for the front end

## Getting Started

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open http://localhost:5000 in your browser. The trained model file must be present at `output_EfficientNetB0/best_model_EfficientNetB0.keras` before running the app.

## Project Structure

```
app.py                  # Flask app: routes, model loading, prediction, nutrition data
requirements.txt        # Python dependencies
templates/              # HTML pages (index)
static/                 # CSS, JS and uploaded images
output_EfficientNetB0/  # Trained EfficientNetB0 model
```
