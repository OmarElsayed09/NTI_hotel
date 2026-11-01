# Hotel Reservation Cancellation & ADR Prediction

An interactive Streamlit application and machine learning pipeline that estimates cancellation risk and average daily room rate (ADR) from three harmonized hotel-booking datasets. It provides single-booking predictions, batch CSV predictions, exploratory charts, and time-aware model evaluation.

> **Important:** This is a historical-data prototype, not a validated revenue-management system. The three source datasets span 2015–2018 and represent different hotel populations and input schemas. Predictions are advisory; validate on recent, hotel-specific bookings before operational use.

## Features

- Cancellation probability, predicted status, and estimated ADR for a booking.
- Batch predictions for up to 10,000 bookings per CSV upload.
- Downloadable input template and spreadsheet-safe prediction results.
- Arabic/English interface and market charts.
- Chronological evaluation: model selection and threshold tuning within 2017, followed by a 2018 diagnostic split.
- Shared preprocessing for training and inference, bounded uploads, and logged prediction failures.

## Project layout

```text
.
├── app.py
├── train_pipeline.py
├── requirements.txt
├── requirements-notebook.txt
├── data/
│   ├── Hotel Reservations.csv
│   ├── hotel_bookings.csv
│   ├── hotel_bookings1.csv
│   └── merged_hotel_reservations.csv
├── models/
│   └── metrics_summary.json
├── presentation_build/
│   ├── presentation.html
│   └── slides/
├── scripts/
│   └── generate_presentation.py
├── src/
│   ├── prediction.py
│   ├── datasets.py
│   └── preprocessing.py
├── tests/
│   └── test_prediction.py
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
python -m streamlit run app.py
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
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

The merged training sources do not all record infants separately; legacy baby counts are combined with children when mapping to `no_of_children`. For manually entered or uploaded application bookings, enter the total number of children and infants in that field.

The output includes the input fields plus:

- `predicted_adr`: estimated average daily room rate.
- `cancellation_probability`: model probability between 0 and 1.
- `predicted_status`: cancellation classification at the validation-selected threshold.
- `cancellation_risk`: Low, Medium, or High, using probability cutoffs of 0.35 and 0.70.
- `projected_total_revenue`: estimated ADR multiplied by the number of stay nights. This is a gross reference estimate, not an occupancy-adjusted or profit-maximizing price.

The cancellation model uses `avg_price_per_room` as a feature. This assumes a quoted rate is available when the cancellation prediction is made; validate that assumption in the intended workflow.

## Dataset and evaluation

Training merges these three unique source files:

| Source | Rows | Arrival years | Schema |
|---|---:|---|---|
| `Hotel Reservations.csv` | 36,275 | 2017–2018 | 19 columns |
| `hotel_bookings.csv` | 5,000 | 2015–2017 | 32 columns |
| `hotel_bookings1.csv` | 119,390 | 2015–2017 | 32 columns |

The root-level `hotel_bookings.csv` is byte-for-byte identical to `data/hotel_bookings1.csv`, so it is an alias and is not counted as a fourth source. The merge maps matching booking fields to a common schema, converts month names and cancellation labels, and records source provenance. Children and babies from the legacy sources are combined in the shared child-count field because the newer source has no separate babies field. Hotel, distribution, and post-booking status fields without a safe booking-time equivalent are not used; `reservation_status` and `reservation_status_date` are excluded to avoid outcome leakage.

The three sources contain **160,665 raw rows**. Training excludes **183** records with no guests or a negative ADR, leaving **160,482 usable bookings**. The full legacy file contains **31,994 repeated exact rows**. Those rows are retained: without booking IDs, identical feature rows cannot be proven to be accidental duplicates. Source-level counts, exclusions, and SHA-256 fingerprints are recorded in `models/metrics_summary.json`. Training writes the harmonized rows and source label to `data/merged_hotel_reservations.csv` without modifying the original files.

Training adds booking-time features (seasonality, weekday, lead-time buckets, guest mix, cancellation history, and quoted-rate ratios) and maps meal, room, and market labels onto a shared vocabulary. Arrival year is kept on the booking form but is not a model input, so later years are not treated as unseen numeric values. Source families are sample-weighted so the Hotel Reservations schema is not drowned out by the larger legacy files.

The chronological split fits candidates on 2015–2016 and selects the classifier and its threshold to maximize F1 on 2017 `Hotel Reservations.csv` rows. It then scores the 2018 rows from that source as a diagnostic split; other 2017 rows are included when refitting after model selection. The metrics file records bootstrap intervals and month/market error slices. **The 2018 results were inspected during prior model-development iterations, so they are not an independent final test.** Do not present them as an untouched estimate of future performance.

The current diagnostic metrics are recorded in `models/metrics_summary.json`: cancellation accuracy 86.12%, precision 84.25%, recall 76.46%, and F1 80.17%; ADR regression MAE $13.62, RMSE $19.65, and R² 0.7035. The classifier's 2017 selection F1 was 0.5924 (precision 0.5461, recall 0.6472), demonstrating that performance changes across years. Slice analysis also identifies weak subgroups, including January 2018 (24 actual cancellations among 1,014 bookings; cancellation precision 10.58%). Interpret accuracy alongside precision, recall, F1, ROC-AUC, average precision, and the confusion matrix. Regression candidates are trained only on non-canceled bookings and selected using 2017 target-source validation R². Because the three datasets represent different hotels, time periods, and field coverage, expect meaningful distribution shift; these results do not guarantee current operational accuracy.

The current production artifacts are large (about 1.94 GB for cancellation and 0.81 GB for pricing). The recorded prediction throughput excludes model loading; allow enough disk space and memory when running the app.

After reporting the holdout results, production artifacts are refit on all usable merged rows. Their predictions are therefore not holdout estimates. Do not choose a different model based on its holdout score.

To retrain:

```powershell
python train_pipeline.py
```

Training replaces the model artifacts and metrics file. Preserve them first if rollback is needed, then restart Streamlit because models are cached for the process lifetime.

## Tests

Run focused tests from the project root:

```powershell
python -m unittest discover -s tests -v
```

## Production checklist

Before exposing this app to hotel staff or customers:

1. Validate the temporal holdout on recent, representative hotel data.
2. Confirm input availability at prediction time and review class-specific errors and probability calibration.
3. Use HTTPS and identity-aware access control; Streamlit itself does not provide application authentication.
4. Define retention and access controls for uploaded booking data.
5. Monitor data drift, cancellation outcomes, pricing error, and model failures; establish reviewed retraining and rollback.
6. Require human approval for deposits, discounts, booking acceptance, and inventory decisions. Do not trigger overbooking automatically.
