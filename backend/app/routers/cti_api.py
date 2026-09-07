from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from typing import List, Dict, Any, Optional
from ..stix_engine import stix_engine
from ..taxii_client import taxii_client
from ..sigma_engine import sigma_engine
from ..yara_engine import yara_engine
from ..attack_engine import attack_engine
from ..ioc_engine import ioc_engine

router = APIRouter(prefix="/api/threat", tags=["Cyber Threat Intelligence (CTI)"])

@router.post("/stix/indicator")
def create_stix_indicator(name: str = Body(...), pattern: str = Body(...)):
    return stix_engine.create_indicator(name, pattern)

@router.get("/taxii/collections")
def list_taxii_collections():
    return taxii_client.list_collections()

@router.get("/taxii/collections/{collection_id}/objects")
def get_taxii_objects(collection_id: str):
    return taxii_client.sync_collection_objects(collection_id)

@router.post("/sigma/validate")
def validate_sigma_rule(rule_yaml: str = Body(..., embed=True)):
    try:
        parsed = sigma_engine.parse_rule(rule_yaml)
        return {"status": "valid", "title": parsed.get("title")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/yara/scan")
def scan_text_with_yara(
    rule_text: str = Body(...),
    content: str = Body(...)
):
    try:
        compiled = yara_engine.compile_rule(rule_text)
        matches = yara_engine.scan_content(compiled, content)
        return {"status": "completed", "matches": matches}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/attack/map")
def map_event_to_mitre(description: str = Query(...)):
    return attack_engine.map_log_to_technique(description)

@router.get("/ioc/check")
def check_ioc_value(value: str = Query(...)):
    return ioc_engine.check_ioc(value)

@router.post("/ioc/add")
def add_new_ioc(
    type: str = Body(...),
    value: str = Body(...),
    confidence: str = Body("medium")
):
    return ioc_engine.add_ioc(type, value, confidence)
