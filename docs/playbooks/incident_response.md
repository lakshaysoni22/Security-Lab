# LEAtTrace Incident Response Playbooks

Detailed steps to validate, contain, eradicate, and recover from security incidents.

---

## 🦹 1. Playbook: Crypto Fraud & Mixer Laundering
* **Detection**: Large transactions routed to Tornado Cash mixers detected.
* **Validation**: Run `/api/blockchain/classify` to verify address risk score.
* **Containment**: Add target address to watchdog blacklist.
* **Eradication**: Notify exchanges and freeze associated accounts.
* **Recovery**: Re-index transaction blocks to monitor output peel chains.

---

## 🔐 2. Playbook: Insider Threat & Unauthorized Downloads
* **Detection**: Massive evidence zip downloads detected by the SIEM Correlation Engine.
* **Validation**: Check investigator ABAC geolocation locks.
* **Containment**: Call `/api/iam/session/revoke` to terminate investigator's active tokens.
* **Eradication**: Revoke RBAC permissions.
* **Recovery**: Restore evidence integrity checksum logs.
