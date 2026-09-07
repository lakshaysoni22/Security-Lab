from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from ..elasticsearch_client import es_client

router = APIRouter(prefix="/api/elasticsearch", tags=["Elasticsearch & Kibana SIEM Aggregation"])

@router.get("/status")
def get_elasticsearch_status():
    return es_client.get_cluster_health()

@router.post("/indices/template")
def load_index_template(
    name: str = Query(...),
    properties: Dict[str, Any] = Body(...)
):
    return es_client.load_index_template(name, properties)

@router.post("/search")
def search_indices(
    index: str = Query(...),
    query: Dict[str, Any] = Body(...)
):
    return es_client.search_logs(index, query)

@router.post("/kibana/saved-objects")
def create_kibana_saved_object(
    type: str = Body(...),
    title: str = Body(...),
    attributes: Dict[str, Any] = Body(...)
):
    return es_client.save_kibana_object(type, title, attributes)

@router.get("/kibana/saved-objects")
def get_kibana_saved_objects(type: Optional[str] = Query(None)):
    return es_client.list_saved_objects(type)
