from fastapi import APIRouter, Depends, HTTPException, Header
import httpx
from typing import Optional
from config.settings import settings
from shared import schemas, utils

router = APIRouter()

# Dependency to check user token (optional gate on non-auth APIs)
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = utils.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token has expired or is invalid")
    return payload

@router.post("/auth/register", response_model=schemas.TokenResponse)
async def register(request: schemas.UserRegisterRequest):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.AUTH_SERVICE_URL}/auth/register", json=request.dict())
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/auth/login", response_model=schemas.TokenResponse)
async def login(request: schemas.UserLoginRequest):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.AUTH_SERVICE_URL}/auth/login", json=request.dict())
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/cpos/process", response_model=schemas.CPOSProcessResponse)
async def process(request: schemas.CPOSProcessRequest, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.CPOS_SERVICE_URL}/cpos/process", json=request.dict())
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/riil/ingest", response_model=schemas.RIILIngestResponse)
async def ingest(request: schemas.RIILIngestRequest, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.RIIL_SERVICE_URL}/riil/ingest", json=request.dict())
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.get("/riil/state", response_model=schemas.RIILStateResponse)
async def get_state(token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{settings.RIIL_SERVICE_URL}/riil/state")
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/ngel/evaluate", response_model=schemas.NGELEvaluateResponse)
async def evaluate(request: schemas.NGELEvaluateRequest, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.NGEL_SERVICE_URL}/ngel/evaluate", json=request.dict())
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/qcal/resolve", response_model=schemas.QCALResolveResponse)
async def resolve(request: schemas.QCALResolveRequest, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.QCAL_SERVICE_URL}/qcal/resolve", json=request.dict())
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/blockchain/trace")
async def trace(request: dict, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.BLOCKCHAIN_SERVICE_URL}/blockchain/trace", json=request)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/investigation/cases/create")
async def create_case(request: dict, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.INVESTIGATION_SERVICE_URL}/investigation/cases/create", json=request)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/investigation/detect-fraud")
async def detect_fraud(request: dict, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.INVESTIGATION_SERVICE_URL}/investigation/detect-fraud", json=request)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()

@router.post("/investigation/forensic-report")
async def generate_forensic_report(request: dict, token_payload: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{settings.INVESTIGATION_SERVICE_URL}/investigation/forensic-report", json=request)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Error"))
        return res.json()
