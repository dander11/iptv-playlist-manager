# Release Notes

## v1.1.2 - Critical Frontend Fix (September 2, 2025)

### 🚨 CRITICAL BUG FIX
**Fixed static file path mismatch causing frontend CSS/JS 404 errors**

#### Problem Resolved
- Frontend HTML was loading but CSS and JavaScript assets were returning 404 errors
- Application appeared as blank/unstyled page making it completely unusable
- Users could access the app but saw no styling or functionality

#### Technical Fix
- **Enhanced React build detection**: Now properly detects nested `static/static/` directory structure
- **Correct static file mounting**: Mount `static/static` directory to `/static` endpoint
- **Robust fallback validation**: Detects CSS/JS files even if directory structure varies
- **Comprehensive logging**: Shows exact static mounting during startup

#### Impact
✅ **Frontend now fully functional** - CSS styling and JavaScript work correctly  
✅ **Cross-device compatibility** - Works from any IP address (192.168.x.x, etc.)  
✅ **Production ready** - No more blank pages or 404 errors  
✅ **Enhanced debugging** - Better troubleshooting capabilities  

### Container Updates
- **Latest image**: `ghcr.io/dander11/iptv-playlist-manager:latest`
- **Versioned image**: `ghcr.io/dander11/iptv-playlist-manager:v1.1.2`
- **Multi-architecture**: AMD64 and ARM64 support

### Upgrade Instructions
```bash
# Pull the latest fixed image
docker pull ghcr.io/dander11/iptv-playlist-manager:latest

# Or use the specific version
docker pull ghcr.io/dander11/iptv-playlist-manager:v1.1.2

# Restart your container to apply the fix
docker-compose down && docker-compose up -d
```

### Validation
After upgrading, the frontend should:
- Load with proper CSS styling
- Have working JavaScript functionality  
- Show no 404 errors in browser console
- Be fully functional from any device

---

## v1.1.1 - Database & API Enhancements

### Fixed Issues
✅ Database initialization permission issues  
✅ Enhanced API direct access capabilities  
✅ Improved frontend HTML serving  

---

## v1.1.0 - CORS Configuration Fix

### Fixed Issues  
✅ Critical CORS origins parsing error preventing startup  
✅ Enhanced environment variable validation  
✅ Improved error handling and logging  

---

## v1.0.1 - Initial Release

### Features
✅ Complete IPTV playlist management system  
✅ FastAPI backend with React frontend  
✅ Multi-architecture Docker support  
✅ Automated GitHub Actions CI/CD  

---

**Current Release**: v1.1.2 (Latest)  
**Container**: `ghcr.io/dander11/iptv-playlist-manager:latest`  
**Status**: Production Ready ✅
