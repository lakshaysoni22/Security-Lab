from typing import Dict, Any, List

# Local templates and saved objects database representation
INDEX_TEMPLATES = {}
SAVED_OBJECTS = []

class ElasticsearchClient:
    def get_cluster_health(self) -> Dict[str, Any]:
        """Queries Elasticsearch cluster status metrics."""
        return {
            "cluster_name": "LEAtTrace-siem-cluster",
            "status": "green",
            "timed_out": False,
            "number_of_nodes": 3,
            "number_of_data_nodes": 3,
            "active_primary_shards": 42,
            "active_shards": 84,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0
        }

    def load_index_template(self, template_name: str, mapping_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a composable index template with mappings and settings."""
        template = {
            "index_patterns": [f"{template_name}-*"],
            "template": {
                "settings": {
                    "index": {
                        "number_of_shards": 3,
                        "number_of_replicas": 1,
                        "lifecycle": {
                            "name": "LEAtTrace-ilm-policy",
                            "rollover_alias": template_name
                        }
                    }
                },
                "mappings": {
                    "properties": mapping_properties
                }
            }
        }
        INDEX_TEMPLATES[template_name] = template
        return template

    def search_logs(self, index_pattern: str, query_body: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates elasticsearch log search queries against target indexes."""
        # Simple simulation returning matches
        return {
            "took": 12,
            "timed_out": False,
            "_shards": {"total": 3, "successful": 3, "skipped": 0, "failed": 0},
            "hits": {
                "total": {"value": 1, "relation": "eq"},
                "max_score": 1.0,
                "hits": [
                    {
                        "_index": f"{index_pattern}-2026.06.29",
                        "_id": "log_doc_101",
                        "_score": 1.0,
                        "_source": {
                            "timestamp": "2026-06-29T12:00:00Z",
                            "message": "User login success",
                            "ip": "192.168.1.42"
                        }
                    }
                ]
            }
        }

    def save_kibana_object(self, object_type: str, title: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Creates or registers a Kibana Saved Object (dashboard, visualization, data view)."""
        new_obj = {
            "id": f"{object_type}--{title.lower().replace(' ', '-')}",
            "type": object_type,
            "attributes": {
                "title": title,
                **attributes
            }
        }
        SAVED_OBJECTS.append(new_obj)
        return new_obj

    def list_saved_objects(self, object_type: str = None) -> List[Dict[str, Any]]:
        """Lists active Kibana Saved Objects."""
        if object_type:
            return [o for o in SAVED_OBJECTS if o["type"] == object_type]
        return SAVED_OBJECTS

es_client = ElasticsearchClient()
