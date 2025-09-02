# 🚀 URGENT UPDATE AVAILABLE - v1.1.2

## 🚨 Critical Fix Released for Frontend Issues

**If you're experiencing blank/broken frontend pages, update immediately!**

### What Was Fixed
- **Frontend CSS/JS 404 Errors**: Static assets now load correctly
- **Blank Page Issue**: Frontend now displays with proper styling
- **Cross-Device Access**: Works from any IP address (not just localhost)
- **Production Usability**: Application fully functional for end users

### Quick Update Instructions

#### Option 1: Update Existing Container
```bash
# Pull the latest fixed image
docker pull ghcr.io/dander11/iptv-playlist-manager:latest

# Restart your container
docker-compose down
docker-compose up -d
```

#### Option 2: Use Versioned Image
```yaml
# In your docker-compose.yml, update to:
services:
  iptv-playlist-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:v1.1.2
```

### Verification
After updating, your frontend should:
- ✅ Load with proper CSS styling (no more blank pages)
- ✅ Have working buttons and JavaScript functionality
- ✅ Show no 404 errors in browser console (F12 → Console)
- ✅ Work from any device on your network

### Container Availability
- **Latest**: `ghcr.io/dander11/iptv-playlist-manager:latest` 
- **Versioned**: `ghcr.io/dander11/iptv-playlist-manager:v1.1.2`
- **Architecture**: AMD64 and ARM64 supported

### Release Timeline
- **v1.1.0**: Fixed CORS configuration bugs
- **v1.1.1**: Fixed database initialization issues  
- **v1.1.2**: 🚨 **CRITICAL** - Fixed frontend static file serving (UPDATE NOW)

This update resolves the critical frontend connectivity issue that made the application unusable. Users should update immediately to restore full functionality.

**Need Help?** Check the troubleshooting endpoints after updating:
- Health check: `http://your-ip:8001/health`
- Frontend status: `http://your-ip:8001/api/health/frontend`
- Debug info: `http://your-ip:8001/api/debug/static`
