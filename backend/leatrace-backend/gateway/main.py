import time
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gateway.routes import router
from shared.logger import logger

app = FastAPI(
    title="LEAtTrace API Gateway",
    description="Secure entry point and request router for LEAtTrace microservices architecture",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. Rate Limiting Middleware (100 req/min per IP) ---
rate_limit_records = {} # In-memory rate limiting store: {ip: [timestamps]}

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # Prune old timestamps
    if client_ip in rate_limit_records:
        rate_limit_records[client_ip] = [t for t in rate_limit_records[client_ip] if now - t < 60]
    else:
        rate_limit_records[client_ip] = []

    # Check limit
    if len(rate_limit_records[client_ip]) >= 100:
        logger.warning(f"Rate limit exceeded for client: {client_ip}")
        return Response(content="Rate limit exceeded. Max 100 requests per minute.", status_code=429)
        
    rate_limit_records[client_ip].append(now)
    response = await call_next(request)
    return response

# --- 2. Web Application Firewall (WAF) Input Sanitization Middleware ---
SQL_INJECTION_PATTERNS = ["UNION SELECT", "UNION ALL SELECT", "OR '1'='1'", "OR 1=1", "; DROP TABLE", "--"]
XSS_PATTERNS = ["<script>", "javascript:", "onload=", "onerror="]

@app.middleware("http")
async def waf_security_middleware(request: Request, call_next):
    # Scan request URL and query params
    url_str = str(request.url).upper()
    for pattern in SQL_INJECTION_PATTERNS + XSS_PATTERNS:
        if pattern.upper() in url_str:
            logger.warning(f"WAF blocked malicious request payload on URL: {request.url}")
            return Response(content="Malicious payload detected (WAF Block).", status_code=400)
            
    response = await call_next(request)
    return response

# --- 3. Security Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "API Gateway"}
