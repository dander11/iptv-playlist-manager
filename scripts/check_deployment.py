#!/usr/bin/env python3
"""
Simple deployment checker that validates the container functionality
without requiring local Docker installation.
"""

import requests
import time
import sys
from typing import Dict, Any
import json

# Container URL - this should be the public GitHub Container Registry URL
CONTAINER_URL = "ghcr.io/dander11/iptv-playlist-manager:latest"
DEPLOYED_URL = "http://localhost:8000"  # Update this with your actual deployment URL


def test_container_health() -> Dict[str, Any]:
    """Test container health without Docker by hitting deployed endpoints."""
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {},
        "summary": {"passed": 0, "failed": 0, "total": 0}
    }
    
    # Test 1: Basic health check
    try:
        response = requests.get(f"{DEPLOYED_URL}/health", timeout=10)
        results["tests"]["health_check"] = {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "details": f"Status: {response.status_code}, Response: {response.text[:200]}"
        }
    except Exception as e:
        results["tests"]["health_check"] = {
            "status": "FAIL",
            "details": f"Connection error: {str(e)}"
        }
    
    # Test 2: Frontend HTML loading
    try:
        response = requests.get(f"{DEPLOYED_URL}/", timeout=10)
        results["tests"]["frontend_html"] = {
            "status": "PASS" if response.status_code == 200 and "html" in response.headers.get("content-type", "").lower() else "FAIL",
            "details": f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}"
        }
    except Exception as e:
        results["tests"]["frontend_html"] = {
            "status": "FAIL",
            "details": f"Connection error: {str(e)}"
        }
    
    # Test 3: Frontend validation endpoint
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/health/frontend", timeout=10)
        results["tests"]["frontend_validation"] = {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "details": f"Status: {response.status_code}, Response: {response.text[:500]}"
        }
        
        if response.status_code == 200:
            data = response.json()
            if data.get("frontend_available") and data.get("all_references_valid"):
                results["tests"]["static_assets"] = {
                    "status": "PASS",
                    "details": f"Assets found: {len(data.get('assets_found', []))}, All references valid: True"
                }
            else:
                results["tests"]["static_assets"] = {
                    "status": "FAIL", 
                    "details": f"Frontend available: {data.get('frontend_available')}, Valid refs: {data.get('all_references_valid')}, Issues: {data.get('issues', [])}"
                }
    except Exception as e:
        results["tests"]["frontend_validation"] = {
            "status": "FAIL",
            "details": f"Connection error: {str(e)}"
        }
        results["tests"]["static_assets"] = {
            "status": "FAIL",
            "details": "Could not validate due to connection error"
        }
    
    # Test 4: API functionality
    try:
        response = requests.get(f"{DEPLOYED_URL}/api/", timeout=10)
        results["tests"]["api_access"] = {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "details": f"Status: {response.status_code}"
        }
    except Exception as e:
        results["tests"]["api_access"] = {
            "status": "FAIL",
            "details": f"Connection error: {str(e)}"
        }
    
    # Calculate summary
    for test_result in results["tests"].values():
        results["summary"]["total"] += 1
        if test_result["status"] == "PASS":
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
    
    return results


def print_results(results: Dict[str, Any]):
    """Print test results in a readable format."""
    print(f"\n=== Deployment Health Check - {results['timestamp']} ===")
    print(f"Container Image: {CONTAINER_URL}")
    print(f"Testing URL: {DEPLOYED_URL}")
    print()
    
    for test_name, test_result in results["tests"].items():
        status_icon = "✅" if test_result["status"] == "PASS" else "❌"
        print(f"{status_icon} {test_name.replace('_', ' ').title()}")
        print(f"   {test_result['details']}")
        print()
    
    summary = results["summary"]
    success_rate = (summary["passed"] / summary["total"]) * 100 if summary["total"] > 0 else 0
    
    print(f"=== Summary ===")
    print(f"Passed: {summary['passed']}/{summary['total']} ({success_rate:.1f}%)")
    
    if summary["failed"] == 0:
        print("🎉 All tests passed! Deployment is healthy.")
    else:
        print(f"⚠️  {summary['failed']} test(s) failed. Review the details above.")


def main():
    """Main function to run deployment checks."""
    if len(sys.argv) > 1:
        global DEPLOYED_URL
        DEPLOYED_URL = sys.argv[1]
        print(f"Testing custom URL: {DEPLOYED_URL}")
    
    print("Checking deployment health...")
    results = test_container_health()
    print_results(results)
    
    # Return appropriate exit code
    return 0 if results["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
