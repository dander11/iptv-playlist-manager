# Container Troubleshooting Guide

## Database Issues

### SQLite Database Initialization Problems

The most common startup issue is related to SQLite database file creation. Here's how to diagnose and fix:

#### Quick Diagnosis

1. **Check container logs**:
   ```bash
   docker logs your-container-name
   ```

2. **Look for these error patterns**:
   - `unable to open database file`
   - `Permission denied`
   - `Database directory is not writable`

#### Common Causes and Solutions

##### 1. Volume Mount Permissions

**Problem**: Host volume directory doesn't have proper permissions.

**Solution**:
```bash
# Create directory with proper permissions
mkdir -p ./volumes/iptv-manager
chmod 755 ./volumes/iptv-manager

# If running as specific user, set ownership
sudo chown 1000:1000 ./volumes/iptv-manager  # iptv user in container
```

##### 2. Database URL Configuration

**Problem**: Incorrect database URL format or path.

**Correct formats**:
```bash
# For volume mount to /app/data
DATABASE_URL=sqlite:///app/data/app.db

# For volume mount to custom path
DATABASE_URL=sqlite:////custom/path/app.db
```

##### 3. Container User Permissions

**Problem**: Container runs as non-root user but can't write to mounted volumes.

**Solutions**:

Option A - Run as root (less secure):
```yaml
user: "0:0"  # Run as root
```

Option B - Match host user ID:
```yaml
user: "1000:1000"  # Match your host user ID
```

Option C - Set volume permissions:
```bash
docker run ... --volume /host/path:/app/data:Z  # SELinux systems
```

#### Docker Compose Configuration Examples

##### Basic Configuration
```yaml
services:
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    container_name: iptv-playlist-manager
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/data/app.db
      - JWT_SECRET=your-secret-key-here
      - CORS_ORIGINS=*
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

##### Configuration with Explicit Permissions
```yaml
services:
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    container_name: iptv-playlist-manager
    restart: unless-stopped
    user: "1000:1000"  # Match your host user
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/data/app.db
      - JWT_SECRET=your-secret-key-here
      - CORS_ORIGINS=http://localhost:8000
    volumes:
      - ./data:/app/data:rw  # Explicit read-write
      - ./logs:/app/logs:rw
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

##### Rootless Configuration
```yaml
services:
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    container_name: iptv-playlist-manager
    restart: unless-stopped
    # Container runs as iptv user (UID 1000 by default)
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/data/app.db
      - JWT_SECRET=your-secret-key-here
    volumes:
      - ./data:/app/data
    # Ensure host directory has proper ownership
    # Run: sudo chown -R 1000:1000 ./data
```

#### Manual Directory Setup

```bash
# Create required directories
mkdir -p ./data ./logs

# Set permissions (option 1 - permissive)
chmod -R 777 ./data ./logs

# Set permissions (option 2 - secure, match container user)
sudo chown -R 1000:1000 ./data ./logs
chmod -R 755 ./data ./logs

# Verify permissions
ls -la ./data ./logs
```

#### Debugging Container Environment

1. **Check if container starts without volumes**:
   ```bash
   docker run --rm -p 8000:8000 ghcr.io/dander11/iptv-playlist-manager:latest
   ```

2. **Run container interactively for debugging**:
   ```bash
   docker run -it --rm \
     --entrypoint /bin/bash \
     -v $(pwd)/data:/app/data \
     ghcr.io/dander11/iptv-playlist-manager:latest
   ```

3. **Inside container, check**:
   ```bash
   # Check user
   whoami
   id
   
   # Check directories
   ls -la /app/
   ls -la /app/data/
   
   # Check permissions
   touch /app/data/test.txt
   
   # Test database creation
   python -c "
   import sqlite3
   conn = sqlite3.connect('/app/data/test.db')
   conn.close()
   print('Database creation successful')
   "
   ```

#### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///app/data/iptv.db` | Database connection string |
| `JWT_SECRET` | Auto-generated | JWT signing secret |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `DEBUG` | `false` | Enable debug logging |

#### Container Health Check

The container includes a health check at `/health`. You can test it:

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response
healthy
```

If health check fails, check:
1. Application logs for startup errors
2. Port binding (8000 internal, mapped to host port)
3. Database connectivity

## Getting Help

If you continue to experience issues:

1. **Collect information**:
   ```bash
   # Container logs
   docker logs container-name > container-logs.txt
   
   # Host system info
   ls -la ./data/ > directory-info.txt
   docker version > docker-info.txt
   ```

2. **Try minimal configuration**:
   ```bash
   # Test with no volume mounts
   docker run --rm -p 8000:8000 ghcr.io/dander11/iptv-playlist-manager:latest
   ```

3. **Check GitHub issues**: Look for similar problems in the repository issues.

4. **Create detailed bug report** including:
   - Docker version
   - Host OS
   - Complete docker-compose.yml
   - Container logs
   - Directory permissions (`ls -la`)
