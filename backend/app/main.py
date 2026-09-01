from fastapi import FastAPI

app = FastAPI(title="OFFSHORE API", version="0.1.0")

@app.get("/")
def root():
    return {"message": "Welcome to OFFSHORE API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/risk-map")
def get_risk_map():
    return {"message": "Risk map endpoint placeholder", "data": []}
