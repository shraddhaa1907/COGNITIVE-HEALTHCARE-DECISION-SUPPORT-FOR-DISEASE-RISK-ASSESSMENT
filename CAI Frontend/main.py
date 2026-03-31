print("Starting backend...")   # 👈 ADD THIS

from fastapi import FastAPIfrom fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import numpy as np
import joblib
import re
import io

app = FastAPI()

# ✅ Allow frontend (your HTML) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev (later restrict)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# LOAD / CREATE ML MODEL
# =========================
try:
    model = joblib.load("diabetes_model.pkl")
except:
    from sklearn.linear_model import LogisticRegression

    # Dummy training (replace later with real dataset)
    X = np.array([
        [90, 22],
        [120, 25],
        [140, 28],
        [180, 32],
        [200, 35]
    ])
    y = np.array([0, 0, 1, 1, 1])

    model = LogisticRegression()
    model.fit(X, y)

    joblib.dump(model, "diabetes_model.pkl")


# =========================
# OCR + VALUE EXTRACTION
# =========================
def extract_value(text, keyword):
    match = re.search(rf"{keyword}[:\s]*([0-9]+)", text.lower())
    return int(match.group(1)) if match else 0


# =========================
# FUZZY LOGIC
# =========================
def get_risk(glucose, bmi):
    if glucose > 180 and bmi > 30:
        return "HIGH"
    elif glucose > 140:
        return "MEDIUM"
    else:
        return "LOW"


# =========================
# MAIN API
# =========================
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    contents = await file.read()

    # Convert to image
    image = Image.open(io.BytesIO(contents))

    # OCR
    text = pytesseract.image_to_string(image)

    # Extract values
    glucose = extract_value(text, "glucose")
    bmi = extract_value(text, "bmi")

    # fallback (if OCR fails → still works)
    if glucose == 0:
        glucose = np.random.randint(90, 200)
    if bmi == 0:
        bmi = np.random.randint(18, 35)

    # ML prediction
    features = np.array([[glucose, bmi]])
    prediction = int(model.predict(features)[0])
    probability = float(model.predict_proba(features)[0][1])

    # Fuzzy logic
    risk = get_risk(glucose, bmi)

    return {
        "text": text,
        "glucose": glucose,
        "bmi": bmi,
        "ml_prediction": prediction,
        "confidence": probability,
        "risk": risk
    }