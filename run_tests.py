#!/usr/bin/env python3
"""
Simple test runner for the hiking trip organizer.
"""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run all tests."""
    print("🧪 Running Hiking Trip Organizer Tests")
    print("=" * 50)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
    
    # Run tests
    test_dir = Path(__file__).parent / "tests"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir),
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
