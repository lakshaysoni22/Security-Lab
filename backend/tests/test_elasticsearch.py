import pytest
from app.elasticsearch_client import es_client

def test_elasticsearch_cluster_health():
    health = es_client.get_cluster_health()
    assert health["status"] == "green"
    assert health["number_of_nodes"] == 3
    assert health["cluster_name"] == "LEAtTrace-siem-cluster"

def test_index_template_registration():
    mapping = {
        "timestamp": {"type": "date"},
        "message": {"type": "text"},
        "ip": {"type": "ip"}
    }
    tmpl = es_client.load_index_template("auth-logs", mapping)
    assert "index_patterns" in tmpl
    assert "auth-logs-*" in tmpl["index_patterns"]
    assert tmpl["template"]["mappings"]["properties"]["ip"]["type"] == "ip"

def test_logs_search_query():
    query = {"query": {"match": {"message": "success"}}}
    res = es_client.search_logs("auth-logs", query)
    assert res["hits"]["total"]["value"] == 1
    assert res["hits"]["hits"][0]["_source"]["ip"] == "192.168.1.42"

def test_kibana_saved_objects_manager():
    # Save a dashboard object
    dashboard_attr = {
        "description": "SOC SIEM Overview Dashboard",
        "panelsJSON": "[]"
    }
    saved = es_client.save_kibana_object("dashboard", "SOC Overview", dashboard_attr)
    assert saved["id"] == "dashboard--soc-overview"
    assert saved["type"] == "dashboard"
    
    # List filtered objects
    all_dashboards = es_client.list_saved_objects("dashboard")
    assert len(all_dashboards) == 1
    assert all_dashboards[0]["attributes"]["title"] == "SOC Overview"
