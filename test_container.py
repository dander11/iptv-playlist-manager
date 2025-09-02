#!/usr/bin/env python3
"""
Container validation test suite
Run this to validate that the IPTV Playlist Manager container is working correctly
"""

import requests
import sys
import time
import json
from urllib.parse import urljoin

def test_container_health(base_url="http://localhost:8000"):
    """Test container health and functionality"""
    print(f"🔍 Testing IPTV Playlist Manager at {base_url}")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Basic health check
    tests_total += 1
    print("1. Testing basic health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            tests_passed += 1
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: API root endpoint
    tests_total += 1
    print("2. Testing API root endpoint...")
    try:
        response = requests.get(f"{base_url}/api", timeout=10)
        if response.status_code == 200 and "endpoints" in response.json():
            print("   ✅ API root accessible")
            tests_passed += 1
        else:
            print(f"   ❌ API root failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API root error: {e}")
    
    # Test 3: API documentation
    tests_total += 1
    print("3. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("   ✅ API docs accessible")
            tests_passed += 1
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API docs error: {e}")
    
    # Test 4: Frontend health check
    tests_total += 1
    print("4. Testing frontend health check...")
    try:
        response = requests.get(f"{base_url}/api/health/frontend", timeout=10)
        if response.status_code == 200:
            frontend_data = response.json()
            if frontend_data.get("frontend_available"):
                print("   ✅ Frontend health check passed")
                tests_passed += 1
                
                # Show detailed frontend status
                print(f"      Frontend available: {frontend_data.get('frontend_available')}")
                print(f"      Assets found: {frontend_data.get('assets_found', 0)}")
                print(f"      Asset references valid: {frontend_data.get('asset_references_valid')}")
                
                if frontend_data.get("issues"):
                    print("      Issues found:")
                    for issue in frontend_data.get("issues", []):
                        print(f"        - {issue}")
            else:
                print("   ⚠️ Frontend available but has issues")
                for issue in frontend_data.get("issues", []):
                    print(f"      - {issue}")
        else:
            print(f"   ❌ Frontend health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend health check error: {e}")
    
    # Test 5: Frontend HTML loading
    tests_total += 1
    print("5. Testing frontend HTML loading...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            content = response.text
            if "<html" in content.lower() and "iptv" in content.lower():
                print("   ✅ Frontend HTML loads correctly")
                tests_passed += 1
            else:
                print("   ⚠️ Frontend loads but content seems incorrect")
        else:
            print(f"   ❌ Frontend HTML failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend HTML error: {e}")
    
    # Test 6: Static asset accessibility
    tests_total += 1
    print("6. Testing static asset accessibility...")
    try:
        # Get frontend health info to see what assets are available
        response = requests.get(f"{base_url}/api/health/frontend", timeout=10)
        if response.status_code == 200:
            frontend_data = response.json()
            
            if frontend_data.get("frontend_available") and frontend_data.get("assets_found", 0) > 0:
                # Try to access the static mount path directly
                static_paths_to_test = [
                    "/static/",
                    "/static/css/",
                    "/static/js/"
                ]
                
                static_accessible = False
                for path in static_paths_to_test:
                    try:
                        response = requests.get(f"{base_url}{path}", timeout=5)
                        # For static files, we expect either:
                        # 200 (file served), 403 (directory listing disabled), or 404 (path structure issue)
                        if response.status_code in [200, 403]:
                            print(f"   ✅ Static path accessible: {path} (status: {response.status_code})")
                            static_accessible = True
                            break
                        elif response.status_code == 404:
                            print(f"   ❌ Static path not found: {path}")
                        else:
                            print(f"   ⚠️ Static path returned: {path} (status: {response.status_code})")
                    except Exception as e:
                        print(f"   ❌ Error testing {path}: {e}")
                
                # Also try to access a specific asset if we know the structure
                if not static_accessible:
                    # Try some common React build file patterns
                    asset_patterns = [
                        "/static/static/css/",
                        "/static/static/js/",
                        "/manifest.json",
                        "/favicon.ico"
                    ]
                    
                    for pattern in asset_patterns:
                        try:
                            response = requests.get(f"{base_url}{pattern}", timeout=5)
                            if response.status_code in [200, 403]:
                                print(f"   ✅ Found accessible asset path: {pattern}")
                                static_accessible = True
                                break
                        except:
                            continue
                
                if static_accessible:
                    tests_passed += 1
                else:
                    print("   ❌ No static asset paths accessible - check FastAPI static mount configuration")
            else:
                print("   ⚠️ No frontend assets reported by health check")
        else:
            print(f"   ❌ Could not get frontend health info: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Static asset test error: {e}")
    
    # Summary
    print("=" * 60)
    print(f"🎯 Test Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! Container is working correctly.")
        return True
    elif tests_passed >= 3:
        print("⚠️ Container is partially functional but has issues.")
        return False
    else:
        print("❌ Container has critical issues and may not be functional.")
        return False


def main():
    """Main test function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("🧪 IPTV Playlist Manager Container Test Suite")
    print(f"Target: {base_url}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Wait a moment for container to fully start
    print("⏳ Waiting 5 seconds for container to fully initialize...")
    time.sleep(5)
    
    # Run tests
    success = test_container_health(base_url)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
