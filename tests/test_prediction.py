import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.prediction import (
    BATCH_REQUIRED_COLUMNS,
    MAX_UPLOAD_COLUMNS,
    MAX_UPLOAD_ROWS,
    predict_batch_bookings,
    to_safe_csv_bytes,
    validate_booking_data,
)
from src.datasets import (
    DATASET_FILES,
    _canonicalize_source,
    load_merged_hotel_reservations,
)
from src.preprocessing import (
    CLASSIFICATION_FEATURES,
    REGRESSION_FEATURES,
    prepare_hotel_reservations,
)
from train_pipeline import (
    best_f1_threshold,
    bootstrap_classification_intervals,
    classification_slice_metrics,
    split_by_arrival_year,
)


class FakeRegressor:
    def predict(self, bookings):
        return np.full(len(bookings), 125.0)


class NegativeRateRegressor:
    def predict(self, bookings):
        return np.full(len(bookings), -1.0)


class FakeClassifier:
    def predict_proba(self, bookings):
        self.columns_seen = set(bookings.columns)
        probabilities = np.full(len(bookings), 0.25)
        return np.column_stack((1 - probabilities, probabilities))


def valid_bookings(rows=1):
    row = {
        "no_of_adults": 2,
        "no_of_children": 0,
        "no_of_weekend_nights": 1,
        "no_of_week_nights": 2,
        "type_of_meal_plan": "Meal Plan 1",
        "required_car_parking_space": 0,
        "room_type_reserved": "Room_Type 1",
        "lead_time": 30,
        "arrival_year": 2018,
        "arrival_month": 6,
        "arrival_date": 15,
        "market_segment_type": "Online",
        "repeated_guest": 0,
        "no_of_previous_cancellations": 0,
        "no_of_previous_bookings_not_canceled": 0,
        "avg_price_per_room": 100.0,
        "no_of_special_requests": 1,
    }
    return pd.DataFrame([row.copy() for _ in range(rows)])


class BookingValidationTests(unittest.TestCase):
    def test_validates_and_predicts_batch_without_target_leakage(self):
        bookings = valid_bookings(3)
        bookings["booking_status"] = ["Not_Canceled", "Canceled", "Not_Canceled"]
        classifier = FakeClassifier()

        results = predict_batch_bookings(
            bookings,
            classifier,
            FakeRegressor(),
            classification_threshold=0.3,
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(results["predicted_adr"].tolist(), [125.0] * 3)
        self.assertEqual(results["predicted_status"].tolist(), ["Not_Canceled"] * 3)
        self.assertEqual(results["projected_total_revenue"].tolist(), [375.0] * 3)
        self.assertNotIn("booking_status", classifier.columns_seen)
        self.assertNotIn("is_canceled", classifier.columns_seen)

    def test_rejects_missing_required_columns(self):
        with self.assertRaisesRegex(ValueError, "no_of_adults"):
            validate_booking_data(valid_bookings().drop(columns=["no_of_adults"]))

    def test_rejects_negative_numeric_values(self):
        bookings = valid_bookings()
        bookings.loc[0, "lead_time"] = -1

        with self.assertRaisesRegex(ValueError, "negative"):
            validate_booking_data(bookings)

    def test_accepts_same_day_bookings(self):
        bookings = valid_bookings()
        bookings.loc[0, ["no_of_weekend_nights", "no_of_week_nights"]] = 0

        validated = validate_booking_data(bookings)

        self.assertEqual(
            validated.loc[0, "total_nights"],
            0,
        )

    def test_rejects_invalid_arrival_date(self):
        bookings = valid_bookings()
        bookings.loc[0, "arrival_date"] = 32

        with self.assertRaisesRegex(ValueError, "arrival_date"):
            validate_booking_data(bookings)

    def test_accepts_source_date_coded_as_february_29_in_2018(self):
        bookings = valid_bookings()
        bookings.loc[0, ["arrival_year", "arrival_month", "arrival_date"]] = [
            2018,
            2,
            29,
        ]

        self.assertEqual(len(validate_booking_data(bookings)), 1)

    def test_rejects_invalid_target_values(self):
        bookings = valid_bookings()
        bookings["booking_status"] = "Unknown"

        with self.assertRaisesRegex(ValueError, "booking_status"):
            prepare_hotel_reservations(bookings, require_target=True)

    def test_rejects_oversized_batches(self):
        with self.assertRaisesRegex(ValueError, "10,000"):
            validate_booking_data(valid_bookings(MAX_UPLOAD_ROWS + 1))

    def test_rejects_too_many_columns(self):
        bookings = valid_bookings()
        for index in range(MAX_UPLOAD_COLUMNS):
            bookings[f"extra_{index}"] = "value"

        with self.assertRaisesRegex(ValueError, "columns"):
            validate_booking_data(bookings)

    def test_rejects_invalid_model_output(self):
        with self.assertRaisesRegex(ValueError, "negative room rate"):
            predict_batch_bookings(
                valid_bookings(),
                FakeClassifier(),
                NegativeRateRegressor(),
            )

    def test_accepts_rows_from_new_project_dataset(self):
        dataset = pd.read_csv("data/Hotel Reservations.csv", nrows=10)
        bookings = dataset[BATCH_REQUIRED_COLUMNS]

        self.assertEqual(len(validate_booking_data(bookings)), len(bookings))

    def test_harmonizes_legacy_month_target_and_baby_counts(self):
        legacy = pd.DataFrame(
            {
                "adults": [2],
                "children": [1],
                "babies": [1],
                "stays_in_weekend_nights": [1],
                "stays_in_week_nights": [2],
                "meal": ["BB"],
                "required_car_parking_spaces": [0],
                "reserved_room_type": ["A"],
                "lead_time": [30],
                "arrival_date_year": [2017],
                "arrival_date_month": ["February"],
                "arrival_date_day_of_month": [15],
                "market_segment": ["Online TA"],
                "is_repeated_guest": [0],
                "previous_cancellations": [0],
                "previous_bookings_not_canceled": [0],
                "adr": [100.0],
                "total_of_special_requests": [1],
                "is_canceled": [1],
            }
        )

        normalized = _canonicalize_source(legacy, "hotel_bookings_sample")
        prepared = prepare_hotel_reservations(normalized, require_target=True)

        self.assertEqual(prepared.loc[0, "arrival_month"], 2)
        self.assertEqual(prepared.loc[0, "no_of_children"], 2)
        self.assertEqual(prepared.loc[0, "booking_status"], "Canceled")
        self.assertEqual(prepared.loc[0, "is_canceled"], 1)
        self.assertEqual(prepared.loc[0, "type_of_meal_plan"], "Meal Plan 1")
        self.assertEqual(prepared.loc[0, "market_segment_type"], "Online")
        self.assertEqual(prepared.loc[0, "room_type_reserved"], "Room_Type 1")
        self.assertEqual(prepared.loc[0, "lead_time_bucket"], "month")
        self.assertNotIn("arrival_year", CLASSIFICATION_FEATURES)
        self.assertNotIn("arrival_year", REGRESSION_FEATURES)
        self.assertIn("log_lead_time", CLASSIFICATION_FEATURES)

    def test_loads_all_three_unique_sources_without_counting_root_alias(self):
        merged, audit = load_merged_hotel_reservations(
            Path("data")
        )

        self.assertEqual(len(DATASET_FILES), 3)
        self.assertEqual(
            audit["files"],
            [
                "Hotel Reservations.csv",
                "hotel_bookings.csv",
                "hotel_bookings1.csv",
            ],
        )
        self.assertEqual(audit["source_rows"], 160665)
        self.assertEqual(audit["usable_rows"], len(merged))
        self.assertEqual(merged["source_dataset"].nunique(), 3)
        self.assertEqual(set(merged["arrival_year"]), {2015, 2016, 2017, 2018})
        self.assertEqual(
            audit["sources"]["hotel_bookings_full"][
                "exact_duplicate_rows_retained"
            ],
            31994,
        )

    def test_csv_export_escapes_spreadsheet_formulas(self):
        frame = pd.DataFrame(
            {"market_segment_type": ["=1+1", "Online"], "count": [2, 3]}
        )

        csv_text = to_safe_csv_bytes(frame).decode("utf-8-sig")

        self.assertIn("'=1+1", csv_text)
        self.assertIn("Online", csv_text)


class TemporalEvaluationTests(unittest.TestCase):
    def test_splits_2015_2016_train_2017_validation_and_2018_holdout(self):
        dataset, _ = load_merged_hotel_reservations(
            Path("data")
        )
        selection, validation, holdout, training_year, holdout_year = (
            split_by_arrival_year(dataset)
        )

        self.assertEqual(training_year, 2017)
        self.assertEqual(holdout_year, 2018)
        self.assertTrue(
            set(dataset.loc[selection, "arrival_year"].unique()) == {2015, 2016}
        )
        self.assertTrue((dataset.loc[validation, "arrival_year"] == 2017).all())
        self.assertTrue((dataset.loc[holdout, "arrival_year"] == 2018).all())

    def test_selects_validation_threshold_for_best_f1(self):
        targets = pd.Series([0, 0, 1, 1])
        probabilities = np.array([0.2, 0.4, 0.45, 0.8])

        threshold, f1 = best_f1_threshold(targets, probabilities)

        self.assertAlmostEqual(threshold, 0.45)
        self.assertEqual(f1, 1.0)

    def test_prefers_f1_over_accuracy_when_selecting_threshold(self):
        targets = pd.Series([0, 0, 0, 1])
        probabilities = np.array([0.2, 0.3, 0.4, 0.35])

        threshold, f1 = best_f1_threshold(targets, probabilities)

        self.assertAlmostEqual(threshold, 0.35)
        self.assertAlmostEqual(f1, 2 / 3)

    def test_rejects_invalid_probability_values(self):
        with self.assertRaisesRegex(ValueError, "valid binary scores"):
            best_f1_threshold(
                pd.Series([0, 1]),
                np.array([0.2, np.nan]),
            )

    def test_reports_classification_slices_and_bootstrap_intervals(self):
        targets = pd.Series([0, 0, 1, 1])
        probabilities = np.array([0.1, 0.6, 0.4, 0.9])

        slice_metrics = classification_slice_metrics(
            targets,
            probabilities,
            threshold=0.5,
        )
        intervals = bootstrap_classification_intervals(
            targets,
            probabilities,
            threshold=0.5,
            n_bootstrap=50,
        )

        self.assertEqual(slice_metrics["bookings"], 4)
        self.assertEqual(slice_metrics["actual_cancellations"], 2)
        self.assertEqual(slice_metrics["predicted_cancellations"], 2)
        self.assertLessEqual(intervals["Recall"][0], intervals["Recall"][1])
        self.assertGreaterEqual(intervals["Recall"][0], 0.0)
        self.assertLessEqual(intervals["Recall"][1], 1.0)


if __name__ == "__main__":
    unittest.main()
