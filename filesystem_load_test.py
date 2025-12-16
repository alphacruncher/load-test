#!/usr/bin/env python3
"""
Filesystem Load Testing Script

This script performs specific workload tests on a filesystem path to mimic
real-world operations and measure their performance over time.
"""

import os
import sys
import time
import json
import logging
import subprocess
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseLogger:
    """Handles PostgreSQL database operations for logging test results."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None

    def connect(self):
        """Establish database connection."""
        try:
            db_config = self.config["database"]
            # Password should be stored in .pgpass file for security
            self.connection = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database"],
                user=db_config["user"],
            )
            logging.info("Connected to PostgreSQL database")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def log_test_result(
        self,
        setup_id: str,
        test_name: str,
        start_time: datetime,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Log test execution results to database."""
        if not self.connection:
            logging.warning("No database connection available")
            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO load_test_results 
                    (setup_id, test_name, start_time, execution_time_seconds, success, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        setup_id,
                        test_name,
                        start_time,
                        execution_time,
                        success,
                        error_message,
                    ),
                )
            self.connection.commit()
            logging.debug(
                f"Logged test result: {setup_id}/{test_name}, {execution_time:.2f}s"
            )
        except Exception as e:
            logging.error(f"Failed to log test result: {e}")
            self.connection.rollback()


class FilesystemLoadTester:
    """Main class for orchestrating filesystem load tests."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.db_logger = DatabaseLogger(self.config)
        self.target_path = Path(self.config["target_path"])
        self.setup_completed = set()  # Track which tests have completed setup
        self.setup_logging()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logging.error(f"Configuration file {self.config_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)

    def setup_logging(self):
        """Configure logging based on config settings."""
        log_level = getattr(logging, self.config.get("log_level", "INFO").upper())
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.config.get("log_file", "load_test.log")),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def ensure_target_path(self):
        """Ensure target path exists and is writable."""
        try:
            self.target_path.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self.target_path / f"test_write_{int(time.time())}"
            test_file.write_text("test")
            test_file.unlink()
            logging.info(f"Target path verified: {self.target_path}")
        except Exception as e:
            logging.error(f"Target path not accessible: {e}")
            raise

    def cleanup_test_artifacts(self):
        """Clean up test artifacts from previous runs."""
        try:
            # Remove any leftover test directories
            for item in self.target_path.iterdir():
                if item.is_dir() and (
                    item.name.startswith("test_repo_")
                    or item.name.startswith("test_venv_")
                ):
                    shutil.rmtree(item)
                    logging.debug(f"Cleaned up artifact: {item}")
        except Exception as e:
            logging.warning(f"Error during cleanup: {e}")

    def execute_test_case(self, test_name: str) -> None:
        """Execute a single test case and log results."""
        start_time = datetime.now(timezone.utc)
        success = False
        error_message = None

        try:
            logging.info(f"Starting test: {test_name}")

            # Get test definition
            if test_name not in self.config["test_definitions"]:
                raise ValueError(
                    f"Test case '{test_name}' not found in test_definitions"
                )

            test_config = self.config["test_definitions"][test_name]
            test_type = test_config["type"]

            # Check if setup is required and not yet completed
            if (
                test_config.get("setup_required", False)
                and test_name not in self.setup_completed
            ):
                logging.info(f"Running setup for test: {test_name}")
                self.run_test_setup(test_name, test_config)
                self.setup_completed.add(test_name)
                logging.info(f"Setup completed for test: {test_name}")
            if test_type == "git_clone":
                execution_time = self.test_git_clone(test_config)
                execution_time = self.test_virtualenv_install(test_config)
                execution_time = self.test_pandas_load(test_config)
                execution_time = self.test_virtualenv_install(test_config)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            success = True
            logging.info(f"Test {test_name} completed in {execution_time:.2f} seconds")

        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            error_message = str(e)
            logging.error(f"Test {test_name} failed: {e}")

        # Log to database
        self.db_logger.log_test_result(
            self.config["setup_id"],
            test_name,
            start_time,
            execution_time,
            success,
            error_message,
        )

    def test_git_clone(self, test_config: Dict[str, Any]) -> float:
        """Test case: Clone a repository to target path."""
        start_time = time.time()

        repo_url = test_config["repository_url"]
        clone_dir = self.target_path / f"test_repo_{int(time.time())}"

        try:
            # Execute git clone
            result = subprocess.run(
                ["git", "clone", repo_url, str(clone_dir)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")

            # Verify clone was successful
            if not (clone_dir / ".git").exists():
                raise RuntimeError("Repository was not properly cloned")

            return time.time() - start_time

        finally:
            # Cleanup: Remove cloned repository
            if clone_dir.exists():
                shutil.rmtree(clone_dir)

    def test_virtualenv_install(self, test_config: Dict[str, Any]) -> float:
        """Test case: Create virtualenv and install pandas."""
        start_time = time.time()

        venv_dir = self.target_path / f"test_venv_{int(time.time())}"

        try:
            # Create virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Virtual environment creation failed: {result.stderr}"
                )

            # Get pip executable path
            if os.name == "nt":  # Windows
                pip_path = venv_dir / "Scripts" / "pip.exe"
            else:  # Unix-like
                pip_path = venv_dir / "bin" / "pip"

            # Install packages
            packages = test_config["packages"]
            result = subprocess.run(
                [str(pip_path), "install"] + packages,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Package installation failed: {result.stderr}")

            return time.time() - start_time

        finally:
            # Cleanup: Remove virtual environment
            if venv_dir.exists():
                shutil.rmtree(venv_dir)

    def run_test_setup(self, test_name: str, test_config: Dict[str, Any]) -> None:
        """Run one-time setup for a test case."""
        test_type = test_config["type"]

        if test_type == "pandas_load":
            self.setup_pandas_load_test(test_name)
        else:
            logging.warning(f"No setup method defined for test type: {test_type}")

    def setup_pandas_load_test(self, test_name: str) -> None:
        """Setup for pandas load test - create persistent venv with pandas."""
        venv_dir = self.target_path / f"pandas_venv_{test_name}"

        # Remove existing venv if it exists
        if venv_dir.exists():
            shutil.rmtree(venv_dir)

        try:
            # Create virtual environment
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Virtual environment creation failed: {result.stderr}"
                )

            # Get pip executable path
            if os.name == "nt":  # Windows
                pip_path = venv_dir / "Scripts" / "pip.exe"
            else:  # Unix-like
                pip_path = venv_dir / "bin" / "pip"

            # Install pandas
            result = subprocess.run(
                [str(pip_path), "install", "pandas"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Pandas installation failed: {result.stderr}")

            logging.info(f"Setup completed: pandas venv at {venv_dir}")

        except Exception as e:
            # Clean up on failure
            if venv_dir.exists():
                shutil.rmtree(venv_dir)
            raise e

    def test_pandas_load(self, test_config: Dict[str, Any]) -> float:
        """Test case: Time pandas import in a fresh Python process."""
        test_name = None
        # Find the test name by looking up the config
        for name, config in self.config["test_definitions"].items():
            if config is test_config:
                test_name = name
                break

        if not test_name:
            raise RuntimeError("Could not determine test name for pandas_load test")

        venv_dir = self.target_path / f"pandas_venv_{test_name}"

        if not venv_dir.exists():
            raise RuntimeError(
                f"Pandas venv not found at {venv_dir}. Setup may have failed."
            )

        # Get python executable path
        if os.name == "nt":  # Windows
            python_path = venv_dir / "Scripts" / "python.exe"
        else:  # Unix-like
            python_path = venv_dir / "bin" / "python"

        # Time the pandas import in a fresh process
        start_time = time.time()

        result = subprocess.run(
            [str(python_path), "-c", "import pandas"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        execution_time = time.time() - start_time

        if result.returncode != 0:
            raise RuntimeError(f"Pandas import failed: {result.stderr}")

        return execution_time

    def run_test_loop(self):
        """Main test loop that runs indefinitely."""
        logging.info("Starting filesystem load test loop")

        # Connect to database
        self.db_logger.connect()

        try:
            while True:
                loop_start = time.time()
                logging.info("Starting new test loop iteration")

                # Run enabled tests
                for test_name in self.config["enabled_tests"]:
                    if test_name in self.config["test_definitions"]:
                        self.execute_test_case(test_name)
                    else:
                        logging.warning(f"Unknown test case: {test_name}")

                # Clean up any remaining artifacts
                self.cleanup_test_artifacts()

                # Wait for next iteration
                loop_duration = time.time() - loop_start
                wait_time = max(0, self.config["loop_interval_seconds"] - loop_duration)

                if wait_time > 0:
                    logging.info(
                        f"Waiting {wait_time:.1f} seconds until next iteration"
                    )
                    time.sleep(wait_time)
                else:
                    logging.warning("Test loop took longer than configured interval")

        except KeyboardInterrupt:
            logging.info("Received interrupt signal, stopping test loop")
        finally:
            self.db_logger.disconnect()

    def run(self):
        """Main entry point for running the load tester."""
        try:
            self.ensure_target_path()
            self.cleanup_test_artifacts()
            self.run_test_loop()
        except Exception as e:
            logging.error(f"Fatal error: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Filesystem Load Testing Script")
    parser.add_argument(
        "--config",
        "-c",
        default="config.json",
        help="Configuration file path (default: config.json)",
    )

    args = parser.parse_args()

    tester = FilesystemLoadTester(args.config)
    tester.run()


if __name__ == "__main__":
    main()
