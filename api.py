import io
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.prediction import (
    BATCH_REQUIRED_COLUMNS,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_ROWS,
    predict_batch_bookings,
    to_safe_csv_bytes,
)

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hotel_api")

# Global state for loaded models and metadata
app_state: Dict[str, Any] = {
    "classifier": None,
    "regressor": None,
    "metrics": {},
    "threshold": 0.45,
    "eda": {},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading ML models and evaluation artifacts...")
    # Load metrics
    metrics_path = MODELS_DIR / "metrics_summary.json"
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            app_state["metrics"] = json.load(f)
            app_state["threshold"] = float(
                app_state["metrics"].get("classification_threshold", 0.45)
            )
            logger.info(f"Loaded threshold: {app_state['threshold']}")

    # Load EDA Cache
    eda_cache_path = MODELS_DIR / "eda_cache.json"
    if eda_cache_path.exists():
        with open(eda_cache_path, "r", encoding="utf-8") as f:
            app_state["eda"] = json.load(f)
            logger.info("Loaded EDA analytics cache.")

    # Load models
    cls_path = MODELS_DIR / "cancellation_classifier.joblib"
    reg_path = MODELS_DIR / "pricing_regressor.joblib"

    if cls_path.exists() and reg_path.exists():
        logger.info("Deserializing classification and regression pipelines...")
        app_state["classifier"] = joblib.load(cls_path)
        app_state["regressor"] = joblib.load(reg_path)
        logger.info("Models loaded successfully and ready for inference.")
    else:
        logger.warning(
            "Model files not found. Train models first using train_pipeline.py."
        )

    yield
    logger.info("Shutting down hotel API service.")


app = FastAPI(
    title="GrandVista AI - Hotel Revenue & Reservation Intelligence API",
    description="Production-grade API for hotel booking cancellation probability and ADR pricing estimation.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BookingInput(BaseModel):
    no_of_adults: int = Field(2, ge=1, le=10, description="Adult guests (min 1)")
    no_of_children: int = Field(0, ge=0, le=10, description="Child guests")
    no_of_weekend_nights: int = Field(1, ge=0, le=20, description="Weekend nights")
    no_of_week_nights: int = Field(2, ge=0, le=30, description="Week nights")
    type_of_meal_plan: str = Field(
        "Meal Plan 1", description="Meal plan (Meal Plan 1/2/3, Not Selected)"
    )
    required_car_parking_space: int = Field(
        0, ge=0, le=1, description="1 if parking requested, else 0"
    )
    room_type_reserved: str = Field(
        "Room_Type 1", description="Room type reserved"
    )
    lead_time: int = Field(
        30, ge=0, le=1000, description="Days between booking and check-in"
    )
    arrival_year: int = Field(2018, ge=2015, le=2030, description="Arrival year")
    arrival_month: int = Field(6, ge=1, le=12, description="Arrival month (1-12)")
    arrival_date: int = Field(15, ge=1, le=31, description="Arrival day of month")
    market_segment_type: str = Field(
        "Online", description="Booking channel/segment"
    )
    repeated_guest: int = Field(
        0, ge=0, le=1, description="1 if repeated guest, else 0"
    )
    no_of_previous_cancellations: int = Field(
        0, ge=0, le=100, description="Past cancellations"
    )
    no_of_previous_bookings_not_canceled: int = Field(
        0, ge=0, le=100, description="Past completed stays"
    )
    avg_price_per_room: float = Field(
        105.0, ge=0.0, description="Quoted rate (ADR) per room"
    )
    no_of_special_requests: int = Field(
        1, ge=0, le=20, description="Special requests count"
    )


class PredictionResponse(BaseModel):
    predicted_adr: float
    cancellation_probability: float
    cancellation_risk: str
    predicted_status: str
    projected_total_revenue: float
    total_stay_nights: int
    recommendations: List[str]


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "classifier_ready": app_state["classifier"] is not None,
        "regressor_ready": app_state["regressor"] is not None,
        "classification_threshold": app_state["threshold"],
    }


@app.get("/api/metadata")
def get_metadata():
    return {
        "classification_threshold": app_state["threshold"],
        "options": {
            "meals": [
                "Meal Plan 1",
                "Meal Plan 2",
                "Meal Plan 3",
                "Not Selected",
            ],
            "rooms": [
                "Room_Type 1",
                "Room_Type 2",
                "Room_Type 3",
                "Room_Type 4",
                "Room_Type 5",
                "Room_Type 6",
                "Room_Type 7",
                "Other",
            ],
            "segments": [
                "Online",
                "Offline",
                "Corporate",
                "Direct",
                "Groups",
                "Aviation",
                "Complementary",
                "Unknown",
            ],
            "years": [2015, 2016, 2017, 2018],
        },
        "metrics_summary": app_state["metrics"],
    }


@app.get("/api/eda")
def get_eda_data():
    if not app_state["eda"]:
        raise HTTPException(
            status_code=503, detail="EDA cache is not ready yet."
        )
    return app_state["eda"]


@app.get("/api/template")
def download_template():
    sample_data = pd.DataFrame(
        [
            {
                "no_of_adults": 2,
                "no_of_children": 0,
                "no_of_weekend_nights": 1,
                "no_of_week_nights": 2,
                "type_of_meal_plan": "Meal Plan 1",
                "required_car_parking_space": 0,
                "room_type_reserved": "Room_Type 1",
                "lead_time": 45,
                "arrival_year": 2018,
                "arrival_month": 7,
                "arrival_date": 14,
                "market_segment_type": "Online",
                "repeated_guest": 0,
                "no_of_previous_cancellations": 0,
                "no_of_previous_bookings_not_canceled": 0,
                "avg_price_per_room": 115.0,
                "no_of_special_requests": 1,
            },
            {
                "no_of_adults": 1,
                "no_of_children": 0,
                "no_of_weekend_nights": 0,
                "no_of_week_nights": 3,
                "type_of_meal_plan": "Meal Plan 1",
                "required_car_parking_space": 1,
                "room_type_reserved": "Room_Type 1",
                "lead_time": 7,
                "arrival_year": 2018,
                "arrival_month": 8,
                "arrival_date": 20,
                "market_segment_type": "Corporate",
                "repeated_guest": 1,
                "no_of_previous_cancellations": 0,
                "no_of_previous_bookings_not_canceled": 4,
                "avg_price_per_room": 95.0,
                "no_of_special_requests": 2,
            },
            {
                "no_of_adults": 2,
                "no_of_children": 2,
                "no_of_weekend_nights": 2,
                "no_of_week_nights": 4,
                "type_of_meal_plan": "Meal Plan 2",
                "required_car_parking_space": 1,
                "room_type_reserved": "Room_Type 4",
                "lead_time": 120,
                "arrival_year": 2018,
                "arrival_month": 8,
                "arrival_date": 10,
                "market_segment_type": "Online",
                "repeated_guest": 0,
                "no_of_previous_cancellations": 1,
                "no_of_previous_bookings_not_canceled": 0,
                "avg_price_per_room": 175.0,
                "no_of_special_requests": 0,
            },
        ]
    )
    csv_bytes = sample_data.to_csv(index=False).encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=hotel_bookings_template.csv"
        },
    )


def generate_recommendations(
    prob: float,
    predicted_adr: float,
    quoted_price: float,
    lead_time: int,
    total_nights: int,
    repeated_guest: int,
) -> List[str]:
    recs = []
    if prob >= 0.70:
        recs.append(
            "⚠️ High Cancellation Risk: Enforce a non-refundable deposit or a 48-hour prepayment window."
        )
        recs.append(
            "💡 Revenue Protection: Allow controlled overbooking allocation for this room inventory."
        )
    elif prob >= 0.35:
        recs.append(
            "⚖️ Moderate Risk: Send automated pre-arrival SMS/Email confirmations with personalized check-in perks."
        )
    else:
        recs.append(
            "✅ High Certainty Guest: Ideal candidate for room upgrades or complimentary dining vouchers."
        )

    if predicted_adr > quoted_price * 1.15:
        recs.append(
            f"📈 Upsell Potential: Market rate benchmark (${predicted_adr:.2f}) exceeds current quote (${quoted_price:.2f}). Consider upward rate adjustment."
        )
    elif predicted_adr < quoted_price * 0.85:
        recs.append(
            f"📉 Price Sensitivity: Quoted rate (${quoted_price:.2f}) is significantly above estimated market value (${predicted_adr:.2f}), which may induce cancellation."
        )

    if lead_time > 90 and prob > 0.40:
        recs.append(
            "⏳ Extended Lead Time: Re-engage traveler 30 and 14 days prior to arrival to confirm itinerary."
        )

    if repeated_guest == 1:
        recs.append(
            "⭐ Loyal Returning Guest: Prioritize preferred floor and VIP recognition at check-in."
        )

    return recs


@app.post("/api/predict", response_model=PredictionResponse)
def predict_single(booking: BookingInput):
    if app_state["classifier"] is None or app_state["regressor"] is None:
        raise HTTPException(
            status_code=503,
            detail="Machine learning models are not initialized.",
        )

    df = pd.DataFrame([booking.model_dump()])
    try:
        results = predict_batch_bookings(
            df,
            app_state["classifier"],
            app_state["regressor"],
            app_state["threshold"],
        )
        row = results.iloc[0]
        stay_nights = (
            booking.no_of_weekend_nights + booking.no_of_week_nights
        ) or 1

        recs = generate_recommendations(
            prob=float(row["cancellation_probability"]),
            predicted_adr=float(row["predicted_adr"]),
            quoted_price=float(booking.avg_price_per_room),
            lead_time=int(booking.lead_time),
            total_nights=stay_nights,
            repeated_guest=int(booking.repeated_guest),
        )

        return PredictionResponse(
            predicted_adr=round(float(row["predicted_adr"]), 2),
            cancellation_probability=round(
                float(row["cancellation_probability"]), 4
            ),
            cancellation_risk=str(row["cancellation_risk"]),
            predicted_status=str(row["predicted_status"]),
            projected_total_revenue=round(
                float(row["projected_total_revenue"]), 2
            ),
            total_stay_nights=int(stay_nights),
            recommendations=recs,
        )
    except Exception as e:
        logger.exception("Single prediction error")
        raise HTTPException(
            status_code=400, detail=f"Prediction error: {str(e)}"
        )


@app.post("/api/predict-batch")
async def predict_batch(file: UploadFile = File(...)):
    if app_state["classifier"] is None or app_state["regressor"] is None:
        raise HTTPException(
            status_code=503, detail="Models are not initialized."
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400, detail="File exceeds maximum allowed size (10 MB)."
        )

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Unable to parse CSV file: {str(e)}"
        )

    if len(df) > MAX_UPLOAD_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed rows ({MAX_UPLOAD_ROWS:,}).",
        )

    missing = [c for c in BATCH_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns in CSV: {', '.join(missing[:5])}",
        )

    try:
        results = predict_batch_bookings(
            df,
            app_state["classifier"],
            app_state["regressor"],
            app_state["threshold"],
        )
    except Exception as e:
        logger.exception("Batch prediction failure")
        raise HTTPException(
            status_code=400, detail=f"Batch processing error: {str(e)}"
        )

    total_rows = len(results)
    expected_cancels = int((results["predicted_status"] == "Canceled").sum())
    cancel_rate = (
        round((expected_cancels / total_rows) * 100, 2)
        if total_rows > 0
        else 0.0
    )
    total_rev = round(float(results["projected_total_revenue"].sum()), 2)
    avg_adr = round(float(results["predicted_adr"].mean()), 2)

    risk_counts = results["cancellation_risk"].value_counts().to_dict()

    preview_cols = [
        "lead_time",
        "market_segment_type",
        "room_type_reserved",
        "avg_price_per_room",
        "predicted_adr",
        "cancellation_probability",
        "cancellation_risk",
        "predicted_status",
        "projected_total_revenue",
    ]
    if "booking_status" in results.columns:
        preview_cols.insert(0, "booking_status")

    preview_df = results[preview_cols].head(50).copy()
    preview_df["cancellation_probability"] = (
        preview_df["cancellation_probability"] * 100
    ).round(1)
    preview_df["predicted_adr"] = preview_df["predicted_adr"].round(2)
    preview_df["projected_total_revenue"] = preview_df[
        "projected_total_revenue"
    ].round(2)

    # Store full results CSV in memory for fast download
    csv_bytes = to_safe_csv_bytes(results)

    return {
        "summary": {
            "total_bookings": total_rows,
            "expected_cancellations": expected_cancels,
            "cancellation_rate_percent": cancel_rate,
            "total_projected_revenue": total_rev,
            "average_predicted_adr": avg_adr,
            "risk_breakdown": {
                "Low": int(risk_counts.get("Low", 0)),
                "Medium": int(risk_counts.get("Medium", 0)),
                "High": int(risk_counts.get("High", 0)),
            },
        },
        "preview": preview_df.to_dict(orient="records"),
        "csv_download_base64": csv_bytes.decode("latin1"),
    }


# Serve static frontend files
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "GrandVista AI Hotel Intelligence API is active."}
