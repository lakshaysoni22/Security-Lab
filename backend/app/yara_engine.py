import re
from typing import Dict, Any, List

class YaraEngine:
    def compile_rule(self, rule_text: str) -> Dict[str, Any]:
        """Parses a YARA rule block and extracts search strings/regexes."""
        strings = []
        # Simple extraction of string definitions: $a = "malicious_string" or $b = /regex/
        matches = re.findall(r'\$(\w+)\s*=\s*(["/])(.*?)\2', rule_text)
        for name, quote, pattern in matches:
            if quote == "/":
                strings.append({"name": name, "regex": re.compile(pattern)})
            else:
                strings.append({"name": name, "literal": pattern})
                
        return {"rule_text": rule_text, "strings": strings}

    def scan_content(self, compiled_rule: Dict[str, Any], content: str) -> List[str]:
        """Scans the text content against the compiled YARA rules. Returns list of matched string IDs."""
        matches = []
        for string in compiled_rule["strings"]:
            if "literal" in string:
                if string["literal"] in content:
                    matches.append(string["name"])
            elif "regex" in string:
                if string["regex"].search(content):
                    matches.append(string["name"])
        return matches

yara_engine = YaraEngine()
