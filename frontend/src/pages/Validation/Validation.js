import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Table, Alert, Badge, ProgressBar } from 'react-bootstrap';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import { toast } from 'react-toastify';

const Validation = () => {
  const [selectedLogId, setSelectedLogId] = useState(null);
  const queryClient = useQueryClient();

  // Fetch validation status
  const { data: status, isLoading: statusLoading } = useQuery(
    'validationStatus',
    () => axios.get('/api/validation/status').then(res => res.data),
    { refetchInterval: 5000 } // Refresh every 5 seconds
  );

  // Fetch validation logs
  const { data: logs, isLoading: logsLoading } = useQuery(
    'validationLogs',
    () => axios.get('/api/validation/logs').then(res => res.data)
  );

  // Fetch validation results for selected log
  const { data: results } = useQuery(
    ['validationResults', selectedLogId],
    () => selectedLogId ? axios.get(`/api/validation/logs/${selectedLogId}/results`).then(res => res.data) : null,
    { enabled: !!selectedLogId }
  );

  // Trigger validation mutation
  const triggerValidationMutation = useMutation(
    () => axios.post('/api/validation/validate', { validate_all: true }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('validationStatus');
        queryClient.invalidateQueries('validationLogs');
        toast.success('Validation started successfully');
      },
      onError: () => {
        toast.error('Failed to start validation');
      }
    }
  );

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <Badge bg="success">Completed</Badge>;
      case 'running':
        return <Badge bg="warning">Running</Badge>;
      case 'failed':
        return <Badge bg="danger">Failed</Badge>;
      default:
        return <Badge bg="secondary">Unknown</Badge>;
    }
  };

  const formatDuration = (started, completed) => {
    if (!started || !completed) return 'N/A';
    
    const start = new Date(started);
    const end = new Date(completed);
    const duration = Math.round((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.round(duration / 60)}m`;
    return `${Math.round(duration / 3600)}h`;
  };

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <div className="page-header d-flex justify-content-between align-items-center">
            <div>
              <h1>Validation</h1>
              <p className="text-muted">Monitor stream validation and system health</p>
            </div>
            <Button
              variant="primary"
              onClick={() => triggerValidationMutation.mutate()}
              disabled={triggerValidationMutation.isLoading || status?.status === 'running'}
            >
              <i className="fas fa-play me-2"></i>
              {status?.status === 'running' ? 'Validation Running...' : 'Run Validation'}
            </Button>
          </div>
        </Col>
      </Row>

      {/* Current Status */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Current Status</h5>
            </Card.Header>
            <Card.Body>
              {statusLoading ? (
                <div className="text-center">
                  <div className="spinner-border spinner-border-sm"></div>
                </div>
              ) : status ? (
                <Row>
                  <Col md={3}>
                    <div className="text-center">
                      <h4>{getStatusBadge(status.status)}</h4>
                      <small className="text-muted">Status</small>
                    </div>
                  </Col>
                  <Col md={3}>
                    <div className="text-center">
                      <h4>{status.total_channels || 0}</h4>
                      <small className="text-muted">Total Channels</small>
                    </div>
                  </Col>
                  <Col md={3}>
                    <div className="text-center">
                      <h4 className="text-success">{status.working_channels || 0}</h4>
                      <small className="text-muted">Working</small>
                    </div>
                  </Col>
                  <Col md={3}>
                    <div className="text-center">
                      <h4 className="text-danger">{status.failed_channels || 0}</h4>
                      <small className="text-muted">Failed</small>
                    </div>
                  </Col>
                </Row>
              ) : (
                <Alert variant="info">No validation data available</Alert>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Validation Progress */}
      {status?.status === 'running' && (
        <Row className="mb-4">
          <Col>
            <Alert variant="info">
              <div className="d-flex align-items-center">
                <div className="spinner-border spinner-border-sm me-3"></div>
                <div className="flex-grow-1">
                  <strong>Validation in progress...</strong>
                  <ProgressBar 
                    animated 
                    now={85} 
                    className="mt-2"
                    style={{ height: '8px' }}
                  />
                </div>
              </div>
            </Alert>
          </Col>
        </Row>
      )}

      {/* Validation Logs */}
      <Row>
        <Col md={8}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Validation History</h5>
            </Card.Header>
            <Card.Body>
              {logsLoading ? (
                <div className="text-center py-4">
                  <div className="spinner-border"></div>
                </div>
              ) : logs && logs.length > 0 ? (
                <div className="table-responsive">
                  <Table striped hover>
                    <thead>
                      <tr>
                        <th>Started</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Channels</th>
                        <th>Results</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr 
                          key={log.id}
                          className={selectedLogId === log.id ? 'table-active' : ''}
                        >
                          <td>
                            <small>{new Date(log.started_at).toLocaleString()}</small>
                          </td>
                          <td>{getStatusBadge(log.status)}</td>
                          <td>
                            <small>{formatDuration(log.started_at, log.completed_at)}</small>
                          </td>
                          <td>
                            <Badge bg="info">{log.total_channels}</Badge>
                          </td>
                          <td>
                            <div>
                              <Badge bg="success" className="me-1">{log.working_channels} ✓</Badge>
                              <Badge bg="danger">{log.failed_channels} ✗</Badge>
                            </div>
                          </td>
                          <td>
                            <Button
                              variant="outline-primary"
                              size="sm"
                              onClick={() => setSelectedLogId(log.id === selectedLogId ? null : log.id)}
                            >
                              {selectedLogId === log.id ? 'Hide' : 'View'} Details
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-5">
                  <i className="fas fa-clock fa-3x text-muted mb-3"></i>
                  <h5>No validation history</h5>
                  <p className="text-muted">Run your first validation to see results here</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Validation Results Details */}
        <Col md={4}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Validation Details</h5>
            </Card.Header>
            <Card.Body>
              {selectedLogId && results ? (
                <div>
                  <h6>Results Summary</h6>
                  <Table size="sm">
                    <tbody>
                      <tr>
                        <td>Total Checked:</td>
                        <td><Badge bg="info">{results.length}</Badge></td>
                      </tr>
                      <tr>
                        <td>Working:</td>
                        <td><Badge bg="success">{results.filter(r => r.is_working).length}</Badge></td>
                      </tr>
                      <tr>
                        <td>Failed:</td>
                        <td><Badge bg="danger">{results.filter(r => !r.is_working).length}</Badge></td>
                      </tr>
                    </tbody>
                  </Table>

                  <h6 className="mt-3">Failed Channels</h6>
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {results.filter(r => !r.is_working).length > 0 ? (
                      results.filter(r => !r.is_working).map((result) => (
                        <div key={result.id} className="border-bottom py-2">
                          <small>
                            <strong>Channel ID:</strong> {result.channel_id}<br />
                            <strong>Error:</strong> {result.error_message || 'Unknown error'}<br />
                            <strong>Status:</strong> {result.status_code || 'N/A'}
                          </small>
                        </div>
                      ))
                    ) : (
                      <small className="text-muted">All channels are working!</small>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <i className="fas fa-info-circle fa-2x text-muted mb-3"></i>
                  <p className="text-muted">Select a validation log to see details</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Validation;
