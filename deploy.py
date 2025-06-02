#!/usr/bin/env python3
"""
Deployment and testing script for the onboarding call agent system.
"""

import os
import sys
import subprocess
import time
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentManager:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.env_file = self.project_root / ".env"
        
    def check_prerequisites(self):
        """Check if all prerequisites are met."""
        logger.info("Checking prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker not found")
            logger.info(f"✓ Docker: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"✗ Docker check failed: {e}")
            return False
            
        # Check Docker Compose
        try:
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker Compose not found")
            logger.info(f"✓ Docker Compose: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"✗ Docker Compose check failed: {e}")
            return False
            
        # Check .env file
        if not self.env_file.exists():
            logger.error("✗ .env file not found. Please copy .env.example to .env and configure it.")
            return False
        logger.info("✓ .env file found")
        
        return True
    
    def validate_environment(self):
        """Validate environment variables."""
        logger.info("Validating environment variables...")
        
        required_vars = [
            "LIVEKIT_URL",
            "LIVEKIT_API_KEY", 
            "LIVEKIT_API_SECRET",
            "GROQ_API_KEY",
            "POSTGRES_PASSWORD",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_PHONE_NUMBER",
            "WEBHOOK_BASE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.strip() == "":
                missing_vars.append(var)
            else:
                # Mask sensitive values in logs
                if "KEY" in var or "SECRET" in var or "TOKEN" in var or "PASSWORD" in var:
                    logger.info(f"✓ {var}: {'*' * 8}")
                else:
                    logger.info(f"✓ {var}: {value}")
        
        if missing_vars:
            logger.error(f"✗ Missing environment variables: {', '.join(missing_vars)}")
            return False
            
        return True
    
    def build_services(self):
        """Build Docker services."""
        logger.info("Building Docker services...")
        
        try:
            result = subprocess.run(
                ["docker-compose", "build", "--no-cache"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Build failed: {result.stderr}")
                return False
                
            logger.info("✓ Services built successfully")
            return True
            
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False
    
    def start_services(self):
        """Start all services."""
        logger.info("Starting services...")
        
        try:
            # Start database and redis first
            subprocess.run(
                ["docker-compose", "up", "-d", "db", "redis"],
                cwd=self.project_root,
                check=True
            )
            
            # Wait for database to be ready
            logger.info("Waiting for database to be ready...")
            time.sleep(10)
            
            # Start remaining services
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.project_root,
                check=True
            )
            
            logger.info("✓ Services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            return False
    
    def run_migrations(self):
        """Run database migrations."""
        logger.info("Running database migrations...")
        
        try:
            result = subprocess.run(
                ["docker-compose", "exec", "-T", "agent", "alembic", "upgrade", "head"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Migration failed: {result.stderr}")
                return False
                
            logger.info("✓ Database migrations completed")
            return True
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return False
    
    def health_check(self):
        """Perform health checks on all services."""
        logger.info("Performing health checks...")
        
        services = ["db", "redis", "agent", "webhook"]
        
        for service in services:
            try:
                result = subprocess.run(
                    ["docker-compose", "exec", "-T", service, "echo", "healthy"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info(f"✓ {service} service is healthy")
                else:
                    logger.warning(f"⚠ {service} service may have issues")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"✗ {service} service health check timed out")
            except Exception as e:
                logger.error(f"✗ {service} service health check failed: {e}")
    
    def test_database_connection(self):
        """Test database connectivity."""
        logger.info("Testing database connection...")
        
        try:
            result = subprocess.run([
                "docker-compose", "exec", "-T", "agent", "python", "-c",
                "from database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().health_check())"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ Database connection successful")
                return True
            else:
                logger.error(f"✗ Database connection failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database test error: {e}")
            return False
    
    def show_status(self):
        """Show status of all services."""
        logger.info("Service status:")
        
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
    
    def show_logs(self, service=None, follow=False):
        """Show logs for services."""
        cmd = ["docker-compose", "logs"]
        
        if follow:
            cmd.append("-f")
            
        if service:
            cmd.append(service)
            
        try:
            subprocess.run(cmd, cwd=self.project_root)
        except KeyboardInterrupt:
            logger.info("Log viewing stopped")
    
    def stop_services(self):
        """Stop all services."""
        logger.info("Stopping services...")
        
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=self.project_root,
                check=True
            )
            logger.info("✓ Services stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop services: {e}")
    
    def cleanup(self):
        """Clean up Docker resources."""
        logger.info("Cleaning up Docker resources...")
        
        try:
            subprocess.run(
                ["docker-compose", "down", "-v", "--remove-orphans"],
                cwd=self.project_root,
                check=True
            )
            logger.info("✓ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

def main():
    """Main deployment script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Onboarding Call Agent Deployment Manager")
    parser.add_argument("action", choices=[
        "check", "build", "start", "migrate", "health", "status", 
        "logs", "stop", "cleanup", "deploy"
    ], help="Action to perform")
    parser.add_argument("--service", help="Specific service for logs")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
    
    manager = DeploymentManager()
    
    if args.action == "check":
        success = manager.check_prerequisites() and manager.validate_environment()
        sys.exit(0 if success else 1)
        
    elif args.action == "build":
        success = manager.build_services()
        sys.exit(0 if success else 1)
        
    elif args.action == "start":
        success = manager.start_services()
        sys.exit(0 if success else 1)
        
    elif args.action == "migrate":
        success = manager.run_migrations()
        sys.exit(0 if success else 1)
        
    elif args.action == "health":
        manager.health_check()
        manager.test_database_connection()
        
    elif args.action == "status":
        manager.show_status()
        
    elif args.action == "logs":
        manager.show_logs(args.service, args.follow)
        
    elif args.action == "stop":
        manager.stop_services()
        
    elif args.action == "cleanup":
        manager.cleanup()
        
    elif args.action == "deploy":
        # Full deployment workflow
        steps = [
            ("Checking prerequisites", manager.check_prerequisites),
            ("Validating environment", manager.validate_environment),
            ("Building services", manager.build_services),
            ("Starting services", manager.start_services),
            ("Running migrations", manager.run_migrations),
            ("Health check", lambda: (manager.health_check(), manager.test_database_connection())[1])
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Deployment failed at step: {step_name}")
                sys.exit(1)
        
        logger.info("🎉 Deployment completed successfully!")
        logger.info("You can now start calling sessions with:")
        logger.info("  docker-compose exec agent python call_manager.py")
        logger.info("")
        logger.info("Access the admin panel at: http://localhost:3000/admin")
        logger.info("Monitor logs with: python deploy.py logs -f")

if __name__ == "__main__":
    main()
