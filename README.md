# Hotel Reservation Cancellation & ADR Prediction

An interactive Machine Learning system and modern web application suite that estimates cancellation risk and average daily room rate (ADR) from three harmonized hotel-booking datasets. It provides single-booking intelligence, batch CSV predictions, executive market charts, and time-aware model evaluation.

> **Important:** This is a historical-data prototype, not a validated revenue-management system. The three source datasets span 2015–2018 and represent different hotel populations and input schemas. Predictions are advisory; validate on recent, hotel-specific bookings before operational use.

## Features

- **GrandVista AI Modern Dashboard**: Production-grade UI built with FastAPI, Tailwind CSS, Lucide Icons, and Chart.js with full English & Arabic (RTL) support.
- **Single Booking Intelligence**: Instant cancellation probability gauge, predicted ADR rate, projected stay value, and automated revenue-management strategy recommendations.
- **Batch CSV Studio**: Drag-and-drop processing for up to 10,000 bookings with risk distribution filters and spreadsheet-safe exports.
- **Executive Analytics**: Interactive charts showing market channel cancel rates, historical annual trends, lead-time risk curves, and room-type ADR benchmarks.
- **Model Governance & Audit**: Transparent chronological evaluation metrics, bootstrap intervals, and SHA-256 data integrity tracking.
- **Interactive OpenAPI Docs**: Complete Swagger UI available at `/docs`.

## Project layout

```text
.
├── api.py                            # Production FastAPI backend service
├── run_dashboard.py                  # One-click dashboard server launcher
├── app.py                            # Streamlit prototype app
├── train_pipeline.py                 # Multi-source training and evaluation pipeline
├── requirements.txt
├── requirements-notebook.txt
├── data/
│   ├── Hotel Reservations.csv
│   ├── hotel_bookings.csv
│   ├── hotel_bookings1.csv
│   └── merged_hotel_reservations.csv
├── models/
│   ├── metrics_summary.json
│   └── eda_cache.json
├── static/
│   └── index.html                    # GrandVista AI modern luxury dashboard
├── src/
│   ├── prediction.py
│   ├── datasets.py
│   └── preprocessing.py
├── tests/
│   ├── test_prediction.py
│   └── test_api.py
├── Hotel_Booking_ML_Full_Project.ipynb
└── Hotel_ML_Project_Presentation.pdf
```

## Requirements and local setup

Use Python 3.11. From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

### 1. Launch Modern Intelligence Dashboard (Recommended ⭐)
```powershell
python run_dashboard.py
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
Interactive OpenAPI Swagger docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Launch Streamlit Prototype
```powershell
python -m streamlit run app.py
```

The notebook's plotting libraries are optional for the web application. Install `requirements-notebook.txt` to use the notebook in Jupyter or VS Code.

Only load model files from trusted sources; `joblib` artifacts can execute code when deserialized.

## Batch CSV predictions

Open **Batch Booking Analysis**, download the template, fill it in, and upload the CSV. Each row represents one prospective booking. The file must contain these columns:

```text
no_of_adults
no_of_children
no_of_weekend_nights
no_of_week_nights
type_of_meal_plan
required_car_parking_space
room_type_reserved
lead_time
arrival_year
arrival_month
arrival_date
market_segment_type
repeated_guest
no_of_previous_cancellations
no_of_previous_bookings_not_canceled
avg_price_per_room
no_of_special_requests
```

An optional `booking_status` column is preserved in the results but never passed to either model. Numeric inputs must be finite and non-negative; counts must be whole numbers, guest count must be at least one, and month/day must be within 1–12/1–31. Same-day bookings are supported. Uploads are limited to 10 MB, 10,000 rows, and 100 columns.

The output includes the input fields plus:

- `predicted_adr`: estimated average daily room rate.
- `cancellation_probability`: model probability between 0 and 1.
- `predicted_status`: cancellation classification at the validation-selected threshold.
- `cancellation_risk`: Low, Medium, or High, using probability cutoffs of 0.35 and 0.70.
- `projected_total_revenue`: estimated ADR multiplied by the number of stay nights.

## Dataset and evaluation

Training merges these three unique source files:

| Source | Rows | Arrival years | Schema |
|---|---:|---|---|
| `Hotel Reservations.csv` | 36,275 | 2017–2018 | 19 columns |
| `hotel_bookings.csv` | 5,000 | 2015–2017 | 32 columns |
| `hotel_bookings1.csv` | 119,390 | 2015–2017 | 32 columns |

The three sources contain **160,665 raw rows**. Training excludes **183** records with no guests or a negative ADR, leaving **160,482 usable bookings**. Source-level counts, exclusions, and SHA-256 fingerprints are recorded in `models/metrics_summary.json`.

The chronological split fits candidates on 2015–2016 and selects the classifier and its threshold to maximize F1 on 2017 `Hotel Reservations.csv` rows. It then scores the 2018 rows from that source as a diagnostic split.

The current diagnostic metrics are recorded in `models/metrics_summary.json`:
- **Cancellation Classifier**: Accuracy 86.12%, Precision 84.25%, Recall 76.46%, and F1 80.17%.
- **ADR Regressor**: MAE $13.62, RMSE $19.65, and R² 0.7035.

To retrain:

```powershell
python train_pipeline.py
```

## Automated Tests

Run focused unit and API tests from the project root:

```powershell
python -m unittest discover -s tests -v
# or test API endpoints directly:
python tests/test_api.py
```
