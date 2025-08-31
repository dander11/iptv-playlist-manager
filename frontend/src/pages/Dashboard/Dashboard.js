import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Alert, Badge } from 'react-bootstrap';
import { useQuery } from 'react-query';
import axios from 'axios';
import { toast } from 'react-toastify';

const Dashboard = () => {
  const [validationStatus, setValidationStatus] = useState(null);

  // Fetch channel statistics
  const { data: stats, isLoading: statsLoading } = useQuery(
    'channelStats',
    () => axios.get('/api/channels/stats/').then(res => res.data),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  // Fetch validation status
  const { data: validation, isLoading: validationLoading, refetch: refetchValidation } = useQuery(
    'validationStatus',
    () => axios.get('/api/validation/status').then(res => res.data),
    { refetchInterval: 10000 } // Refresh every 10 seconds
  );

  // Fetch recent playlists
  const { data: playlists, isLoading: playlistsLoading } = useQuery(
    'recentPlaylists',
    () => axios.get('/api/playlists/').then(res => res.data)
  );

  const triggerValidation = async () => {
    try {
      await axios.post('/api/validation/validate', { validate_all: true });
      toast.success('Validation started successfully');
      refetchValidation();
    } catch (error) {
      toast.error('Failed to start validation');
    }
  };

  const generatePlaylist = async () => {
    try {
      await axios.post('/api/validation/generate-playlist');
      toast.success('Playlist generation started');
    } catch (error) {
      toast.error('Failed to generate playlist');
    }
  };

  if (statsLoading || validationLoading || playlistsLoading) {
    return (
      <Container>
        <div className="text-center py-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <div className="page-header">
            <h1>Dashboard</h1>
            <p className="text-muted">Overview of your IPTV playlist management system</p>
          </div>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row className="mb-4">
        <Col md={6}>
          <Card className="h-100">
            <Card.Body>
              <h5>Quick Actions</h5>
              <div className="d-grid gap-2">
                <Button variant="primary" onClick={triggerValidation}>
                  <i className="fas fa-play me-2"></i>
                  Run Validation Now
                </Button>
                <Button variant="outline-primary" onClick={generatePlaylist}>
                  <i className="fas fa-file-export me-2"></i>
                  Generate Unified Playlist
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card className="h-100">
            <Card.Body>
              <h5>System Status</h5>
              {validation && (
                <div>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span>Last Validation:</span>
                    <Badge bg={validation.status === 'completed' ? 'success' : 
                             validation.status === 'running' ? 'warning' : 'secondary'}>
                      {validation.status}
                    </Badge>
                  </div>
                  {validation.last_run && (
                    <small className="text-muted">
                      {new Date(validation.last_run).toLocaleString()}
                    </small>
                  )}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Statistics Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center stats-card">
            <Card.Body>
              <i className="fas fa-list fa-2x text-primary mb-2"></i>
              <h3>{playlists?.length || 0}</h3>
              <p className="text-muted mb-0">Total Playlists</p>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center stats-card">
            <Card.Body>
              <i className="fas fa-tv fa-2x text-success mb-2"></i>
              <h3>{stats?.total_channels || 0}</h3>
              <p className="text-muted mb-0">Total Channels</p>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center stats-card">
            <Card.Body>
              <i className="fas fa-check-circle fa-2x text-success mb-2"></i>
              <h3>{stats?.working_channels || 0}</h3>
              <p className="text-muted mb-0">Working Channels</p>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center stats-card">
            <Card.Body>
              <i className="fas fa-exclamation-triangle fa-2x text-warning mb-2"></i>
              <h3>{stats?.broken_channels || 0}</h3>
              <p className="text-muted mb-0">Broken Channels</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Recent Activity and Channel Groups */}
      <Row>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Recent Playlists</h5>
            </Card.Header>
            <Card.Body>
              {playlists && playlists.length > 0 ? (
                <div>
                  {playlists.slice(0, 5).map((playlist) => (
                    <div key={playlist.id} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                      <div>
                        <strong>{playlist.name}</strong>
                        <br />
                        <small className="text-muted">
                          {playlist.channel_count || 0} channels
                        </small>
                      </div>
                      <Badge bg={playlist.is_active ? 'success' : 'secondary'}>
                        {playlist.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted">No playlists available</p>
              )}
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Channel Groups</h5>
            </Card.Header>
            <Card.Body>
              {stats?.groups && stats.groups.length > 0 ? (
                <div>
                  {stats.groups.slice(0, 10).map((group, index) => (
                    <div key={index} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                      <span>{group.name}</span>
                      <Badge bg="info">{group.count}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted">No channel groups available</p>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Validation Status Alert */}
      {validation && validation.status === 'running' && (
        <Row className="mt-4">
          <Col>
            <Alert variant="info">
              <i className="fas fa-spinner fa-spin me-2"></i>
              Validation is currently running...
            </Alert>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default Dashboard;
