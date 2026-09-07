from fastapi import FastAPI
from shared import schemas

app = FastAPI(title="NGEL Service", version="1.0.0")

@app.post("/ngel/evaluate", response_model=schemas.NGELEvaluateResponse)
def evaluate(request: schemas.NGELEvaluateRequest):
    # Safe governance policy gate
    if request.risk_level == "critical":
        return schemas.NGELEvaluateResponse(allowed=False, reason="Action violates strict safety constraints.")
    return schemas.NGELEvaluateResponse(allowed=True, reason="Governance policy check passed.")
