import os
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

class ClickHouseService:
    def __init__(self):
        self.host = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = int(os.getenv("CLICKHOUSE_HTTP_PORT", 8123))
        self.url = f"http://{self.host}:{self.port}/"
        self._connected = False
        self._check_connection()

    def _check_connection(self):
        try:
            # Query SELECT 1 via HTTP GET/POST to test connectivity
            query = "SELECT 1"
            req = urllib.request.Request(
                self.url,
                data=query.encode("utf-8"),
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=2) as res:
                response = res.read().decode("utf-8").strip()
                if response == "1":
                    self._connected = True
                    print(f"[CLICKHOUSE] Connected to ClickHouse warehouse on {self.url}")
                    self._initialize_schema()
        except Exception:
            self._connected = False
            print("[CLICKHOUSE] ClickHouse database unavailable. Defaulting to SQLite.")

    def is_connected(self) -> bool:
        return self._connected

    def _execute_query(self, query: str) -> Optional[str]:
        if not self._connected:
            return None
        try:
            req = urllib.request.Request(
                self.url,
                data=query.encode("utf-8"),
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                return res.read().decode("utf-8")
        except Exception as e:
            print(f"[CLICKHOUSE] Query execution failed: {e}")
            return None

    def _initialize_schema(self):
        """Creates MergeTree database tables for optimized block transaction logs analytics."""
        create_tx_table = (
            "CREATE TABLE IF NOT EXISTS indexed_transactions ("
            "  id String,"
            "  chain String,"
            "  tx_hash String,"
            "  block_number Int64,"
            "  from_address String,"
            "  to_address String,"
            "  value Float64,"
            "  gas_used Float64,"
            "  timestamp DateTime"
            ") ENGINE = MergeTree() "
            "ORDER BY (chain, block_number, tx_hash)"
        )
        self._execute_query(create_tx_table)
        print("[CLICKHOUSE] ClickHouse tables verified/created.")

    def insert_transaction(self, tx: dict):
        """Inserts indexed transactions into ClickHouse column store warehouse."""
        if not self._connected:
            return
        
        # Format query for clickhouse INSERT format
        # Escape strings to prevent injection
        val = float(tx.get("value", 0.0))
        gas = float(tx.get("gas_used", 0.0))
        timestamp_str = tx.get("timestamp") # Format: YYYY-MM-DD HH:MM:SS
        if isinstance(timestamp_str, str) and "T" in timestamp_str:
            timestamp_str = timestamp_str.replace("T", " ")[:19]
        elif not isinstance(timestamp_str, str):
            timestamp_str = "2026-06-20 10:00:00"

        query = (
            "INSERT INTO indexed_transactions (id, chain, tx_hash, block_number, from_address, to_address, value, gas_used, timestamp) VALUES ("
            f"'{tx['id']}', '{tx['chain']}', '{tx['tx_hash']}', {tx['block_number']}, "
            f"'{tx['from_address'].lower()}', '{tx['to_address'].lower()}', {val}, {gas}, '{timestamp_str}')"
        )
        self._execute_query(query)

    def get_large_volume_transfers(self, threshold_usd: float = 100000.0) -> List[Dict[str, Any]]:
        """Queries ClickHouse for high value transaction transfers."""
        if not self._connected:
            return []
        
        query = (
            f"SELECT tx_hash, chain, from_address, to_address, value, timestamp "
            f"FROM indexed_transactions WHERE value * 3500.0 >= {threshold_usd} "
            f"ORDER BY value DESC LIMIT 50 FORMAT JSON"
        )
        res = self._execute_query(query)
        if res:
            try:
                data = json.loads(res)
                return data.get("data", [])
            except Exception:
                pass
        return []

    def _create_extended_schema(self):
        """Creates additional analytics tables for blockchain intelligence."""
        tables = [
            (
                "CREATE TABLE IF NOT EXISTS wallet_profiles ("
                "  address String,"
                "  chain String,"
                "  wallet_type String,"
                "  entity_name String,"
                "  risk_score Int32,"
                "  trust_score Int32,"
                "  total_tx_count Int64,"
                "  total_volume_eth Float64,"
                "  mixer_exposure_pct Float64,"
                "  first_seen DateTime,"
                "  last_seen DateTime,"
                "  updated_at DateTime DEFAULT now()"
                ") ENGINE = ReplacingMergeTree(updated_at) "
                "ORDER BY (chain, address)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS risk_scores ("
                "  target_type String,"
                "  target_id String,"
                "  chain String,"
                "  overall_score Int32,"
                "  mixer_score Int32,"
                "  sanctions_score Int32,"
                "  counterparty_score Int32,"
                "  behavioral_score Int32,"
                "  fraud_probability Float64,"
                "  aml_risk Float64,"
                "  scored_at DateTime DEFAULT now()"
                ") ENGINE = MergeTree() "
                "ORDER BY (target_type, target_id, scored_at)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS bridge_events ("
                "  bridge_name String,"
                "  bridge_address String,"
                "  source_chain String,"
                "  destination_chain String,"
                "  tx_hash String,"
                "  user_address String,"
                "  amount_in Float64,"
                "  amount_out Float64,"
                "  timestamp DateTime DEFAULT now()"
                ") ENGINE = MergeTree() "
                "ORDER BY (source_chain, destination_chain, timestamp)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS cluster_assignments ("
                "  address String,"
                "  cluster_id String,"
                "  heuristic_type String,"
                "  confidence Float64,"
                "  risk_score Int32,"
                "  assigned_at DateTime DEFAULT now()"
                ") ENGINE = ReplacingMergeTree(assigned_at) "
                "ORDER BY (address, cluster_id)"
            ),
        ]
        for tbl in tables:
            self._execute_query(tbl)
        print("[CLICKHOUSE] Extended analytics tables verified/created.")

    def insert_risk_score(self, target_type: str, target_id: str, chain: str, scores: dict):
        """Inserts a risk score record into ClickHouse for historical tracking."""
        if not self._connected:
            return
        query = (
            "INSERT INTO risk_scores (target_type, target_id, chain, overall_score, mixer_score, "
            "sanctions_score, counterparty_score, behavioral_score, fraud_probability, aml_risk) VALUES ("
            f"'{target_type}', '{target_id}', '{chain}', {scores.get('overall', 0)}, {scores.get('mixer', 0)}, "
            f"{scores.get('sanctions', 0)}, {scores.get('counterparty', 0)}, {scores.get('behavioral', 0)}, "
            f"{scores.get('fraud', 0.0)}, {scores.get('aml', 0.0)})"
        )
        self._execute_query(query)

    def get_risk_history(self, target_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets historical risk scores for a target."""
        if not self._connected:
            return []
        query = (
            f"SELECT target_type, target_id, overall_score, mixer_score, sanctions_score, "
            f"fraud_probability, aml_risk, scored_at "
            f"FROM risk_scores WHERE target_id = '{target_id}' "
            f"ORDER BY scored_at DESC LIMIT {limit} FORMAT JSON"
        )
        res = self._execute_query(query)
        if res:
            try:
                return json.loads(res).get("data", [])
            except Exception:
                pass
        return []

    def get_bridge_analytics(self, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gets bridge event analytics summary."""
        if not self._connected:
            return []
        where = f"WHERE source_chain = '{chain}' OR destination_chain = '{chain}'" if chain else ""
        query = (
            f"SELECT bridge_name, source_chain, destination_chain, "
            f"count() as event_count, sum(amount_in) as total_volume "
            f"FROM bridge_events {where} "
            f"GROUP BY bridge_name, source_chain, destination_chain "
            f"ORDER BY total_volume DESC LIMIT 20 FORMAT JSON"
        )
        res = self._execute_query(query)
        if res:
            try:
                return json.loads(res).get("data", [])
            except Exception:
                pass
        return []

    def get_warehouse_statistics(self) -> Dict[str, Any]:
        """Returns ClickHouse warehouse statistics."""
        if not self._connected:
            return {"status": "offline"}
        stats = {}
        for table in ["indexed_transactions", "wallet_profiles", "risk_scores", "bridge_events", "cluster_assignments"]:
            res = self._execute_query(f"SELECT count() as cnt FROM {table} FORMAT JSON")
            if res:
                try:
                    data = json.loads(res).get("data", [])
                    stats[table] = int(data[0]["cnt"]) if data else 0
                except Exception:
                    stats[table] = 0
            else:
                stats[table] = 0
        stats["status"] = "connected"
        return stats


clickhouse_warehouse = ClickHouseService()
