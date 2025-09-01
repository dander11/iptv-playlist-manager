# IPTV Playlist Manager - Production Deployment

## 🏗️ Production Setup Checklist

### Infrastructure Requirements

- [ ] Docker Engine 20.10+ or Podman 3.0+
- [ ] Docker Compose 1.29+ or Podman Compose
- [ ] Minimum 1GB RAM, 2GB recommended
- [ ] 10GB+ disk space for playlists and logs
- [ ] SSL certificate for HTTPS (recommended)
- [ ] Reverse proxy (nginx, Apache, Traefik)

### Security Checklist

- [ ] Generate secure JWT secret (32+ characters)
- [ ] Configure CORS origins for your domains
- [ ] Set up firewall rules
- [ ] Configure SSL/TLS termination
- [ ] Set up log rotation
- [ ] Regular security updates scheduled
- [ ] Database backups configured

### Network Architecture

```
Internet → Reverse Proxy → IPTV Manager Container
                ↓
           Docker Network
                ↓
        [Database] [Logs] [Data]
```

## 🔧 Advanced Configuration

### External PostgreSQL Database

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    environment:
      - DATABASE_URL=postgresql://iptv_user:secure_password@postgres:5432/iptv_db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
    networks:
      - iptv_network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=iptv_db
      - POSTGRES_USER=iptv_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - iptv_network

volumes:
  postgres_data:

networks:
  iptv_network:
    driver: bridge
```

### Redis Caching Layer

```yaml
services:
  iptv-manager:
    # ... existing config ...
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - iptv_network

volumes:
  redis_data:
```

### High Availability Setup

```yaml
version: '3.8'

services:
  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    environment:
      - DATABASE_URL=postgresql://iptv_user:${POSTGRES_PASSWORD}@postgres:5432/iptv_db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    networks:
      - iptv_network

  postgres:
    image: postgres:15-alpine
    deploy:
      placement:
        constraints: [node.role == manager]
    environment:
      - POSTGRES_DB=iptv_db
      - POSTGRES_USER=iptv_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - iptv_network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    deploy:
      placement:
        constraints: [node.role == manager]
    networks:
      - iptv_network

volumes:
  postgres_data:

networks:
  iptv_network:
    driver: overlay
    attachable: true
```

## 🌐 Reverse Proxy Configurations

### Nginx with SSL

```nginx
# /etc/nginx/sites-available/iptv
server {
    listen 80;
    server_name iptv.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name iptv.yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Large file uploads for playlists
    client_max_body_size 100M;

    location / {
        proxy_pass http://iptv-manager:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed for real-time features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Cache static files
    location /static/ {
        proxy_pass http://iptv-manager:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://iptv-manager:8000;
        access_log off;
    }
}
```

### Traefik v2 Configuration

```yaml
# docker-compose.traefik.yml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.letsencrypt.acme.tlschallenge=true
      - --certificatesresolvers.letsencrypt.acme.email=your-email@domain.com
      - --certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt
    networks:
      - traefik

  iptv-manager:
    image: ghcr.io/dander11/iptv-playlist-manager:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.iptv.rule=Host(`iptv.yourdomain.com`)"
      - "traefik.http.routers.iptv.entrypoints=websecure"
      - "traefik.http.routers.iptv.tls=true"
      - "traefik.http.routers.iptv.tls.certresolver=letsencrypt"
      - "traefik.http.services.iptv.loadbalancer.server.port=8000"
      - "traefik.http.routers.iptv-http.rule=Host(`iptv.yourdomain.com`)"
      - "traefik.http.routers.iptv-http.entrypoints=web"
      - "traefik.http.routers.iptv-http.middlewares=redirect-to-https"
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - CORS_ORIGINS=https://iptv.yourdomain.com
    volumes:
      - iptv_data:/app/data
      - iptv_logs:/app/logs
    networks:
      - traefik

volumes:
  letsencrypt:
  iptv_data:
  iptv_logs:

networks:
  traefik:
    external: true
```

## 📊 Monitoring and Logging

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - monitoring

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - monitoring

  iptv-manager:
    # ... existing config ...
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8000"
      - "prometheus.io/path=/metrics"
    networks:
      - monitoring
      - iptv_network

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
```

### ELK Stack for Logs

```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    networks:
      - elk

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - elk

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    networks:
      - elk

  iptv-manager:
    # ... existing config ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - elk
      - iptv_network

volumes:
  es_data:

networks:
  elk:
    driver: bridge
```

## 🔄 Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/iptv"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup (if using external PostgreSQL)
if [ "$USE_POSTGRES" = "true" ]; then
    docker exec postgres pg_dump -U iptv_user iptv_db > "$BACKUP_DIR/db_backup_$DATE.sql"
else
    # SQLite backup
    docker run --rm -v iptv_data:/data -v $BACKUP_DIR:/backup alpine cp /data/iptv.db /backup/iptv_backup_$DATE.db
fi

# Application data backup
docker run --rm -v iptv_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/data_backup_$DATE.tar.gz -C /data .

# Logs backup
docker run --rm -v iptv_logs:/logs -v $BACKUP_DIR:/backup alpine tar czf /backup/logs_backup_$DATE.tar.gz -C /logs .

# Cleanup old backups
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Script

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR="/backups/iptv"
BACKUP_DATE="$1"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la "$BACKUP_DIR" | grep backup
    exit 1
fi

# Stop services
docker-compose down

# Restore database
if [ "$USE_POSTGRES" = "true" ]; then
    docker exec postgres psql -U iptv_user -d iptv_db < "$BACKUP_DIR/db_backup_$BACKUP_DATE.sql"
else
    docker run --rm -v iptv_data:/data -v $BACKUP_DIR:/backup alpine cp /backup/iptv_backup_$BACKUP_DATE.db /data/iptv.db
fi

# Restore application data
docker run --rm -v iptv_data:/data -v $BACKUP_DIR:/backup alpine tar xzf /backup/data_backup_$BACKUP_DATE.tar.gz -C /data

# Restart services
docker-compose up -d

echo "Restore completed from $BACKUP_DATE"
```

## 🚀 Performance Optimization

### Application Settings

```env
# .env.production
# Database optimization
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30

# Caching
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600

# API rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Playlist validation
VALIDATION_WORKERS=4
VALIDATION_TIMEOUT=30
VALIDATION_BATCH_SIZE=100

# File upload limits
MAX_PLAYLIST_SIZE=104857600  # 100MB
MAX_CONCURRENT_UPLOADS=5
```

### Container Resource Limits

```yaml
services:
  iptv-manager:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

## 📋 Maintenance

### Update Procedure

1. **Backup current deployment**:
```bash
./backup.sh
```

2. **Pull latest changes**:
```bash
git pull origin main
docker-compose pull
```

3. **Update with zero downtime**:
```bash
docker-compose up -d --no-deps iptv-manager
```

4. **Verify deployment**:
```bash
curl -f http://localhost:8000/health
```

### Health Monitoring

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:8000/health"
MAX_RETRIES=3
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f -s "$HEALTH_URL" > /dev/null; then
        echo "Service is healthy"
        exit 0
    else
        echo "Health check failed (attempt $i/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    fi
done

echo "Service is unhealthy - restarting"
docker-compose restart iptv-manager
```

This comprehensive production setup ensures your IPTV Playlist Manager runs reliably, securely, and efficiently in any production environment! 🚀
