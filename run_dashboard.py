import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🏨 GrandVista AI - Hotel Revenue & Reservation Intelligence")
    print("🚀 Dashboard URL: http://127.0.0.1:8000")
    print("📖 Swagger API Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
