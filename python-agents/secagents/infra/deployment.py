"""Deployment automation for SecAgents."""

import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manage SecAgents deployment across environments."""

    def __init__(self, environment: str = "staging"):
        self.environment = environment

    def deploy_docker(self) -> bool:
        """Deploy using Docker Compose."""
        try:
            logger.info(f"Starting Docker deployment ({self.environment})...")
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            logger.info("Docker deployment completed successfully")
            return True
        except Exception as e:
            logger.error(f"Docker deployment failed: {e}")
            return False

    def deploy_kubernetes(self) -> bool:
        """Deploy using Kubernetes."""
        try:
            logger.info(f"Starting Kubernetes deployment ({self.environment})...")
            subprocess.run(["kubectl", "apply", "-f", f"k8s/{self.environment}/"], check=True)
            logger.info("Kubernetes deployment completed successfully")
            return True
        except Exception as e:
            logger.error(f"Kubernetes deployment failed: {e}")
            return False

    def health_check(self) -> bool:
        """Check deployment health."""
        try:
            response = subprocess.run(
                ["curl", "-s", "http://localhost:8000/health"], capture_output=True, text=True
            )

            if response.returncode == 0:
                health = json.loads(response.stdout)
                return health.get("status") == "healthy"
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def rollback(self) -> bool:
        """Rollback to previous deployment."""
        try:
            logger.info("Rolling back deployment...")
            subprocess.run(["docker-compose", "down"], check=True)
            logger.info("Rollback completed")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def deploy_worker_node(self, worker_ip: str, redis_url: str) -> bool:
        """Deploy distributed worker node onto remote cloud egress machine."""
        try:
            logger.info(f"Deploying worker node to {worker_ip}...")
            cmd = [
                "ssh",
                f"root@{worker_ip}",
                f"docker run -d --name secagent-worker -e REDIS_URL={redis_url} ghcr.io/gl1tch0x1/cog-ai:latest secagent --worker",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Worker node deployment failed: {e}")
            return False
