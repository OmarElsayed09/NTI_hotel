import numpy as np
import pandas as pd

BOOKING_INPUT_COLUMNS = [
    "no_of_adults",
    "no_of_children",
    "no_of_weekend_nights",
    "no_of_week_nights",
    "type_of_meal_plan",
    "required_car_parking_space",
    "room_type_reserved",
    "lead_time",
    "arrival_year",
    "arrival_month",
    "arrival_date",
    "market_segment_type",
    "repeated_guest",
    "no_of_previous_cancellations",
    "no_of_previous_bookings_not_canceled",
    "avg_price_per_room",
    "no_of_special_requests",
]

NUMERIC_BOOKING_COLUMNS = [
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

INTEGER_BOOKING_COLUMNS = [
    column
    for column in NUMERIC_BOOKING_COLUMNS
    if column != "avg_price_per_room"
]

DERIVED_NUMERIC_FEATURES = [
    "arrival_month_sin",
    "arrival_month_cos",
    "arrival_date_sin",
    "arrival_date_cos",
    "arrival_weekday",
    "arrival_weekday_sin",
    "arrival_weekday_cos",
    "total_nights",
    "total_guests",
    "log_lead_time",
    "weekend_night_share",
    "previous_booking_count",
    "previous_cancel_rate",
    "has_previous_cancellation",
    "special_requests_per_guest",
    "parking_requested",
    "is_family",
    "is_solo",
    "is_peak_month",
]

PRICE_FEATURES = [
    "price_per_guest",
    "price_per_night",
]

# Arrival year is collected for the booking form but excluded from models so
# 2018 and later dates are not treated as an unseen numeric category.
CLASSIFICATION_FEATURES = [
    column for column in BOOKING_INPUT_COLUMNS if column != "arrival_year"
] + DERIVED_NUMERIC_FEATURES + PRICE_FEATURES + ["lead_time_bucket"]

REGRESSION_FEATURES = [
    column
    for column in BOOKING_INPUT_COLUMNS
    if column not in {"avg_price_per_room", "arrival_year"}
] + DERIVED_NUMERIC_FEATURES + ["lead_time_bucket"]

_MEAL_PLAN_MAP = {
    "bb": "Meal Plan 1",
    "breakfast": "Meal Plan 1",
    "meal plan 1": "Meal Plan 1",
    "hb": "Meal Plan 2",
    "half board": "Meal Plan 2",
    "meal plan 2": "Meal Plan 2",
    "fb": "Meal Plan 3",
    "full board": "Meal Plan 3",
    "meal plan 3": "Meal Plan 3",
    "sc": "Not Selected",
    "undefined": "Not Selected",
    "not selected": "Not Selected",
}

_MARKET_SEGMENT_MAP = {
    "online ta": "Online",
    "online": "Online",
    "offline ta/to": "Offline",
    "offline": "Offline",
    "corporate": "Corporate",
    "complementary": "Complementary",
    "aviation": "Aviation",
    "direct": "Direct",
    "groups": "Groups",
    "undefined": "Unknown",
}

_ROOM_TYPE_MAP = {
    "a": "Room_Type 1",
    "room_type 1": "Room_Type 1",
    "b": "Room_Type 2",
    "room_type 2": "Room_Type 2",
    "c": "Room_Type 3",
    "room_type 3": "Room_Type 3",
    "d": "Room_Type 4",
    "room_type 4": "Room_Type 4",
    "e": "Room_Type 5",
    "room_type 5": "Room_Type 5",
    "f": "Room_Type 6",
    "room_type 6": "Room_Type 6",
    "g": "Room_Type 7",
    "room_type 7": "Room_Type 7",
}


def prepare_hotel_reservations(
    bookings: pd.DataFrame,
    require_target: bool = False,
) -> pd.DataFrame:
    if bookings.empty:
        raise ValueError("The reservations CSV contains no rows.")

    prepared = bookings.copy()
    prepared.columns = prepared.columns.map(str).str.strip()
    if prepared.columns.duplicated().any():
        raise ValueError("The reservations CSV contains duplicate column names.")

    required = set(BOOKING_INPUT_COLUMNS)
    if require_target:
        required.add("booking_status")
    missing = sorted(required - set(prepared.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    for column in NUMERIC_BOOKING_COLUMNS:
        original = prepared[column]
        converted = pd.to_numeric(original, errors="coerce")
        malformed = original.notna() & converted.isna()
        if malformed.any() or converted.isna().any():
            raise ValueError(f"Column '{column}' must contain numeric values.")
        if not np.isfinite(converted).all():
            raise ValueError(f"Column '{column}' must contain finite values.")
        if (converted < 0).any():
            raise ValueError(f"Column '{column}' cannot contain negative values.")
        if column in INTEGER_BOOKING_COLUMNS and (converted % 1 != 0).any():
            raise ValueError(f"Column '{column}' must contain whole numbers.")
        prepared[column] = converted

    if not prepared["repeated_guest"].isin([0, 1]).all():
        raise ValueError("Column 'repeated_guest' must contain only 0 or 1.")
    if (prepared["no_of_adults"] + prepared["no_of_children"] <= 0).any():
        raise ValueError("Each reservation must include at least one guest.")
    if not prepared["arrival_month"].between(1, 12).all():
        raise ValueError("Column 'arrival_month' must be between 1 and 12.")
    if not prepared["arrival_date"].between(1, 31).all():
        raise ValueError("Column 'arrival_date' must be between 1 and 31.")

    for column in ("type_of_meal_plan", "room_type_reserved", "market_segment_type"):
        values = prepared[column].astype("string").str.strip()
        if values.isna().any() or values.eq("").any():
            raise ValueError(f"Column '{column}' cannot contain empty values.")
        prepared[column] = values

    prepared["type_of_meal_plan"] = (
        prepared["type_of_meal_plan"]
        .str.casefold()
        .map(_MEAL_PLAN_MAP)
        .fillna(prepared["type_of_meal_plan"])
    )
    prepared["market_segment_type"] = (
        prepared["market_segment_type"]
        .str.casefold()
        .map(_MARKET_SEGMENT_MAP)
        .fillna("Unknown")
    )
    room_keys = prepared["room_type_reserved"].str.casefold().str.replace(
        r"\s+",
        " ",
        regex=True,
    )
    prepared["room_type_reserved"] = room_keys.map(_ROOM_TYPE_MAP).fillna("Other")

    if require_target:
        statuses = prepared["booking_status"].astype("string").str.strip()
        if not statuses.isin(["Canceled", "Not_Canceled"]).all():
            raise ValueError(
                "Column 'booking_status' must contain only Canceled or Not_Canceled."
            )
        prepared["booking_status"] = statuses
        prepared["is_canceled"] = statuses.eq("Canceled").astype("int8")

    prepared["arrival_month_sin"] = np.sin(
        2 * np.pi * prepared["arrival_month"] / 12
    )
    prepared["arrival_month_cos"] = np.cos(
        2 * np.pi * prepared["arrival_month"] / 12
    )
    prepared["arrival_date_sin"] = np.sin(
        2 * np.pi * prepared["arrival_date"] / 31
    )
    prepared["arrival_date_cos"] = np.cos(
        2 * np.pi * prepared["arrival_date"] / 31
    )
    arrival_stamp = pd.to_datetime(
        {
            "year": prepared["arrival_year"],
            "month": prepared["arrival_month"],
            "day": prepared["arrival_date"],
        },
        errors="coerce",
    )
    weekday = arrival_stamp.dt.weekday.fillna(3).astype("int16")
    prepared["arrival_weekday"] = weekday
    prepared["arrival_weekday_sin"] = np.sin(2 * np.pi * weekday / 7)
    prepared["arrival_weekday_cos"] = np.cos(2 * np.pi * weekday / 7)
    nights = prepared["no_of_weekend_nights"] + prepared["no_of_week_nights"]
    guests = prepared["no_of_adults"] + prepared["no_of_children"]
    previous_bookings = (
        prepared["no_of_previous_cancellations"]
        + prepared["no_of_previous_bookings_not_canceled"]
    )
    prepared["total_nights"] = nights
    prepared["total_guests"] = guests
    prepared["log_lead_time"] = np.log1p(prepared["lead_time"])
    prepared["weekend_night_share"] = np.where(
        nights > 0,
        prepared["no_of_weekend_nights"] / nights,
        0.0,
    )
    prepared["previous_booking_count"] = previous_bookings
    prepared["previous_cancel_rate"] = np.where(
        previous_bookings > 0,
        prepared["no_of_previous_cancellations"] / previous_bookings,
        0.0,
    )
    prepared["has_previous_cancellation"] = (
        prepared["no_of_previous_cancellations"] > 0
    ).astype("int8")
    prepared["special_requests_per_guest"] = prepared[
        "no_of_special_requests"
    ] / guests.clip(lower=1)
    prepared["parking_requested"] = (
        prepared["required_car_parking_space"] > 0
    ).astype("int8")
    prepared["is_family"] = (prepared["no_of_children"] > 0).astype("int8")
    prepared["is_solo"] = (guests == 1).astype("int8")
    prepared["is_peak_month"] = prepared["arrival_month"].isin(
        [4, 5, 6, 7, 8, 9, 12]
    ).astype("int8")
    prepared["price_per_guest"] = prepared["avg_price_per_room"] / guests.clip(
        lower=1
    )
    prepared["price_per_night"] = np.where(
        nights > 0,
        prepared["avg_price_per_room"] / nights,
        prepared["avg_price_per_room"],
    )
    prepared["lead_time_bucket"] = pd.cut(
        prepared["lead_time"],
        bins=[-0.1, 0, 7, 30, 90, 180, 10_000],
        labels=["same_day", "week", "month", "quarter", "half_year", "long"],
    ).astype("string")
    return prepared
