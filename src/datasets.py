import hashlib
import calendar
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.preprocessing import BOOKING_INPUT_COLUMNS, prepare_hotel_reservations

DATASET_FILES = {
    "hotel_reservations": "Hotel Reservations.csv",
    "hotel_bookings_sample": "hotel_bookings.csv",
    "hotel_bookings_full": "hotel_bookings1.csv",
}

_LEGACY_COLUMN_MAP = {
    "adults": "no_of_adults",
    "stays_in_weekend_nights": "no_of_weekend_nights",
    "stays_in_week_nights": "no_of_week_nights",
    "meal": "type_of_meal_plan",
    "required_car_parking_spaces": "required_car_parking_space",
    "reserved_room_type": "room_type_reserved",
    "arrival_date_year": "arrival_year",
    "arrival_date_day_of_month": "arrival_date",
    "market_segment": "market_segment_type",
    "is_repeated_guest": "repeated_guest",
    "previous_cancellations": "no_of_previous_cancellations",
    "previous_bookings_not_canceled": "no_of_previous_bookings_not_canceled",
    "adr": "avg_price_per_room",
    "total_of_special_requests": "no_of_special_requests",
}

_MONTH_NUMBERS = {
    month.lower(): index
    for index, month in enumerate(calendar.month_name)
    if month
}
_MONTH_NUMBERS.update(
    {
        month.lower(): index
        for index, month in enumerate(calendar.month_abbr)
        if month
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonicalize_source(
    raw: pd.DataFrame,
    source_name: str,
) -> pd.DataFrame:
    if source_name == "hotel_reservations":
        canonical = raw.copy()
        if "booking_status" not in canonical.columns:
            raise ValueError(
                "Hotel Reservations.csv must include its booking_status target."
            )
        return canonical

    required = {
        "adults",
        "children",
        "babies",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "meal",
        "required_car_parking_spaces",
        "reserved_room_type",
        "lead_time",
        "arrival_date_year",
        "arrival_date_month",
        "arrival_date_day_of_month",
        "market_segment",
        "is_repeated_guest",
        "previous_cancellations",
        "previous_bookings_not_canceled",
        "adr",
        "total_of_special_requests",
        "is_canceled",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(
            f"Legacy hotel-bookings data is missing columns: {', '.join(missing)}"
        )

    canonical = raw.rename(columns=_LEGACY_COLUMN_MAP).copy()
    month_names = (
        canonical["arrival_date_month"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    month_numbers = pd.to_numeric(month_names, errors="coerce")
    named_months = month_names.map(_MONTH_NUMBERS)
    canonical["arrival_month"] = month_numbers.fillna(named_months)
    canonical["no_of_children"] = (
        pd.to_numeric(canonical["children"], errors="coerce").fillna(0)
        + pd.to_numeric(canonical["babies"], errors="coerce").fillna(0)
    )
    canonical["booking_status"] = pd.to_numeric(
        canonical["is_canceled"],
        errors="coerce",
    ).map({0: "Not_Canceled", 1: "Canceled"})
    canonical["source_dataset"] = source_name
    return canonical


def load_merged_hotel_reservations(
    data_dir: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames = []
    source_audit: dict[str, Any] = {}

    for source_name, filename in DATASET_FILES.items():
        path = data_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required booking dataset not found: {path}")

        raw = pd.read_csv(path)
        canonical = _canonicalize_source(raw, source_name)
        if source_name == "hotel_reservations":
            canonical["source_dataset"] = source_name

        for column in (
            "type_of_meal_plan",
            "room_type_reserved",
            "market_segment_type",
        ):
            if column not in canonical.columns:
                raise ValueError(
                    f"{filename} could not be mapped to required column '{column}'."
                )
            values = canonical[column].astype("string").str.strip()
            canonical[column] = values.fillna("Unknown").replace("", "Unknown")

        if "booking_status" not in canonical.columns:
            raise ValueError(f"{filename} could not be mapped to booking_status.")

        numeric_columns = [
            "no_of_adults",
            "no_of_children",
            "no_of_weekend_nights",
            "no_of_week_nights",
            "required_car_parking_space",
            "lead_time",
            "arrival_year",
            "arrival_month",
            "arrival_date",
            "repeated_guest",
            "no_of_previous_cancellations",
            "no_of_previous_bookings_not_canceled",
            "avg_price_per_room",
            "no_of_special_requests",
        ]
        for column in numeric_columns:
            if column not in canonical.columns:
                raise ValueError(
                    f"{filename} could not be mapped to required column '{column}'."
                )
            original = canonical[column]
            converted = pd.to_numeric(original, errors="coerce")
            malformed = original.notna() & converted.isna()
            if malformed.any():
                raise ValueError(
                    f"{filename} contains non-numeric values in '{column}'."
                )
            canonical[column] = converted

        status = canonical["booking_status"].astype("string").str.strip()
        valid_status = status.isin(["Canceled", "Not_Canceled"])
        if status.isna().any() or not valid_status.all():
            bad_values = sorted(status.loc[~valid_status].dropna().unique().tolist())
            raise ValueError(
                f"{filename} contains unsupported booking_status values: {bad_values}"
            )
        canonical["booking_status"] = status
        canonical = canonical.loc[
            :,
            BOOKING_INPUT_COLUMNS + ["booking_status", "source_dataset"],
        ]

        invalid_guests = (
            canonical["no_of_adults"].fillna(0)
            + canonical["no_of_children"].fillna(0)
        ) <= 0
        negative_adr = canonical["avg_price_per_room"] < 0
        finite_numeric = pd.Series(True, index=canonical.index)
        for column in numeric_columns:
            finite_numeric &= canonical[column].notna() & np.isfinite(
                canonical[column]
            )
        invalid_rows = invalid_guests | negative_adr | ~finite_numeric
        valid = canonical.loc[~invalid_rows].copy()
        prepared = prepare_hotel_reservations(valid, require_target=True)
        prepared["source_dataset"] = source_name
        frames.append(prepared)

        year_counts = (
            prepared.groupby("arrival_year")
            .agg(
                bookings=("is_canceled", "size"),
                cancellations=("is_canceled", "sum"),
            )
            .reset_index()
        )
        source_audit[source_name] = {
            "file": filename,
            "sha256": _sha256(path),
            "source_rows": int(len(raw)),
            "usable_rows": int(len(prepared)),
            "exact_duplicate_rows_retained": int(raw.duplicated().sum()),
            "rows_excluded_invalid_guest_count": int(invalid_guests.sum()),
            "rows_excluded_negative_adr": int(negative_adr.sum()),
            "rows_excluded_non_finite_or_missing_numeric": int(
                (~finite_numeric).sum()
            ),
            "cancellation_rate": round(float(prepared["is_canceled"].mean()), 4),
            "year_summary": [
                {
                    "arrival_year": int(row.arrival_year),
                    "bookings": int(row.bookings),
                    "cancellations": int(row.cancellations),
                }
                for row in year_counts.itertuples(index=False)
            ],
        }

    merged = pd.concat(frames, ignore_index=True, sort=False)
    audit = {
        "files": [details["file"] for details in source_audit.values()],
        "source_rows": int(sum(item["source_rows"] for item in source_audit.values())),
        "usable_rows": int(len(merged)),
        "exact_duplicate_rows_retained": int(
            sum(item["exact_duplicate_rows_retained"] for item in source_audit.values())
        ),
        "sources": source_audit,
    }
    return merged, audit
