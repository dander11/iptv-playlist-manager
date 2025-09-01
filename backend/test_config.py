#!/usr/bin/env python3
"""
Test script to validate the configuration parsing
This can be run to debug configuration issues
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_cors_config():
    """Test various CORS configuration formats"""
    
    # Test cases
    test_cases = [
        ("*", ["*"]),
        ("http://localhost:3000", ["http://localhost:3000"]),
        ("http://localhost:3000,http://localhost:8000", ["http://localhost:3000", "http://localhost:8000"]),
        ('["http://localhost:3000","http://localhost:8000"]', ["http://localhost:3000", "http://localhost:8000"]),
        ("  http://localhost:3000  ,  http://localhost:8000  ", ["http://localhost:3000", "http://localhost:8000"]),
        ("", ["*"]),  # Empty should default to wildcard
    ]
    
    print("Testing CORS configuration parsing...")
    
    for input_val, expected in test_cases:
        print(f"\nInput: '{input_val}'")
        print(f"Expected: {expected}")
        
        # Set environment variable
        if input_val:
            os.environ["CORS_ORIGINS"] = input_val
        else:
            os.environ.pop("CORS_ORIGINS", None)
        
        try:
            from core.config import Settings
            
            # Create fresh settings instance
            settings = Settings()
            result = settings.cors_origins
            
            print(f"Result: {result}")
            
            if result == expected:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Clean up environment
    os.environ.pop("CORS_ORIGINS", None)
    print("\n" + "="*50)


def test_full_settings():
    """Test loading full settings without errors"""
    print("Testing full settings loading...")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        
        print(f"✅ Settings loaded successfully!")
        print(f"  - App Name: {settings.app_name}")
        print(f"  - CORS Origins: {settings.cors_origins}")
        print(f"  - Database URL: {settings.database_url}")
        print(f"  - JWT Secret: {'*' * len(settings.jwt_secret_key)}")
        print(f"  - Debug Mode: {settings.debug}")
        
    except Exception as e:
        print(f"❌ ERROR loading settings: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_cors_config()
    test_full_settings()
