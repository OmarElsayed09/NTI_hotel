import json
import os
import tempfile
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.preprocessing import (
    CLASSIFICATION_FEATURES,
    REGRESSION_FEATURES,
)
from src.datasets import DATASET_FILES, load_merged_hotel_reservations

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MERGED_DATA_PATH = DATA_DIR / "merged_hotel_reservations.csv"
MODEL_DIR = BASE_DIR / "models"
RANDOM_STATE = 42


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [
        column
        for column in X.columns
        if pd.api.types.is_object_dtype(X[column].dtype)
        or pd.api.types.is_string_dtype(X[column].dtype)
    ]
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                num_cols,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "ohe",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                sparse_output=False,
                            ),
                        ),
                    ]
                ),
                cat_cols,
            ),
        ]
    )


def best_f1_threshold(
    targets: pd.Series,
    probabilities: np.ndarray,
) -> tuple[float, float]:
    target_values = targets.to_numpy(dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    if (
        target_values.size == 0
        or scores.shape != target_values.shape
        or not np.isfinite(scores).all()
        or (scores < 0).any()
        or (scores > 1).any()
        or not np.isin(target_values, [0, 1]).all()
    ):
        raise ValueError("Targets and probabilities must be valid binary scores.")

    order = np.argsort(scores, kind="stable")
    sorted_scores = scores[order]
    sorted_targets = target_values[order]
    thresholds, first_indices = np.unique(sorted_scores, return_index=True)
    positive_prefix = np.concatenate(([0], np.cumsum(sorted_targets)))
    positives_below = positive_prefix[first_indices]
    total_positives = int(target_values.sum())
    true_positives = total_positives - positives_below
    predicted_positives = target_values.size - first_indices
    f1_by_threshold = np.divide(
        2 * true_positives,
        predicted_positives + total_positives,
        out=np.zeros_like(true_positives, dtype=float),
        where=(predicted_positives + total_positives) > 0,
    )
    thresholds = np.append(thresholds, np.nextafter(sorted_scores[-1], np.inf))
    f1_by_threshold = np.append(f1_by_threshold, 0.0)
    best_f1 = float(f1_by_threshold.max())
    best_indices = np.flatnonzero(f1_by_threshold == best_f1)
    best_index = min(
        best_indices,
        key=lambda index: abs(thresholds[index] - 0.5),
    )
    return float(thresholds[best_index]), best_f1


def classification_slice_metrics(
    targets: pd.Series,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, float | int]:
    actual = targets.to_numpy(dtype=int)
    predicted = probabilities >= threshold
    return {
        "bookings": int(actual.size),
        "actual_cancellations": int(actual.sum()),
        "predicted_cancellations": int(predicted.sum()),
        "accuracy": round(float(accuracy_score(actual, predicted)), 4),
        "precision": round(float(precision_score(actual, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(actual, predicted, zero_division=0)), 4),
        "f1": round(float(f1_score(actual, predicted, zero_division=0)), 4),
    }


def bootstrap_classification_intervals(
    targets: pd.Series,
    probabilities: np.ndarray,
    threshold: float,
    n_bootstrap: int = 1000,
) -> dict[str, list[float]]:
    actual = targets.to_numpy(dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    negatives = np.flatnonzero(actual == 0)
    positives = np.flatnonzero(actual == 1)
    if negatives.size == 0 or positives.size == 0:
        raise ValueError("Bootstrap intervals require both target classes.")
    if scores.shape != actual.shape or not np.isfinite(scores).all():
        raise ValueError("Bootstrap probabilities must match the targets.")

    rng = np.random.default_rng(RANDOM_STATE)
    samples: dict[str, list[float]] = {
        "Accuracy": [],
        "Precision": [],
        "Recall": [],
        "F1_Score": [],
        "ROC_AUC": [],
        "Average_Precision": [],
        "Brier_Score": [],
    }
    for _ in range(n_bootstrap):
        indices = np.concatenate(
            [
                rng.choice(negatives, size=negatives.size, replace=True),
                rng.choice(positives, size=positives.size, replace=True),
            ]
        )
        sample_actual = actual[indices]
        sample_scores = scores[indices]
        sample_predicted = sample_scores >= threshold
        samples["Accuracy"].append(
            accuracy_score(sample_actual, sample_predicted)
        )
        samples["Precision"].append(
            precision_score(sample_actual, sample_predicted, zero_division=0)
        )
        samples["Recall"].append(
            recall_score(sample_actual, sample_predicted, zero_division=0)
        )
        samples["F1_Score"].append(
            f1_score(sample_actual, sample_predicted, zero_division=0)
        )
        samples["ROC_AUC"].append(roc_auc_score(sample_actual, sample_scores))
        samples["Average_Precision"].append(
            average_precision_score(sample_actual, sample_scores)
        )
        samples["Brier_Score"].append(
            brier_score_loss(sample_actual, sample_scores)
        )
    return {
        metric: [
            round(float(np.quantile(values, 0.025)), 4),
            round(float(np.quantile(values, 0.975)), 4),
        ]
        for metric, values in samples.items()
    }


def split_by_arrival_year(
    bookings: pd.DataFrame,
) -> tuple[pd.Index, pd.Index, pd.Index, int, int]:
    years = sorted(bookings["arrival_year"].unique())
    if len(years) < 3:
        raise ValueError(
            "The merged reservations dataset must contain at least three arrival "
            "years for chronological training, validation, and holdout sets."
        )
    selection_years = years[:-2]
    validation_year, holdout_year = int(years[-2]), int(years[-1])
    selection_indices = bookings.index[
        bookings["arrival_year"].isin(selection_years)
    ]
    validation_indices = bookings.index[
        bookings["arrival_year"] == validation_year
    ]
    holdout_indices = bookings.index[bookings["arrival_year"] == holdout_year]
    if (
        len(selection_indices) < 20
        or len(validation_indices) < 2
        or len(holdout_indices) < 2
    ):
        raise ValueError(
            "The chronological training, validation, and holdout splits "
            "must each contain enough rows."
        )
    return (
        pd.Index(selection_indices),
        pd.Index(validation_indices),
        pd.Index(holdout_indices),
        validation_year,
        holdout_year,
    )


def source_balanced_weights(source_labels: pd.Series) -> np.ndarray:
    family = source_labels.replace(
        {
            "hotel_bookings_sample": "legacy",
            "hotel_bookings_full": "legacy",
            "hotel_reservations": "reservations",
        }
    )
    counts = family.value_counts()
    if counts.empty or (counts <= 0).any():
        raise ValueError("Sample weights require at least one labeled source.")
    per_family_weight = len(source_labels) / (counts.size * counts)
    return family.map(per_family_weight).to_numpy(dtype=float)


def _fit_pipeline(
    pipeline: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
    sample_weight: np.ndarray | None = None,
) -> Pipeline:
    if sample_weight is None:
        pipeline.fit(features, target)
        return pipeline
    pipeline.fit(
        features,
        target,
        model__sample_weight=sample_weight,
    )
    return pipeline


def _classification_models() -> dict[str, object]:
    return {
        "Logistic Regression (Baseline)": LogisticRegression(
            max_iter=2000,
            C=1.5,
            solver="lbfgs",
            random_state=RANDOM_STATE,
        ),
        "Random Forest Classifier": RandomForestClassifier(
            n_estimators=350,
            max_depth=18,
            min_samples_leaf=2,
            max_features="sqrt",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Deep Random Forest Classifier": RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Balanced Random Forest Classifier": RandomForestClassifier(
            n_estimators=350,
            max_depth=18,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Deep Balanced Random Forest Classifier": RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            max_features=0.7,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Extra Trees Classifier": ExtraTreesClassifier(
            n_estimators=400,
            max_depth=18,
            min_samples_leaf=2,
            max_features="sqrt",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Deep Extra Trees Classifier": ExtraTreesClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Balanced Extra Trees Classifier": ExtraTreesClassifier(
            n_estimators=400,
            max_depth=18,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Hist Gradient Boosting Classifier": HistGradientBoostingClassifier(
            max_iter=450,
            max_leaf_nodes=63,
            min_samples_leaf=20,
            l2_regularization=0.15,
            learning_rate=0.06,
            max_depth=None,
            early_stopping=False,
            random_state=RANDOM_STATE,
        ),
        "Regularized Hist Gradient Boosting Classifier": (
            HistGradientBoostingClassifier(
                max_iter=600,
                max_leaf_nodes=31,
                min_samples_leaf=30,
                l2_regularization=0.3,
                learning_rate=0.05,
                early_stopping=False,
                random_state=RANDOM_STATE,
            )
        ),
    }


def _regression_models() -> dict[str, object]:
    return {
        "Ridge Regression (Baseline)": Ridge(alpha=1.0),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=250,
            max_depth=14,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Extra Trees Regressor": ExtraTreesRegressor(
            n_estimators=350,
            max_depth=18,
            min_samples_leaf=2,
            max_features=1.0,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Deep Extra Trees Regressor": ExtraTreesRegressor(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            max_features=0.8,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Random Forest Regressor (Tuned)": RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            min_samples_leaf=3,
            max_features=0.8,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Hist Gradient Boosting Regressor": HistGradientBoostingRegressor(
            max_iter=400,
            max_leaf_nodes=63,
            min_samples_leaf=20,
            l2_regularization=0.1,
            learning_rate=0.06,
            early_stopping=False,
            random_state=RANDOM_STATE,
        ),
        "Regularized Hist Gradient Boosting Regressor": (
            HistGradientBoostingRegressor(
                max_iter=600,
                max_leaf_nodes=31,
                min_samples_leaf=30,
                l2_regularization=0.3,
                learning_rate=0.05,
                early_stopping=False,
                random_state=RANDOM_STATE,
            )
        ),
    }


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    prepared, source_audit = load_merged_hotel_reservations(DATA_DIR)
    print(
        f"[1/4] Loaded and harmonized {len(DATASET_FILES)} source datasets: "
        f"{source_audit['source_rows']:,} source rows -> "
        f"{len(prepared):,} usable rows"
    )
    for details in source_audit["sources"].values():
        print(
            f"  {details['file']}: {details['source_rows']:,} rows, "
            f"{details['usable_rows']:,} usable, "
            f"{details['exact_duplicate_rows_retained']:,} exact duplicate "
            "rows retained"
        )

    (
        selection_indices,
        validation_indices,
        holdout_indices,
        validation_year,
        holdout_year,
    ) = split_by_arrival_year(prepared)
    training_indices = selection_indices.append(validation_indices)
    X_cls = prepared[CLASSIFICATION_FEATURES]
    y_cls = prepared["is_canceled"]
    y_selection = y_cls.loc[selection_indices]
    target_validation_indices = validation_indices[
        prepared.loc[validation_indices, "source_dataset"].eq("hotel_reservations")
    ]
    if len(target_validation_indices) < 2:
        raise ValueError(
            "The 2017 validation split must contain target-source bookings."
        )
    print(
        f"Temporal evaluation: fit on {sorted(prepared.loc[selection_indices, 'arrival_year'].unique())}; "
        f"select on {len(target_validation_indices):,} {validation_year} "
        f"Hotel Reservations rows; refit through {validation_year}; "
        f"evaluate on {holdout_year} diagnostic split ({len(holdout_indices):,} rows)"
    )
    y_validation = y_cls.loc[target_validation_indices]
    y_training = y_cls.loc[training_indices]
    y_holdout = y_cls.loc[holdout_indices]
    if any(part.nunique() != 2 for part in (y_selection, y_validation, y_holdout)):
        raise ValueError("Each classification split must contain both booking outcomes.")

    cls_models = _classification_models()
    cls_validation_accuracy: dict[str, float] = {}
    cls_validation_precision: dict[str, float] = {}
    cls_validation_recall: dict[str, float] = {}
    cls_validation_f1: dict[str, float] = {}
    cls_validation_threshold: dict[str, float] = {}
    cls_validation_auc: dict[str, float] = {}
    cls_validation_average_precision: dict[str, float] = {}
    selection_weights = source_balanced_weights(
        prepared.loc[selection_indices, "source_dataset"]
    )
    training_weights = source_balanced_weights(
        prepared.loc[training_indices, "source_dataset"]
    )
    production_weights = source_balanced_weights(prepared["source_dataset"])
    for name, model in cls_models.items():
        pipe = Pipeline(
            [
                ("preprocessor", build_preprocessor(X_cls.loc[selection_indices])),
                ("model", model),
            ]
        )
        _fit_pipeline(
            pipe,
            X_cls.loc[selection_indices],
            y_selection,
            selection_weights,
        )
        validation_probability = pipe.predict_proba(
            X_cls.loc[target_validation_indices]
        )[:, 1]
        cls_validation_threshold[name], cls_validation_f1[name] = best_f1_threshold(
            y_validation,
            validation_probability,
        )
        validation_prediction = (
            validation_probability >= cls_validation_threshold[name]
        )
        cls_validation_accuracy[name] = accuracy_score(
            y_validation,
            validation_prediction,
        )
        cls_validation_precision[name] = precision_score(
            y_validation,
            validation_prediction,
        )
        cls_validation_recall[name] = recall_score(
            y_validation,
            validation_prediction,
        )
        cls_validation_auc[name] = roc_auc_score(
            y_validation,
            validation_probability,
        )
        cls_validation_average_precision[name] = average_precision_score(
            y_validation,
            validation_probability,
        )

    best_cls_name = max(
        cls_validation_f1,
        key=cls_validation_f1.get,
    )
    classification_results = []
    holdout_probabilities: dict[str, np.ndarray] = {}
    for name, model in cls_models.items():
        pipe = Pipeline(
            [
                ("preprocessor", build_preprocessor(X_cls.loc[training_indices])),
                ("model", model),
            ]
        )
        _fit_pipeline(
            pipe,
            X_cls.loc[training_indices],
            y_training,
            training_weights,
        )
        holdout_probability = pipe.predict_proba(X_cls.loc[holdout_indices])[:, 1]
        holdout_probabilities[name] = holdout_probability
        holdout_prediction = holdout_probability >= cls_validation_threshold[name]
        classification_results.append(
            {
                "Model": name,
                "Validation_Accuracy": round(cls_validation_accuracy[name], 4),
                "Validation_Precision": round(cls_validation_precision[name], 4),
                "Validation_Recall": round(cls_validation_recall[name], 4),
                "Validation_F1_Score": round(cls_validation_f1[name], 4),
                "Classification_Threshold": round(
                    cls_validation_threshold[name],
                    4,
                ),
                "Validation_ROC_AUC": round(cls_validation_auc[name], 4),
                "Validation_Average_Precision": round(
                    cls_validation_average_precision[name],
                    4,
                ),
                "Accuracy": round(
                    accuracy_score(y_holdout, holdout_prediction),
                    4,
                ),
                "Precision": round(
                    precision_score(y_holdout, holdout_prediction),
                    4,
                ),
                "Recall": round(
                    recall_score(y_holdout, holdout_prediction),
                    4,
                ),
                "F1_Score": round(f1_score(y_holdout, holdout_prediction), 4),
                "ROC_AUC": round(
                    roc_auc_score(y_holdout, holdout_probability),
                    4,
                ),
                "Average_Precision": round(
                    average_precision_score(y_holdout, holdout_probability),
                    4,
                ),
                "Confusion_Matrix": [
                    [
                        int(((y_holdout == 0) & (holdout_prediction == 0)).sum()),
                        int(((y_holdout == 0) & (holdout_prediction == 1)).sum()),
                    ],
                    [
                        int(((y_holdout == 1) & (holdout_prediction == 0)).sum()),
                        int(((y_holdout == 1) & (holdout_prediction == 1)).sum()),
                    ],
                ],
            }
        )
    classification_frame = pd.DataFrame(classification_results).sort_values(
        by="Validation_F1_Score",
        ascending=False,
    )
    print("\n[2/4] Cancellation model comparison:")
    print(classification_frame.to_string(index=False))

    production_cls = Pipeline(
        [
            ("preprocessor", build_preprocessor(X_cls)),
            ("model", cls_models[best_cls_name]),
        ]
    )
    _fit_pipeline(production_cls, X_cls, y_cls, production_weights)

    regression_data = prepared.loc[prepared["is_canceled"] == 0]
    X_reg = regression_data[REGRESSION_FEATURES]
    y_reg = regression_data["avg_price_per_room"]
    reg_selection_indices = selection_indices.intersection(regression_data.index)
    reg_validation_indices = target_validation_indices.intersection(
        regression_data.index
    )
    reg_training_indices = training_indices.intersection(regression_data.index)
    reg_holdout_indices = holdout_indices.intersection(regression_data.index)
    if (
        len(reg_selection_indices) < 2
        or len(reg_validation_indices) < 2
        or len(reg_holdout_indices) < 2
    ):
        raise ValueError("ADR regression requires at least two rows in each temporal split.")

    reg_models = _regression_models()
    reg_validation_r2: dict[str, float] = {}
    reg_selection_weights = source_balanced_weights(
        regression_data.loc[reg_selection_indices, "source_dataset"]
    )
    reg_training_weights = source_balanced_weights(
        regression_data.loc[reg_training_indices, "source_dataset"]
    )
    reg_production_weights = source_balanced_weights(
        regression_data["source_dataset"]
    )
    for name, model in reg_models.items():
        pipe = Pipeline(
            [
                ("preprocessor", build_preprocessor(X_reg.loc[reg_selection_indices])),
                ("model", model),
            ]
        )
        _fit_pipeline(
            pipe,
            X_reg.loc[reg_selection_indices],
            y_reg.loc[reg_selection_indices],
            reg_selection_weights,
        )
        validation_prediction = pipe.predict(X_reg.loc[reg_validation_indices])
        reg_validation_r2[name] = r2_score(
            y_reg.loc[reg_validation_indices],
            validation_prediction,
        )
    best_reg_name = max(reg_validation_r2, key=reg_validation_r2.get)

    regression_results = []
    regression_holdout_predictions: dict[str, np.ndarray] = {}
    for name, model in reg_models.items():
        pipe = Pipeline(
            [
                ("preprocessor", build_preprocessor(X_reg.loc[reg_training_indices])),
                ("model", model),
            ]
        )
        _fit_pipeline(
            pipe,
            X_reg.loc[reg_training_indices],
            y_reg.loc[reg_training_indices],
            reg_training_weights,
        )
        holdout_prediction = pipe.predict(X_reg.loc[reg_holdout_indices])
        regression_holdout_predictions[name] = holdout_prediction
        regression_results.append(
            {
                "Model": name,
                "Validation_R2_Score": round(reg_validation_r2[name], 4),
                "RMSE ($)": round(
                    float(
                        np.sqrt(
                            mean_squared_error(
                                y_reg.loc[reg_holdout_indices],
                                holdout_prediction,
                            )
                        )
                    ),
                    2,
                ),
                "MAE ($)": round(
                    mean_absolute_error(
                        y_reg.loc[reg_holdout_indices],
                        holdout_prediction,
                    ),
                    2,
                ),
                "R2_Score": round(
                    r2_score(
                        y_reg.loc[reg_holdout_indices],
                        holdout_prediction,
                    ),
                    4,
                ),
            }
        )
    regression_frame = pd.DataFrame(regression_results).sort_values(
        by="Validation_R2_Score",
        ascending=False,
    )
    print("\n[3/4] ADR regression comparison:")
    print(regression_frame.to_string(index=False))

    production_reg = Pipeline(
        [
            ("preprocessor", build_preprocessor(X_reg)),
            ("model", reg_models[best_reg_name]),
        ]
    )
    _fit_pipeline(production_reg, X_reg, y_reg, reg_production_weights)

    inference_features = X_cls.loc[holdout_indices].head(1000)
    inference_regression_features = X_reg.loc[reg_holdout_indices].head(1000)
    production_cls.predict_proba(inference_features.head(10))
    production_reg.predict(inference_regression_features.head(10))
    inference_started = time.perf_counter()
    production_cls.predict_proba(inference_features)
    production_reg.predict(inference_regression_features)
    inference_seconds = time.perf_counter() - inference_started

    year_summary = (
        prepared.groupby("arrival_year")
        .agg(
            bookings=("is_canceled", "size"),
            cancellation_rate=("is_canceled", "mean"),
        )
        .reset_index()
    )
    selected_holdout_probabilities = holdout_probabilities[best_cls_name]
    selected_holdout_frame = prepared.loc[holdout_indices]
    classification_slices = {}
    for column in ("arrival_month", "market_segment_type"):
        classification_slices[column] = {}
        for value, group in selected_holdout_frame.groupby(column, dropna=False):
            group_positions = selected_holdout_frame.index.get_indexer(group.index)
            classification_slices[column][str(value)] = (
                classification_slice_metrics(
                    group["is_canceled"],
                    selected_holdout_probabilities[group_positions],
                    cls_validation_threshold[best_cls_name],
                )
            )

    selected_regression_actual = y_reg.loc[reg_holdout_indices].to_numpy(dtype=float)
    selected_regression_prediction = regression_holdout_predictions[best_reg_name]
    regression_bootstrap_rng = np.random.default_rng(RANDOM_STATE)
    mae_bootstrap = []
    r2_bootstrap = []
    for _ in range(1000):
        sample_indices = regression_bootstrap_rng.integers(
            0,
            selected_regression_actual.size,
            size=selected_regression_actual.size,
        )
        sample_actual = selected_regression_actual[sample_indices]
        sample_prediction = selected_regression_prediction[sample_indices]
        mae_bootstrap.append(
            mean_absolute_error(sample_actual, sample_prediction)
        )
        r2_bootstrap.append(r2_score(sample_actual, sample_prediction))

    metrics = {
        "dataset": {
            "files": source_audit["files"],
            "sources": source_audit["sources"],
            "source_rows": source_audit["source_rows"],
            "usable_rows": int(len(prepared)),
            "columns": int(len(prepared.columns)),
            "exact_duplicate_rows_retained": source_audit[
                "exact_duplicate_rows_retained"
            ],
            "year_summary": [
                {
                    "arrival_year": int(row.arrival_year),
                    "bookings": int(row.bookings),
                    "cancellation_rate": round(float(row.cancellation_rate), 4),
                }
                for row in year_summary.itertuples(index=False)
            ],
            "cancellation_rate": round(float(prepared["is_canceled"].mean()), 4),
            "average_adr": round(
                float(
                    prepared.loc[
                        prepared["is_canceled"] == 0,
                        "avg_price_per_room",
                    ].mean()
                ),
                2,
            ),
        },
        "classification": classification_frame.to_dict(orient="records"),
        "classification_uncertainty_95_ci": bootstrap_classification_intervals(
            y_holdout,
            selected_holdout_probabilities,
            cls_validation_threshold[best_cls_name],
        ),
        "classification_slices": classification_slices,
        "classification_baseline": {
            "strategy": "majority_class",
            "accuracy": round(
                float(
                    max(
                        (y_holdout == 0).mean(),
                        (y_holdout == 1).mean(),
                    )
                ),
                4,
            ),
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        },
        "regression": regression_frame.to_dict(orient="records"),
        "regression_uncertainty_95_ci": {
            "MAE ($)": [
                round(float(np.quantile(mae_bootstrap, 0.025)), 2),
                round(float(np.quantile(mae_bootstrap, 0.975)), 2),
            ],
            "R2_Score": [
                round(float(np.quantile(r2_bootstrap, 0.025)), 4),
                round(float(np.quantile(r2_bootstrap, 0.975)), 4),
            ],
        },
        "operational": {
            "inference_rows": int(len(inference_features)),
            "inference_seconds": round(inference_seconds, 4),
            "inference_rows_per_second": round(
                len(inference_features) / inference_seconds,
                1,
            ),
        },
        "best_cls_model": best_cls_name,
        "classification_threshold": cls_validation_threshold[best_cls_name],
        "best_reg_model": best_reg_name,
        "evaluation": {
            "method": (
                "historical_years_train_then_2017_validation_then_2018_diagnostic_split"
            ),
            "training_years": sorted(
                int(year)
                for year in prepared.loc[
                    selection_indices,
                    "arrival_year",
                ].unique()
            ),
            "validation_year": validation_year,
            "validation_source": "hotel_reservations",
            "validation_year_rows": int(len(validation_indices)),
            "target_source_validation_rows": int(len(target_validation_indices)),
            "holdout_year": holdout_year,
            "classification_selection_metric": "validation_f1",
            "classification_threshold_source": "validation_year",
            "selection_training_rows": int(len(selection_indices)),
            "validation_rows": int(len(target_validation_indices)),
            "validation_year_rows": int(len(validation_indices)),
            "training_rows": int(len(training_indices)),
            "holdout_rows": int(len(holdout_indices)),
            "production_model_fit": "all_usable_rows_after_holdout_evaluation",
            "warning": (
                "The 2018 Hotel Reservations diagnostic split was inspected "
                "during prior model-development iterations, so it is not an "
                "independent final test. The source datasets also differ in "
                "feature coverage and population; scores do not establish "
                "performance for other hotels or future periods."
            ),
            "scikit_learn_version": sklearn.__version__,
        },
    }

    with tempfile.TemporaryDirectory(
        prefix=".model-staging-",
        dir=MODEL_DIR,
    ) as staging:
        staging_dir = Path(staging)
        staged_classifier = staging_dir / "cancellation_classifier.joblib"
        staged_regressor = staging_dir / "pricing_regressor.joblib"
        staged_metrics = staging_dir / "metrics_summary.json"
        staged_merged_data = staging_dir / MERGED_DATA_PATH.name
        joblib.dump(production_cls, staged_classifier)
        joblib.dump(production_reg, staged_regressor)
        metrics["operational"]["classifier_artifact_bytes"] = (
            staged_classifier.stat().st_size
        )
        metrics["operational"]["regressor_artifact_bytes"] = (
            staged_regressor.stat().st_size
        )
        prepared.to_csv(staged_merged_data, index=False)
        with staged_metrics.open("w", encoding="utf-8") as file:
            json.dump(metrics, file, indent=2)

        os.replace(staged_classifier, MODEL_DIR / "cancellation_classifier.joblib")
        os.replace(staged_regressor, MODEL_DIR / "pricing_regressor.joblib")
        os.replace(staged_metrics, MODEL_DIR / "metrics_summary.json")
        os.replace(staged_merged_data, MERGED_DATA_PATH)

    print(
        f"\n[4/4] Production models fitted on all {len(prepared):,} usable rows. "
        f"Artifacts saved to models/; merged data saved to {MERGED_DATA_PATH}."
    )


if __name__ == "__main__":
    main()
