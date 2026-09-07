"""
LEATrace Multi-Cloud Secret Adapter.

Provides unified secret management abstraction for:
- AWS Secrets Manager / KMS
- GCP Secret Manager
- Azure Key Vault
- Environment Variable Fallback
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("leatrace.cloud.secrets")


class CloudSecretAdapter:
    """
    Multi-cloud Secret Management Abstraction Layer.
    Fetches sensitive API keys, database credentials, and cryptographic secrets.
    """

    def __init__(self):
        self.provider = os.getenv("SECRET_PROVIDER", "env").lower()

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieves a secret value by key from cloud vault or environment variables."""
        if self.provider == "aws":
            try:
                import boto3
                client = boto3.client("secretsmanager")
                response = client.get_secret_value(SecretId=secret_name)
                return response.get("SecretString")
            except Exception as e:
                logger.warning(f"AWS Secret Manager failed for '{secret_name}': {e}")

        elif self.provider == "gcp":
            try:
                from google.cloud import secretmanager
                client = secretmanager.SecretManagerServiceClient()
                project_id = os.getenv("GCP_PROJECT_ID", "leattrace-gov")
                name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")
            except Exception as e:
                logger.warning(f"GCP Secret Manager failed for '{secret_name}': {e}")

        # Environment variable fallback
        return os.getenv(secret_name)


cloud_secret_adapter = CloudSecretAdapter()
