#!/usr/bin/env python3
"""
Quick test script to verify database connection works
"""

import json
import psycopg2
import os
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("connection_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def test_connection():
    print("🔍 Testing database connection...")
    logger.info("Starting connection test")

    # Load config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        db_config = config["database"]
        print(f"✓ Config loaded - connecting to {db_config['host']}")
        logger.info(f"Config loaded successfully, host: {db_config['host']}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        logger.error(f"Failed to load config: {e}")
        return False

    # Try to get password from secrets file
    password = None
    try:
        # Try to parse secrets.toml manually (simple approach)
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                if "db_password" in line and "=" in line:
                    password = line.split("=")[1].strip().strip('"').strip("'")
                    break
        print("✓ Password found in secrets file")
        logger.info("Password loaded from secrets file")
    except Exception as e:
        print(f"⚠️ Could not read secrets file: {e}")
        logger.warning(f"Could not read secrets file: {e}")

    # Fallback to environment variable
    if not password:
        password = os.environ.get("DB_PASSWORD")
        if password:
            print("✓ Password found in environment variable")
            logger.info("Password loaded from environment variable")

    if not password:
        print("❌ No password found in secrets file or environment variable")
        logger.error("No password available from any source")
        return False

    # Test connection
    try:
        logger.info(f"Attempting to connect to {db_config['host']}:{db_config['port']}")
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=password,
        )
        logger.info("Connection established successfully")

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM load_test_results")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        print(f"✅ Connection successful! Found {count} load test results in database.")
        logger.info(f"Database test successful, found {count} records")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        logger.error(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
