FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy codebase
COPY . .

# Set PYTHONPATH to root of project to enable relative module imports
ENV PYTHONPATH=/app

EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003
EXPOSE 8004
EXPOSE 8005
EXPOSE 8006

# Default command runs the main multi-process ecosystem runner
CMD ["python", "main.py"]
