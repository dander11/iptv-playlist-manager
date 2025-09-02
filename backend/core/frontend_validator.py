"""
Frontend asset validation and testing utilities
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def validate_frontend_assets() -> Dict[str, any]:
    """Validate that frontend assets are properly accessible"""
    validation_results = {
        "frontend_available": False,
        "static_directory_exists": False,
        "index_html_exists": False,
        "assets_found": [],
        "static_mount_path": None,
        "issues": [],
        "recommendations": []
    }
    
    # Check if static directory exists
    static_dir = Path("static")
    if static_dir.exists():
        validation_results["static_directory_exists"] = True
        logger.info(f"Static directory found: {static_dir.absolute()}")
    else:
        validation_results["issues"].append("Static directory does not exist")
        return validation_results
    
    # Check for index.html
    index_html = static_dir / "index.html"
    if index_html.exists():
        validation_results["index_html_exists"] = True
        logger.info(f"Index.html found: {index_html.absolute()}")
    else:
        validation_results["issues"].append("index.html not found in static directory")
    
    # Check for React build structure
    react_static = static_dir / "static"
    regular_static = static_dir
    
    if react_static.exists():
        # React build structure with nested static directory
        validation_results["static_mount_path"] = "static/static"
        logger.info("Detected React build structure with nested static directory")
        
        # Check for typical React build assets
        css_dir = react_static / "css"
        js_dir = react_static / "js"
        
        if css_dir.exists():
            css_files = list(css_dir.glob("*.css"))
            validation_results["assets_found"].extend([f"css/{f.name}" for f in css_files])
            logger.info(f"Found CSS files: {[f.name for f in css_files]}")
        
        if js_dir.exists():
            js_files = list(js_dir.glob("*.js"))
            validation_results["assets_found"].extend([f"js/{f.name}" for f in js_files])
            logger.info(f"Found JS files: {[f.name for f in js_files]}")
            
        if css_files or js_files:
            validation_results["frontend_available"] = True
    
    else:
        # Regular static directory structure
        validation_results["static_mount_path"] = "static"
        logger.info("Regular static directory structure")
        
        # Check for assets directly in static
        css_files = list(regular_static.glob("**/*.css"))
        js_files = list(regular_static.glob("**/*.js"))
        
        if css_files or js_files:
            validation_results["frontend_available"] = True
            validation_results["assets_found"].extend([f.name for f in css_files + js_files])
    
    # Generate recommendations
    if not validation_results["frontend_available"]:
        validation_results["recommendations"].append(
            "No frontend assets found. Check if React build completed successfully."
        )
    
    if validation_results["static_mount_path"] == "static/static":
        validation_results["recommendations"].append(
            "Using nested static directory structure. Ensure FastAPI mount path is configured correctly."
        )
    
    return validation_results


def validate_index_html_asset_references() -> Dict[str, any]:
    """Validate that index.html references match available assets"""
    validation_results = {
        "index_html_readable": False,
        "css_references": [],
        "js_references": [],
        "asset_path_pattern": None,
        "issues": [],
        "all_references_valid": True
    }
    
    index_path = Path("static/index.html")
    if not index_path.exists():
        validation_results["issues"].append("index.html not found")
        return validation_results
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        validation_results["index_html_readable"] = True
        
        # Extract CSS and JS references
        import re
        
        # Find CSS links
        css_pattern = r'<link[^>]*href=["\']([^"\']*\.css)["\'][^>]*>'
        css_matches = re.findall(css_pattern, html_content)
        validation_results["css_references"] = css_matches
        
        # Find JS script sources  
        js_pattern = r'<script[^>]*src=["\']([^"\']*\.js)["\'][^>]*>'
        js_matches = re.findall(js_pattern, html_content)
        validation_results["js_references"] = js_matches
        
        # Determine asset path pattern
        all_refs = css_matches + js_matches
        if all_refs:
            first_ref = all_refs[0]
            if first_ref.startswith('/static/'):
                validation_results["asset_path_pattern"] = "/static/"
            elif first_ref.startswith('./static/'):
                validation_results["asset_path_pattern"] = "./static/"
            else:
                validation_results["asset_path_pattern"] = "unknown"
        
        # Check if referenced files actually exist
        for ref in all_refs:
            # Skip external CDN references
            if ref.startswith(('http://', 'https://', '//')):
                continue
                
            # Convert reference to file path
            if ref.startswith('/static/'):
                file_path = Path("static") / ref[8:]  # Remove /static/ prefix
            elif ref.startswith('./static/'):
                file_path = Path("static") / ref[9:]  # Remove ./static/ prefix
            else:
                file_path = Path("static") / ref
            
            # Check both regular and nested locations
            regular_path = Path("static") / ref.lstrip('./')
            nested_path = Path("static/static") / ref.replace('/static/', '').replace('./static/', '')
            
            if not (regular_path.exists() or nested_path.exists()):
                validation_results["issues"].append(f"Referenced asset not found: {ref}")
                validation_results["all_references_valid"] = False
        
        logger.info(f"Found {len(css_matches)} CSS and {len(js_matches)} JS references")
        
    except Exception as e:
        validation_results["issues"].append(f"Failed to read index.html: {e}")
    
    return validation_results


def log_frontend_validation():
    """Log comprehensive frontend validation results"""
    logger.info("=== Frontend Asset Validation ===")
    
    # Validate assets
    asset_results = validate_frontend_assets()
    logger.info(f"Frontend available: {asset_results['frontend_available']}")
    logger.info(f"Static mount path: {asset_results['static_mount_path']}")
    logger.info(f"Assets found: {len(asset_results['assets_found'])}")
    
    for issue in asset_results['issues']:
        logger.warning(f"Asset issue: {issue}")
    
    for rec in asset_results['recommendations']:
        logger.info(f"Recommendation: {rec}")
    
    # Validate HTML references
    html_results = validate_index_html_asset_references()
    logger.info(f"Index.html readable: {html_results['index_html_readable']}")
    logger.info(f"Asset references valid: {html_results['all_references_valid']}")
    logger.info(f"Asset path pattern: {html_results['asset_path_pattern']}")
    
    for issue in html_results['issues']:
        logger.warning(f"HTML reference issue: {issue}")
    
    logger.info("=== Frontend validation completed ===")
    
    return {
        "assets": asset_results,
        "html_references": html_results,
        "overall_status": asset_results["frontend_available"] and html_results["all_references_valid"]
    }


def test_static_file_access():
    """Test that static files can be accessed through FastAPI"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test accessing a known static file
        asset_results = validate_frontend_assets()
        if asset_results["assets_found"]:
            # Try to access the first found asset
            first_asset = asset_results["assets_found"][0]
            test_url = f"/static/{first_asset}"
            
            response = client.get(test_url)
            logger.info(f"Static file test {test_url}: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Static file serving is working correctly")
                return True
            else:
                logger.error(f"❌ Static file serving failed: {response.status_code}")
                return False
        else:
            logger.warning("No assets found to test")
            return False
            
    except Exception as e:
        logger.error(f"Static file access test failed: {e}")
        return False


if __name__ == "__main__":
    # Run validation
    logging.basicConfig(level=logging.INFO)
    results = log_frontend_validation()
    
    if results["overall_status"]:
        print("✅ Frontend validation passed")
    else:
        print("❌ Frontend validation failed")
        exit(1)
