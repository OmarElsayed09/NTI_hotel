import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import app, lifespan, predict_single, get_metadata, get_eda_data as get_eda, BookingInput, download_template

async def run_tests():
    print("Testing API endpoints directly...")
    async with lifespan(app):
        # 1. Metadata
        meta = get_metadata()
        assert "options" in meta
        print("[PASS] Metadata:", meta["options"]["segments"][:4])

        # 2. EDA
        eda = get_eda()
        assert "by_year" in eda
        print("[PASS] EDA loaded:", len(eda["by_year"]), "years")

        # 3. Single Prediction
        payload = BookingInput(
            no_of_adults=2,
            no_of_children=0,
            no_of_weekend_nights=1,
            no_of_week_nights=2,
            type_of_meal_plan="Meal Plan 1",
            required_car_parking_space=0,
            room_type_reserved="Room_Type 1",
            lead_time=30,
            arrival_year=2018,
            arrival_month=6,
            arrival_date=15,
            market_segment_type="Online",
            repeated_guest=0,
            no_of_previous_cancellations=0,
            no_of_previous_bookings_not_canceled=0,
            avg_price_per_room=105.0,
            no_of_special_requests=1
        )
        res = predict_single(payload)
        assert res.predicted_adr > 0
        assert 0 <= res.cancellation_probability <= 1
        assert res.cancellation_risk in ["Low", "Medium", "High"]
        assert len(res.recommendations) > 0
        print(f"[PASS] Prediction Output: ADR=${res.predicted_adr}, Probability={res.cancellation_probability*100:.1f}%, Risk={res.cancellation_risk}")
        print(f"[PASS] Recommendations count: {len(res.recommendations)}")

        # 4. Template download
        tmpl = download_template()
        assert tmpl.status_code == 200
        print("[PASS] Template download verified.")

    print("\n>>> All API tests passed with 100% success! <<<")

if __name__ == "__main__":
    asyncio.run(run_tests())
