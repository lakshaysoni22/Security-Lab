from fastapi import FastAPI

app = FastAPI(title="ARNS Service", version="1.0.0")

@app.get("/arns/health")
def health():
    return {"status": "ARNS Reality Adaptation loop is running."}
