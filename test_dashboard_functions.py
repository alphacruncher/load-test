#!/usr/bin/env python3
"""
Quick test to verify dashboard functions work correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import dashboard functions
from dashboard import (
    get_database_config,
    get_database_connection,
    test_database_connection,
)


def test_dashboard_functions():
    print("🧪 Testing dashboard functions...")

    # Test config loading
    print("Testing configuration loading...")
    config = get_database_config()
    if config:
        print(f"✓ Config loaded successfully, host: {config['host']}")
    else:
        print("❌ Failed to load config")
        return False

    # Test connection manager
    print("Testing connection manager...")
    with get_database_connection() as conn:
        if conn:
            print("✓ Connection manager works")
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            print(f"✓ Connection test query result: {result}")
        else:
            print("❌ Connection manager failed")
            return False

    # Test connection test function
    print("Testing connection test function...")
    if test_database_connection():
        print("✓ Connection test function works")
    else:
        print("❌ Connection test function failed")
        return False

    print("🎉 All dashboard functions work correctly!")
    return True


if __name__ == "__main__":
    test_dashboard_functions()
