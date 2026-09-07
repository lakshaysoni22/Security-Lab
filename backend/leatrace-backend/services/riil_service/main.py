from fastapi import FastAPI
from shared import schemas

app = FastAPI(title="RIIL Service", version="1.0.0")

@app.post("/riil/ingest", response_model=schemas.RIILIngestResponse)
def ingest(request: schemas.RIILIngestRequest):
    return schemas.RIILIngestResponse(
        status="success",
        ingested_events_count=1
    )

@app.get("/riil/state", response_model=schemas.RIILStateResponse)
def get_state():
    return schemas.RIILStateResponse(
        system_state="active",
        external_sync=True
    )
