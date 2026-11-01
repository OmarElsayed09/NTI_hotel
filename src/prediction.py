from typing import Any

import numpy as np
import pandas as pd

from src.preprocessing import (
    BOOKING_INPUT_COLUMNS,
    CLASSIFICATION_FEATURES,
    REGRESSION_FEATURES,
    prepare_hotel_reservations,
)

BATCH_REQUIRED_COLUMNS = BOOKING_INPUT_COLUMNS
MAX_UPLOAD_ROWS = 10_000
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_COLUMNS = 100


def validate_booking_data(bookings: pd.DataFrame) -> pd.DataFrame:
    if len(bookings) > MAX_UPLOAD_ROWS:
        raise ValueError(f"The file may contain at most {MAX_UPLOAD_ROWS:,} bookings.")
    if len(bookings.columns) > MAX_UPLOAD_COLUMNS:
        raise ValueError(f"The file may contain at most {MAX_UPLOAD_COLUMNS} columns.")
    return prepare_hotel_reservations(bookings, require_target=False)


def predict_batch_bookings(
    bookings: pd.DataFrame,
    cls_model: Any,
    reg_model: Any,
    classification_threshold: float = 0.5,
) -> pd.DataFrame:
    if (
        not np.isfinite(classification_threshold)
        or not 0 <= classification_threshold <= 1
    ):
        raise ValueError("Classification threshold must be between 0 and 1.")

    validated = validate_booking_data(bookings)
    predicted_adr = np.asarray(
        reg_model.predict(validated[REGRESSION_FEATURES]),
        dtype=float,
    )
    if (
        predicted_adr.shape != (len(validated),)
        or not np.isfinite(predicted_adr).all()
    ):
        raise ValueError("Pricing model returned invalid predictions.")
    if (predicted_adr < 0).any():
        raise ValueError("Pricing model returned a negative room rate.")

    cancellation_probability = np.asarray(
        cls_model.predict_proba(validated[CLASSIFICATION_FEATURES])[:, 1],
        dtype=float,
    )
    if (
        cancellation_probability.shape != (len(validated),)
        or not np.isfinite(cancellation_probability).all()
        or (cancellation_probability < 0).any()
        or (cancellation_probability > 1).any()
    ):
        raise ValueError("Cancellation model returned invalid probabilities.")

    results = bookings.copy()
    results["predicted_adr"] = predicted_adr
    results["cancellation_probability"] = cancellation_probability
    results["predicted_status"] = np.where(
        cancellation_probability >= classification_threshold,
        "Canceled",
        "Not_Canceled",
    )
    results["cancellation_risk"] = np.select(
        [cancellation_probability < 0.35, cancellation_probability < 0.70],
        ["Low", "Medium"],
        default="High",
    )
    results["projected_total_revenue"] = predicted_adr * (
        validated["no_of_weekend_nights"] + validated["no_of_week_nights"]
    )
    return results


def to_safe_csv_bytes(frame: pd.DataFrame) -> bytes:
    safe_frame = frame.copy()
    formula_prefix = r"^[\t\r\n ]*[=+\-@]"
    text_columns = [
        column
        for column in safe_frame.columns
        if pd.api.types.is_object_dtype(safe_frame[column].dtype)
        or pd.api.types.is_string_dtype(safe_frame[column].dtype)
    ]
    for column in text_columns:
        values = safe_frame[column].astype("string")
        unsafe_values = values.str.match(formula_prefix, na=False)
        safe_frame.loc[unsafe_values, column] = "'" + values.loc[unsafe_values]
    return safe_frame.to_csv(index=False).encode("utf-8-sig")
