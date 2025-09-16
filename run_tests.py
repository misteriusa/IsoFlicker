#!/usr/bin/env python3
"""
Test runner for IsoFlicker Pro
"""
import sys
import os
import subprocess

def run_tests():
    """Run all tests using pytest"""
    try:
        # Run pytest on the tests directory
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests", "-v"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)