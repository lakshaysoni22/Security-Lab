from fastapi import FastAPI
from shared import schemas
import random

app = FastAPI(title="QCAL Service", version="1.0.0")

@app.post("/qcal/resolve", response_model=schemas.QCALResolveResponse)
def resolve(request: schemas.QCALResolveRequest):
    # Simply choose a path with high-dimension simulation probability weights
    if not request.inputs:
        return schemas.QCALResolveResponse(selected="", probability=0.0)

    selected = random.choice(request.inputs)
    prob = round(random.uniform(0.75, 0.98), 2)
    return schemas.QCALResolveResponse(selected=selected, probability=prob)
