# IPTV Playlist Manager - Deployment Guide

## 🚀 Quick Start - Standalone Deployment

### Option 1: Clone and Build Locally

1. **Clone the repository:**
```bash
git clone git@github.com:dander11/iptv-playlist-manager.git
cd iptv-playlist-manager
```

2. **Configure environment (optional):**
```bash
cp .env.production .env
# Edit .env with your preferred settings
nano .env
```

3. **Deploy with Docker Compose:**
```bash
docker-compose -f docker-compose.standalone.yml up -d
```

4. **Access the application:**
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Unified Playlist: http://localhost:8000/playlist.m3u8

### Option 2: Use Pre-built Image (Coming Soon)

```bash
# Pull and run the pre-built image
docker run -d \
  --name iptv-playlist-manager \
  -p 8000:8000 \
  -v iptv_data:/app/data \
  -v iptv_logs:/app/logs \
  -e JWT_SECRET_KEY=your-secret-key \
  ghcr.io/dander11/iptv-playlist-manager:latest
```

## 🔧 Integration with Existing Docker Compose

### Step 1: Add to Your Existing Setup

Add this service to your existing `docker-compose.yml`:

```yaml
services:
  # ... your existing services ...
  
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    container_name: iptv-playlist-manager
    ports:
      - "8000:8000"  # Change port if needed
    environment:
      - JWT_SECRET_KEY=${IPTV_JWT_SECRET}
      - CORS_ORIGINS=*
      - VALIDATION_SCHEDULE=0 2 * * *
    volumes:
      - iptv_data:/app/data
      - iptv_logs:/app/logs
    restart: unless-stopped
    networks:
      - your_network  # Use your existing network

volumes:
  iptv_data:
  iptv_logs:
  # ... your existing volumes ...
```

### Step 2: Set Environment Variables

Add to your `.env` file:
```bash
IPTV_JWT_SECRET=your-super-secret-jwt-key-change-this
```

### Step 3: Deploy

```bash
docker-compose up -d iptv-manager
```

## 📊 Behind a Reverse Proxy

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name iptv.yourdomain.com;
    
    location / {
        proxy_pass http://iptv-manager:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Traefik Labels

```yaml
iptv-manager:
  # ... other config ...
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.iptv.rule=Host(\`iptv.yourdomain.com\`)"
    - "traefik.http.routers.iptv.tls=true"
    - "traefik.http.routers.iptv.tls.certresolver=letsencrypt"
    - "traefik.http.services.iptv.loadbalancer.server.port=8000"
```

## 🔒 Production Security

### 1. Change Default Secrets

```bash
# Generate a secure JWT secret
openssl rand -hex 32
```

### 2. Use Environment Variables

```bash
# In your .env file
JWT_SECRET_KEY=your-generated-secret-key-here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Network Security

```yaml
services:
  iptv-manager:
    # ... other config ...
    networks:
      - internal_network  # Don't expose to public if behind proxy

networks:
  internal_network:
    internal: true  # No external access
```

## 📁 Data Persistence

The application uses these persistent volumes:

- **`iptv_data`**: Database and application data
- **`iptv_logs`**: Application logs
- **`iptv_uploads`**: Uploaded playlist files

### Backup Strategy

```bash
# Backup data volume
docker run --rm -v iptv_data:/data -v $(pwd):/backup alpine tar czf /backup/iptv_backup_$(date +%Y%m%d).tar.gz -C /data .

# Restore data volume
docker run --rm -v iptv_data:/data -v $(pwd):/backup alpine tar xzf /backup/iptv_backup_YYYYMMDD.tar.gz -C /data
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description | Format Examples |
|----------|---------|-------------|-----------------|
| `JWT_SECRET_KEY` | - | **Required** Secret key for JWT tokens | `your-secret-key` |
| `DATABASE_URL` | `sqlite:///./data/iptv.db` | Database connection string | `sqlite:///./data/iptv.db`<br/>`postgresql://user:pass@db:5432/iptv` |
| `CORS_ORIGINS` | `*` | Allowed CORS origins | `*`<br/>`https://domain.com`<br/>`https://domain.com,https://api.domain.com`<br/>`["https://domain.com","https://api.domain.com"]` |
| `VALIDATION_SCHEDULE` | `0 2 * * *` | Cron schedule for validation | `0 2 * * *` (daily at 2 AM) |
| `MAX_PLAYLIST_SIZE` | `104857600` | Max file upload size (100MB) | `104857600` |
| `LOG_LEVEL` | `INFO` | Logging level | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `PORT` | `8000` | Internal port (don't change unless needed) | `8000` |

### CORS Configuration Details

The `CORS_ORIGINS` environment variable supports multiple formats for flexibility:

1. **Wildcard (allows all origins)**:
   ```bash
   CORS_ORIGINS=*
   ```

2. **Single origin**:
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

3. **Multiple origins (comma-separated)**:
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://api.yourdomain.com
   ```

4. **JSON array format**:
   ```bash
   CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
   ```

**Note**: If `CORS_ORIGINS` is not specified or is empty, it defaults to `*` (allow all origins).

### External Database Support

For production, consider using an external database:

```yaml
environment:
  - DATABASE_URL=postgresql://user:pass@db:5432/iptv
  # or
  - DATABASE_URL=mysql://user:pass@db:3306/iptv
```

## 🚀 Deployment Examples

### Docker Swarm

```yaml
version: '3.8'

services:
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
    secrets:
      - jwt_secret
    volumes:
      - iptv_data:/app/data
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

secrets:
  jwt_secret:
    external: true

volumes:
  iptv_data:
    driver: local
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iptv-playlist-manager
spec:
  replicas: 2
  selector:
    matchLabels:
      app: iptv-playlist-manager
  template:
    metadata:
      labels:
        app: iptv-playlist-manager
    spec:
      containers:
      - name: iptv-manager
        image: ghcr.io/dander11/iptv-playlist-manager:latest
        ports:
        - containerPort: 8000
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: iptv-secrets
              key: jwt-secret
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: iptv-data-pvc
```

## 📋 Health Checks & Monitoring

### Health Check Endpoint

- **URL**: `http://localhost:8000/health`
- **Response**: `{"status": "healthy", "service": "IPTV Playlist Manager"}`

### Monitoring Integration

```yaml
# Prometheus monitoring
labels:
  - "prometheus.io/scrape=true"
  - "prometheus.io/port=8000"
  - "prometheus.io/path=/metrics"
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port conflicts**: Change the port mapping: `"8080:8000"`
2. **Permission errors**: Ensure volumes have correct permissions
3. **Database locked**: Stop all containers and restart
4. **Memory issues**: Increase container memory limits

### CORS Configuration Issues

If you encounter CORS-related startup errors, try these solutions:

1. **Check CORS_ORIGINS format**:
   ```bash
   # Test the configuration parsing
   docker exec -it iptv-playlist-manager python test_config.py
   ```

2. **Use wildcard for development**:
   ```bash
   CORS_ORIGINS=*
   ```

3. **For production, specify exact domains**:
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **If using quotes in docker-compose.yml, escape properly**:
   ```yaml
   environment:
     - 'CORS_ORIGINS=["https://domain.com","https://api.domain.com"]'
   ```

### Configuration Validation

To debug configuration issues, you can run the configuration test:

```bash
# Enter the container
docker exec -it iptv-playlist-manager bash

# Run configuration test
python test_config.py

# Check current configuration
python -c "from core.config import get_settings; print(get_settings().cors_origins)"
```

### Logs

```bash
# View application logs
docker-compose logs iptv-manager

# Follow logs in real-time
docker-compose logs -f iptv-manager
```

### Container Shell Access

```bash
# Access container shell for debugging
docker exec -it iptv-playlist-manager sh
```

## 📖 API Usage

Once deployed, you can:

1. **Access Web UI**: http://localhost:8000
2. **Import playlists**: Upload files or add URLs
3. **Get unified playlist**: http://localhost:8000/playlist.m3u8
4. **API Documentation**: http://localhost:8000/docs

### Quick API Example

```bash
# Register user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "secure123"}'

# Login
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secure123"

# Add playlist (with token)
curl -X POST "http://localhost:8000/api/playlists/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Playlist", "source_url": "https://iptv-org.github.io/iptv/index.m3u"}'
```

This deployment guide provides everything needed to run IPTV Playlist Manager as a single container in any Docker environment! 🎉
