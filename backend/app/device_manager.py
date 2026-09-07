import re
from typing import Dict, Any

class DeviceManager:
    def parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """Extracts operating system and browser details from User-Agent string."""
        ua = user_agent.lower()
        
        # Detect OS
        os = "Unknown OS"
        if "windows" in ua:
            os = "Windows"
        elif "macintosh" in ua or "mac os" in ua:
            os = "Mac OS"
        elif "linux" in ua:
            os = "Linux"
        elif "iphone" in ua or "ipad" in ua:
            os = "iOS"
        elif "android" in ua:
            os = "Android"
            
        # Detect Browser
        browser = "Unknown Browser"
        if "chrome" in ua:
            browser = "Google Chrome"
        elif "firefox" in ua:
            browser = "Mozilla Firefox"
        elif "safari" in ua and "chrome" not in ua:
            browser = "Safari"
        elif "edge" in ua:
            browser = "Microsoft Edge"
            
        return {"os": os, "browser": browser}

    def evaluate_device_risk(self, ip_address: str, user_agent: str, is_trusted: bool) -> int:
        """Calculates a safety risk score (0 to 100) based on client parameters."""
        risk = 0
        if not is_trusted:
            risk += 30
        if ip_address.startswith("10.") or ip_address.startswith("192.168."):
            # Safe local network
            pass
        else:
            risk += 20 # External IP penalty
            
        # Old user agents / bot signatures
        if "bot" in user_agent.lower() or "python" in user_agent.lower():
            risk += 40
            
        return min(risk, 100)

device_manager = DeviceManager()
