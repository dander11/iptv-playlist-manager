import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Table, Badge } from 'react-bootstrap';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import { toast } from 'react-toastify';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('general');
  const queryClient = useQueryClient();

  // Fetch system configuration
  const { data: config, isLoading: configLoading } = useQuery(
    'systemConfig',
    () => axios.get('/api/system/config').then(res => res.data)
  );

  // Fetch system status
  const { data: systemStatus } = useQuery(
    'systemStatus',
    () => axios.get('/api/system/status').then(res => res.data),
    { refetchInterval: 30000 }
  );

  // Update configuration mutation
  const updateConfigMutation = useMutation(
    (configData) => axios.put('/api/system/config', configData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('systemConfig');
        toast.success('Configuration updated successfully');
      },
      onError: () => {
        toast.error('Failed to update configuration');
      }
    }
  );

  const handleConfigSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const configData = {
      validation_timeout: parseInt(formData.get('validation_timeout')),
      validation_concurrent_limit: parseInt(formData.get('validation_concurrent_limit')),
      validation_retry_attempts: parseInt(formData.get('validation_retry_attempts'))
    };
    updateConfigMutation.mutate(configData);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <div className="page-header">
            <h1>Settings</h1>
            <p className="text-muted">Configure system settings and view system information</p>
          </div>
        </Col>
      </Row>

      {/* Settings Navigation */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <div className="btn-group" role="group">
                <Button
                  variant={activeTab === 'general' ? 'primary' : 'outline-primary'}
                  onClick={() => setActiveTab('general')}
                >
                  General
                </Button>
                <Button
                  variant={activeTab === 'validation' ? 'primary' : 'outline-primary'}
                  onClick={() => setActiveTab('validation')}
                >
                  Validation
                </Button>
                <Button
                  variant={activeTab === 'system' ? 'primary' : 'outline-primary'}
                  onClick={() => setActiveTab('system')}
                >
                  System Info
                </Button>
              </div>
            </Card.Header>
          </Card>
        </Col>
      </Row>

      {/* General Settings */}
      {activeTab === 'general' && (
        <Row>
          <Col md={8}>
            <Card>
              <Card.Header>
                <h5 className="mb-0">General Configuration</h5>
              </Card.Header>
              <Card.Body>
                {configLoading ? (
                  <div className="text-center py-4">
                    <div className="spinner-border"></div>
                  </div>
                ) : config ? (
                  <Form onSubmit={handleConfigSubmit}>
                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>HTTP Timeout (seconds)</Form.Label>
                          <Form.Control
                            type="number"
                            name="http_timeout"
                            defaultValue={config.http_timeout}
                            min="5"
                            max="120"
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>JWT Expire Minutes</Form.Label>
                          <Form.Control
                            type="number"
                            name="jwt_expire_minutes"
                            defaultValue={config.jwt_expire_minutes}
                            min="15"
                            max="1440"
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Form.Group className="mb-3">
                      <Form.Label>Max Playlist Size</Form.Label>
                      <Form.Control
                        type="text"
                        value={formatBytes(config.max_playlist_size)}
                        disabled
                      />
                      <Form.Text className="text-muted">
                        Maximum allowed playlist file size
                      </Form.Text>
                    </Form.Group>

                    <Button
                      type="submit"
                      variant="primary"
                      disabled={updateConfigMutation.isLoading}
                    >
                      {updateConfigMutation.isLoading ? 'Updating...' : 'Update Settings'}
                    </Button>
                  </Form>
                ) : (
                  <Alert variant="warning">Unable to load configuration</Alert>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Validation Settings */}
      {activeTab === 'validation' && (
        <Row>
          <Col md={8}>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Validation Configuration</h5>
              </Card.Header>
              <Card.Body>
                {config ? (
                  <Form onSubmit={handleConfigSubmit}>
                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Validation Timeout (seconds)</Form.Label>
                          <Form.Control
                            type="number"
                            name="validation_timeout"
                            defaultValue={config.validation_timeout}
                            min="5"
                            max="120"
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Concurrent Limit</Form.Label>
                          <Form.Control
                            type="number"
                            name="validation_concurrent_limit"
                            defaultValue={config.validation_concurrent_limit}
                            min="1"
                            max="100"
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Retry Attempts</Form.Label>
                          <Form.Control
                            type="number"
                            name="validation_retry_attempts"
                            defaultValue={config.validation_retry_attempts}
                            min="1"
                            max="10"
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Schedule</Form.Label>
                          <Form.Control
                            type="text"
                            value={config.validation_schedule}
                            disabled
                          />
                          <Form.Text className="text-muted">
                            Cron expression for automatic validation
                          </Form.Text>
                        </Form.Group>
                      </Col>
                    </Row>

                    <Button
                      type="submit"
                      variant="primary"
                      disabled={updateConfigMutation.isLoading}
                    >
                      {updateConfigMutation.isLoading ? 'Updating...' : 'Update Validation Settings'}
                    </Button>
                  </Form>
                ) : (
                  <Alert variant="warning">Unable to load configuration</Alert>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* System Information */}
      {activeTab === 'system' && (
        <Row>
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">System Information</h5>
              </Card.Header>
              <Card.Body>
                {systemStatus ? (
                  <Row>
                    <Col md={6}>
                      <h6>System Resources</h6>
                      <Table size="sm">
                        <tbody>
                          <tr>
                            <td>Memory Usage:</td>
                            <td>
                              <Badge bg="info">
                                {systemStatus.memory_usage?.percentage?.toFixed(1)}%
                              </Badge>
                            </td>
                          </tr>
                          <tr>
                            <td>Disk Usage:</td>
                            <td>
                              <Badge bg="info">
                                {systemStatus.disk_usage?.percentage?.toFixed(1)}%
                              </Badge>
                            </td>
                          </tr>
                          <tr>
                            <td>Status:</td>
                            <td>
                              <Badge bg="success">{systemStatus.status}</Badge>
                            </td>
                          </tr>
                        </tbody>
                      </Table>
                    </Col>
                    
                    <Col md={6}>
                      <h6>Database Statistics</h6>
                      <Table size="sm">
                        <tbody>
                          <tr>
                            <td>Total Playlists:</td>
                            <td><Badge bg="info">{systemStatus.database_stats?.total_playlists}</Badge></td>
                          </tr>
                          <tr>
                            <td>Active Playlists:</td>
                            <td><Badge bg="success">{systemStatus.database_stats?.active_playlists}</Badge></td>
                          </tr>
                          <tr>
                            <td>Total Channels:</td>
                            <td><Badge bg="info">{systemStatus.database_stats?.total_channels}</Badge></td>
                          </tr>
                          <tr>
                            <td>Working Channels:</td>
                            <td><Badge bg="success">{systemStatus.database_stats?.working_channels}</Badge></td>
                          </tr>
                        </tbody>
                      </Table>
                    </Col>
                  </Row>
                ) : (
                  <Alert variant="warning">Unable to load system information</Alert>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default Settings;
