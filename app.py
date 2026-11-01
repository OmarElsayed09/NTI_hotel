import calendar
import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import sklearn
import streamlit as st

from src.prediction import (
    BATCH_REQUIRED_COLUMNS,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_ROWS,
    predict_batch_bookings,
    to_safe_csv_bytes,
)
from src.datasets import load_merged_hotel_reservations

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGGER = logging.getLogger(__name__)

TEXT = {
    "ar": {
        "title": "توقع إلغاء الحجوزات وتسعير الغرف",
        "subtitle": "تحليلات وتوقعات إرشادية مبنية على 3 مجموعات حجوزات موحّدة.",
        "dataset_sources": "تم دمج المصادر الثلاثة بعد توحيد الأعمدة؛ نسخة hotel_bookings.csv الموجودة بجذر المشروع مطابقة للملف الكامل ولم تُحتسب مرتين.",
        "language": "اللغة",
        "project_info": "معلومات عن البيانات والنموذج",
        "bookings": "الحجوزات في مجموعة البيانات",
        "cancel_rate": "معدل الإلغاء",
        "average_adr": "متوسط سعر الغرفة للحجوزات المكتملة",
        "navigation": "القسم",
        "pages": ["توقع حجز", "تحليل CSV", "استكشاف البيانات"],
        "input_header": "بيانات الحجز المتاحة وقت الإدخال",
        "basic_details": "البيانات الأساسية",
        "more_details": "تفاصيل إضافية",
        "more_details_help": "عدّل القيم الافتراضية إذا كانت لديك معلومات أدق عن الحجز.",
        "quoted_price_help": "السعر الحالي يساعد في تقدير الإلغاء، ولا يدخل في تقدير سعر الغرفة.",
        "adults": "عدد البالغين",
        "children": "عدد الأطفال",
        "weekend_nights": "ليالي نهاية الأسبوع",
        "week_nights": "ليالي أيام الأسبوع",
        "lead_time": "أيام بين الحجز والوصول",
        "arrival_year": "سنة الوصول",
        "arrival_month": "شهر الوصول",
        "arrival_day": "يوم الوصول",
        "meal": "خطة الوجبات",
        "parking": "موقف سيارة مطلوب",
        "room": "نوع الغرفة المحجوزة",
        "segment": "قناة السوق",
        "repeated": "ضيف متكرر",
        "previous_cancellations": "إلغاءات سابقة",
        "previous_kept": "حجوزات سابقة غير ملغاة",
        "quoted_price": "السعر الحالي للغرفة (ADR)",
        "requests": "الطلبات الخاصة",
        "analyze": "حلّل الحجز",
        "price_prediction": "السعر اليومي التقديري",
        "cancellation_probability": "احتمال الإلغاء",
        "cancellation_result": "نتيجة الإلغاء",
        "predicted_status": "التصنيف عند عتبة التحقق",
        "projected_revenue": "إجمالي سعر الإقامة المتوقع",
        "disclaimer": "هذه نتائج تاريخية إرشادية وليست ضمانًا للأداء المستقبلي. البيانات تغطي 2015–2018 ومصادرها وفنادقها مختلفة.",
        "batch_header": "التنبؤ لمجموعة حجوزات",
        "batch_help": "ارفع CSV بالأعمدة المطلوبة. يمكن أن يحتوي الملف على booking_status لعرض الحقيقة التاريخية، لكنه لا يدخل أبدًا ضمن مدخلات الموديل.",
        "download_template": "تنزيل قالب CSV",
        "upload": "رفع CSV",
        "download_results": "تنزيل النتائج",
        "too_big": "حجم الملف يتجاوز 10 ميجابايت.",
        "too_many": "الملف يتجاوز 10,000 صف.",
        "actual_status": "الحالة الفعلية موجودة للمقارنة، ولم تستخدم في التوقع.",
        "eda_year": "معدل الإلغاء حسب سنة الوصول",
        "eda_segment": "معدل الإلغاء حسب قناة السوق",
        "eda_adr": "توزيع السعر اليومي للحجوزات المكتملة",
        "eda_lead": "مهلة الحجز مقارنة بالحالة",
        "drift_warning": "تنبيه: المصادر تختلف في الفنادق والفترات وتغطية الحقول، لذلك قد تختلف النتائج عند استخدامها مع فنادق أو فترات أخرى.",
        "dataset_error": "تعذر تحميل بيانات أو نماذج المشروع. راجع الملفات ثم أعد تشغيل التطبيق.",
        "prediction_error": "تعذر إكمال التوقع. راجع صحة القيم المدخلة.",
        "invalid_csv": "تعذرت قراءة الملف. تأكد أنه CSV صالح.",
        "all_years": "كل السنوات",
        "year_filter": "سنة الوصول",
        "outcome": "حالة الحجز",
        "canceled": "ملغي",
        "not_canceled": "غير ملغي",
        "revenue_note": "إيراد إجمالي تقديري وليس سعرًا أمثل أو توقعًا للربح.",
    },
    "en": {
        "title": "Hotel Reservation Cancellation & Rate Prediction",
        "subtitle": "Advisory analysis using three harmonized hotel-booking datasets.",
        "dataset_sources": "Three sources are mapped to shared booking fields; the root-level hotel_bookings.csv is an exact copy of the full source and is not counted twice.",
        "language": "Language",
        "project_info": "About the data and model",
        "bookings": "Bookings in dataset",
        "cancel_rate": "Cancellation rate",
        "average_adr": "Average room rate for completed bookings",
        "navigation": "Section",
        "pages": ["Single booking", "Batch CSV", "Explore data"],
        "input_header": "Information available when the booking is entered",
        "basic_details": "Booking basics",
        "more_details": "More booking details",
        "more_details_help": "Adjust the default values if you have more accurate booking information.",
        "quoted_price_help": "The current quote helps estimate cancellation; it is not used to estimate the room rate.",
        "adults": "Adults",
        "children": "Children",
        "weekend_nights": "Weekend nights",
        "week_nights": "Week nights",
        "lead_time": "Days between booking and arrival",
        "arrival_year": "Arrival year",
        "arrival_month": "Arrival month",
        "arrival_day": "Arrival day",
        "meal": "Meal plan",
        "parking": "Parking space required",
        "room": "Reserved room type",
        "segment": "Market segment",
        "repeated": "Repeated guest",
        "previous_cancellations": "Previous cancellations",
        "previous_kept": "Previous bookings not canceled",
        "quoted_price": "Current quoted room rate (ADR)",
        "requests": "Special requests",
        "analyze": "Analyze booking",
        "price_prediction": "Estimated daily rate",
        "cancellation_probability": "Cancellation probability",
        "cancellation_result": "Cancellation result",
        "predicted_status": "Classification at validation threshold",
        "projected_revenue": "Estimated total stay rate",
        "disclaimer": "These are advisory historical estimates, not a guarantee of future performance. The data spans 2015–2018 and combines different sources and hotel populations.",
        "batch_header": "Batch booking predictions",
        "batch_help": "Upload a CSV with the required columns. It may include booking_status for historical comparison, but that label is never used as a model input.",
        "download_template": "Download CSV template",
        "upload": "Upload CSV",
        "download_results": "Download results",
        "too_big": "The file exceeds 10 MB.",
        "too_many": "The file exceeds 10,000 rows.",
        "actual_status": "Actual status is shown for comparison and was not used for prediction.",
        "eda_year": "Cancellation rate by arrival year",
        "eda_segment": "Cancellation rate by market segment",
        "eda_adr": "Daily rate distribution for completed bookings",
        "eda_lead": "Booking lead time by outcome",
        "drift_warning": "Warning: sources differ in hotel populations, dates, and field coverage, so results may differ for other hotels or periods.",
        "dataset_error": "Project data or models could not be loaded. Check the files and restart the app.",
        "prediction_error": "Prediction could not be completed. Check the input values.",
        "invalid_csv": "Could not read the file. Ensure it is a valid CSV.",
        "all_years": "All years",
        "year_filter": "Arrival year",
        "outcome": "Booking status",
        "canceled": "Canceled",
        "not_canceled": "Not canceled",
        "revenue_note": "Gross estimated stay revenue; not an optimized rate or profit prediction.",
    },
}

st.set_page_config(
    page_title="Hotel Reservation Cancellation & Rate Prediction",
    page_icon="🏨",
    layout="wide",
)


@st.cache_resource
def load_artifacts():
    with (BASE_DIR / "models" / "metrics_summary.json").open(
        "r",
        encoding="utf-8",
    ) as file:
        metrics = json.load(file)
    data, source_audit = load_merged_hotel_reservations(DATA_DIR)
    dataset_metrics = metrics.get("dataset", {})
    if dataset_metrics.get("files") != source_audit["files"]:
        raise ValueError("Saved models do not match the configured booking sources.")
    if dataset_metrics.get("sources") != source_audit["sources"]:
        raise ValueError("Booking source files changed after the models were trained.")
    if dataset_metrics.get("usable_rows") != len(data):
        raise ValueError("Saved model metrics do not match the merged booking data.")
    if "classification_threshold" not in metrics:
        raise ValueError("Model metrics do not include a classification threshold.")
    training_sklearn_version = metrics.get("evaluation", {}).get(
        "scikit_learn_version"
    )
    if (
        training_sklearn_version
        and training_sklearn_version != sklearn.__version__
    ):
        raise ValueError(
            "The saved models were trained with scikit-learn "
            f"{training_sklearn_version}, but the runtime has {sklearn.__version__}."
        )
    classifier = joblib.load(BASE_DIR / "models" / "cancellation_classifier.joblib")
    regressor = joblib.load(BASE_DIR / "models" / "pricing_regressor.joblib")
    return classifier, regressor, metrics, data


try:
    classifier, regressor, metrics, data = load_artifacts()
except Exception:
    LOGGER.exception("Application data or model artifacts could not be loaded.")
    st.error("Required application files could not be loaded. Check data/ and models/.")
    st.stop()

language = st.sidebar.radio("Language / اللغة", ["العربية", "English"])
lang = "ar" if language == "العربية" else "en"
t = TEXT[lang]
page = st.sidebar.radio(t["navigation"], t["pages"])

st.title(f"🏨 {t['title']}")
st.caption(t["subtitle"])

if page == t["pages"][0]:
    with st.expander(t["project_info"]):
        st.caption(t["dataset_sources"])
        info1, info2, info3 = st.columns(3)
        info1.metric(t["bookings"], f"{len(data):,}")
        info2.metric(t["cancel_rate"], f"{data['is_canceled'].mean() * 100:.1f}%")
        info3.metric(t["average_adr"], f"${metrics['dataset']['average_adr']:.2f}")
        st.warning(t["drift_warning"])

    st.subheader(t["input_header"])
    with st.form("reservation_prediction"):
        st.caption(t["basic_details"])
        col1, col2 = st.columns(2)
        with col1:
            adults = st.number_input(t["adults"], 1, 10, 2)
            children = st.number_input(t["children"], 0, 10, 0)
            weekend_nights = st.number_input(t["weekend_nights"], 0, 20, 1)
            week_nights = st.number_input(t["week_nights"], 0, 30, 2)
            lead_time = st.number_input(t["lead_time"], 0, 1000, 30)
        with col2:
            years = sorted(data["arrival_year"].unique().tolist())
            arrival_year = st.selectbox(t["arrival_year"], years, index=len(years) - 1)
            arrival_month = st.selectbox(t["arrival_month"], range(1, 13), index=5)
            max_day = calendar.monthrange(int(arrival_year), int(arrival_month))[1]
            arrival_date = st.selectbox(t["arrival_day"], range(1, max_day + 1))
            quoted_price = st.number_input(
                t["quoted_price"],
                min_value=0.0,
                value=float(metrics["dataset"]["average_adr"]),
                step=5.0,
                help=t["quoted_price_help"],
            )

        with st.expander(t["more_details"]):
            st.caption(t["more_details_help"])
            meal_options = sorted(data["type_of_meal_plan"].unique().tolist())
            meal = st.selectbox(
                t["meal"],
                meal_options,
                index=meal_options.index(data["type_of_meal_plan"].mode().iloc[0]),
            )
            room_options = sorted(data["room_type_reserved"].unique().tolist())
            room = st.selectbox(
                t["room"],
                room_options,
                index=room_options.index(data["room_type_reserved"].mode().iloc[0]),
            )
            segment_options = sorted(data["market_segment_type"].unique().tolist())
            segment = st.selectbox(
                t["segment"],
                segment_options,
                index=segment_options.index(
                    data["market_segment_type"].mode().iloc[0]
                ),
            )
            parking = st.selectbox(t["parking"], [0, 1])
            repeated = st.selectbox(t["repeated"], [0, 1])
            previous_cancellations = st.number_input(
                t["previous_cancellations"],
                0,
                100,
                0,
            )
            previous_kept = st.number_input(t["previous_kept"], 0, 100, 0)
            requests = st.number_input(t["requests"], 0, 20, 0)
        submitted = st.form_submit_button(t["analyze"], type="primary")

        if submitted:
            if adults + children < 1:
                st.error("Each reservation must include at least one guest.")
            else:
                booking = pd.DataFrame(
                    [
                        {
                            "no_of_adults": adults,
                            "no_of_children": children,
                            "no_of_weekend_nights": weekend_nights,
                            "no_of_week_nights": week_nights,
                            "type_of_meal_plan": meal,
                            "required_car_parking_space": parking,
                            "room_type_reserved": room,
                            "lead_time": lead_time,
                            "arrival_year": arrival_year,
                            "arrival_month": arrival_month,
                            "arrival_date": arrival_date,
                            "market_segment_type": segment,
                            "repeated_guest": repeated,
                            "no_of_previous_cancellations": previous_cancellations,
                            "no_of_previous_bookings_not_canceled": previous_kept,
                            "avg_price_per_room": quoted_price,
                            "no_of_special_requests": requests,
                        }
                    ]
                )
                try:
                    result = predict_batch_bookings(
                        booking,
                        classifier,
                        regressor,
                        metrics["classification_threshold"],
                    ).iloc[0]
                except Exception:
                    LOGGER.exception("Single reservation prediction failed.")
                    st.error(t["prediction_error"])
                else:
                    a, b, c = st.columns(3)
                    a.metric(t["price_prediction"], f"${result['predicted_adr']:.2f}")
                    b.metric(
                        t["cancellation_probability"],
                        f"{result['cancellation_probability'] * 100:.1f}%",
                    )
                    c.metric(
                        t["cancellation_result"],
                        result["predicted_status"].replace("_", " "),
                    )
                    st.caption(
                        f"{t['projected_revenue']}: "
                        f"${result['projected_total_revenue']:.2f} · "
                        f"{t['revenue_note']}"
                    )
    st.info(t["disclaimer"])

elif page == t["pages"][1]:
    st.subheader(t["batch_header"])
    st.write(t["batch_help"])
    template = data[BATCH_REQUIRED_COLUMNS].head(5)
    st.download_button(
        t["download_template"],
        data=template.to_csv(index=False).encode("utf-8-sig"),
        file_name="hotel_reservations_template.csv",
        mime="text/csv",
    )
    uploaded_file = st.file_uploader(t["upload"], type=["csv"])
    if uploaded_file is not None:
        if uploaded_file.size > MAX_UPLOAD_BYTES:
            st.error(t["too_big"])
        else:
            try:
                uploaded = pd.read_csv(uploaded_file, nrows=MAX_UPLOAD_ROWS + 1)
                if len(uploaded) > MAX_UPLOAD_ROWS:
                    st.error(t["too_many"])
                else:
                    results = predict_batch_bookings(
                        uploaded,
                        classifier,
                        regressor,
                        metrics["classification_threshold"],
                    )
                    st.dataframe(results, hide_index=True, use_container_width=True)
                    if "booking_status" in uploaded.columns:
                        st.caption(t["actual_status"])
                    st.download_button(
                        t["download_results"],
                        data=to_safe_csv_bytes(results),
                        file_name="hotel_reservation_predictions.csv",
                        mime="text/csv",
                    )
            except pd.errors.EmptyDataError:
                st.error(t["invalid_csv"])
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                LOGGER.exception("Batch reservation prediction failed.")
                st.error(t["invalid_csv"])

elif page == t["pages"][2]:
    selected_year = st.selectbox(
        t["year_filter"],
        [t["all_years"]] + sorted(data["arrival_year"].unique().tolist()),
        key="eda_year",
    )
    view = data if selected_year == t["all_years"] else data[
        data["arrival_year"] == selected_year
    ]
    left, right = st.columns(2)
    with left:
        by_year = (
            data.groupby("arrival_year", as_index=False)["is_canceled"]
            .mean()
            .assign(cancellation_rate=lambda frame: frame["is_canceled"] * 100)
        )
        fig = px.bar(
            by_year,
            x="arrival_year",
            y="cancellation_rate",
            title=t["eda_year"],
            labels={"arrival_year": t["arrival_year"], "cancellation_rate": "%"},
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        by_segment = (
            view.groupby("market_segment_type", as_index=False)["is_canceled"]
            .mean()
            .assign(cancellation_rate=lambda frame: frame["is_canceled"] * 100)
        )
        fig = px.bar(
            by_segment,
            x="market_segment_type",
            y="cancellation_rate",
            title=t["eda_segment"],
            labels={"market_segment_type": t["segment"], "cancellation_rate": "%"},
        )
        st.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    with left:
        completed = view.loc[view["is_canceled"] == 0]
        fig = px.histogram(
            completed,
            x="avg_price_per_room",
            color="market_segment_type",
            title=t["eda_adr"],
            nbins=40,
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        outcomes = view.assign(
            outcome=np.where(view["is_canceled"] == 1, t["canceled"], t["not_canceled"])
        )
        fig = px.box(
            outcomes,
            x="outcome",
            y="lead_time",
            color="outcome",
            title=t["eda_lead"],
            labels={"outcome": t["outcome"], "lead_time": t["lead_time"]},
        )
        st.plotly_chart(fig, use_container_width=True)
