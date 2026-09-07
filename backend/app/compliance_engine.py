from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List


class ComplianceAutomation:
    def scan_path(self, target_path: Path) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        for path in sorted(target_path.rglob("*")):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue

            if re.search(r"AKIA[0-9A-Z]{16}", content):
                findings.append({"path": str(path), "kind": "aws-access-key-detected"})
            if re.search(r"ghp_[A-Za-z0-9]{36}", content):
                findings.append({"path": str(path), "kind": "github-token-detected"})
            if "secret" in path.name.lower() or "token" in path.name.lower():
                findings.append({"path": str(path), "kind": "suspicious-file-name"})
            if "requests==" in content or "==" in content and "requirements" in path.name.lower():
                findings.append({"path": str(path), "kind": "dependency-declaration"})

        return {"status": "completed", "findings": findings}
