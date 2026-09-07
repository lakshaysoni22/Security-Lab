@echo off
rem Generate self-signed TLS certificates on Windows using OpenSSL
set SSL_DIR=%~dp0certs
if not exist "%SSL_DIR%" mkdir "%SSL_DIR%"

if not exist "%SSL_DIR%\LEAtTrace.key" (
    echo Generating new self-signed TLS certificates for local domain: localhost...
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "%SSL_DIR%\LEAtTrace.key" -out "%SSL_DIR%\LEAtTrace.crt" -subj "/C=IN/ST=Delhi/L=New Delhi/O=NIA/OU=Cyber Incident Command/CN=localhost"
    echo TLS Certificates generated successfully in %SSL_DIR%
) else (
    echo TLS Certificates already exist in %SSL_DIR%. Skipping generation.
)
