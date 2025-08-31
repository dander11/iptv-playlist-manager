# IPTV Playlist Manager

A modern web-based application to manage, aggregate, clean, and deliver IPTV M3U playlists with automated nightly validation.

## Features

- **Web Interface**: Modern React-based UI for playlist management
- **Multi-Source Aggregation**: Combine multiple M3U playlists from URLs or uploads
- **Automated Validation**: Nightly validation to remove dead streams and duplicates
- **RESTful API**: Complete API for integration and automation
- **Docker Deployment**: Containerized for easy deployment
- **Real-time Monitoring**: Health checks and validation logs

## Architecture

```
├── backend/         # Python FastAPI backend
├── frontend/        # React.js frontend
├── docker/          # Docker configuration
├── scripts/         # Automation scripts
├── docs/            # Documentation
└── tests/           # Test suites
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for development)
- Node.js 16+ (for frontend development)

### Development Setup

1. Clone and setup:
```bash
git clone <repository-url>
cd iptv-checker
```

2. Start with Docker Compose:
```bash
docker-compose up -d
```

3. Access the application:
- Web UI: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Development

1. Backend setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Frontend setup:
```bash
cd frontend
npm install
npm start
```

## Configuration

The application can be configured through:
- Environment variables
- `config/config.yaml`
- Web UI settings panel

## Testing

Run the test suite:
```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && npm test
```

## License

MIT License - see LICENSE file for details.
