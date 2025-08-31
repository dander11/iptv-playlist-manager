import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Table, Form, Badge, InputGroup, Pagination } from 'react-bootstrap';
import { useQuery } from 'react-query';
import axios from 'axios';

const Channels = () => {
  const [filters, setFilters] = useState({
    search: '',
    group: '',
    activeOnly: true,
    workingOnly: false
  });
  const [currentPage, setCurrentPage] = useState(1);
  const channelsPerPage = 50;

  // Fetch channels
  const { data: channels, isLoading } = useQuery(
    ['channels', filters, currentPage],
    () => {
      const params = new URLSearchParams({
        active_only: filters.activeOnly,
        working_only: filters.workingOnly,
        limit: channelsPerPage,
        offset: (currentPage - 1) * channelsPerPage
      });

      if (filters.search) params.append('search', filters.search);
      if (filters.group) params.append('group_title', filters.group);

      return axios.get(`/api/channels/?${params}`).then(res => res.data);
    }
  );

  // Fetch channel groups
  const { data: groups } = useQuery(
    'channelGroups',
    () => axios.get('/api/channels/groups/').then(res => res.data)
  );

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const getStatusBadge = (channel) => {
    if (!channel.is_active) {
      return <Badge bg="secondary">Inactive</Badge>;
    }
    if (channel.is_working) {
      return <Badge bg="success">Working</Badge>;
    }
    if (channel.last_checked) {
      return <Badge bg="danger">Failed</Badge>;
    }
    return <Badge bg="warning">Unchecked</Badge>;
  };

  const formatResponseTime = (time) => {
    if (!time) return 'N/A';
    return `${(time * 1000).toFixed(0)}ms`;
  };

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <div className="page-header">
            <h1>Channels</h1>
            <p className="text-muted">Browse and manage IPTV channels</p>
          </div>
        </Col>
      </Row>

      {/* Filters */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body>
              <Row>
                <Col md={4}>
                  <Form.Group>
                    <Form.Label>Search Channels</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <i className="fas fa-search"></i>
                      </InputGroup.Text>
                      <Form.Control
                        type="text"
                        placeholder="Search by name..."
                        value={filters.search}
                        onChange={(e) => handleFilterChange('search', e.target.value)}
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
                
                <Col md={3}>
                  <Form.Group>
                    <Form.Label>Channel Group</Form.Label>
                    <Form.Select
                      value={filters.group}
                      onChange={(e) => handleFilterChange('group', e.target.value)}
                    >
                      <option value="">All Groups</option>
                      {groups?.map((group, index) => (
                        <option key={index} value={group}>{group}</option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>
                
                <Col md={3}>
                  <Form.Group>
                    <Form.Label>Status Filter</Form.Label>
                    <div>
                      <Form.Check
                        type="checkbox"
                        label="Active only"
                        checked={filters.activeOnly}
                        onChange={(e) => handleFilterChange('activeOnly', e.target.checked)}
                      />
                      <Form.Check
                        type="checkbox"
                        label="Working only"
                        checked={filters.workingOnly}
                        onChange={(e) => handleFilterChange('workingOnly', e.target.checked)}
                      />
                    </div>
                  </Form.Group>
                </Col>
                
                <Col md={2} className="d-flex align-items-end">
                  <Button
                    variant="outline-secondary"
                    onClick={() => {
                      setFilters({
                        search: '',
                        group: '',
                        activeOnly: true,
                        workingOnly: false
                      });
                      setCurrentPage(1);
                    }}
                  >
                    Clear Filters
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Channels Table */}
      <Row>
        <Col>
          <Card>
            <Card.Body>
              {isLoading ? (
                <div className="text-center py-4">
                  <div className="spinner-border"></div>
                </div>
              ) : channels && channels.length > 0 ? (
                <>
                  <div className="table-responsive">
                    <Table striped hover>
                      <thead>
                        <tr>
                          <th>Channel</th>
                          <th>Group</th>
                          <th>Status</th>
                          <th>Response Time</th>
                          <th>Last Checked</th>
                          <th>URL</th>
                        </tr>
                      </thead>
                      <tbody>
                        {channels.map((channel) => (
                          <tr key={channel.id}>
                            <td>
                              <div className="d-flex align-items-center">
                                {channel.logo && (
                                  <img
                                    src={channel.logo}
                                    alt={channel.name}
                                    style={{ width: '32px', height: '32px', marginRight: '8px' }}
                                    onError={(e) => { e.target.style.display = 'none'; }}
                                  />
                                )}
                                <div>
                                  <strong>{channel.name}</strong>
                                  {channel.tvg_id && (
                                    <><br /><small className="text-muted">ID: {channel.tvg_id}</small></>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td>
                              <Badge bg="secondary">{channel.group_title || 'Unknown'}</Badge>
                            </td>
                            <td>{getStatusBadge(channel)}</td>
                            <td>{formatResponseTime(channel.response_time)}</td>
                            <td>
                              {channel.last_checked ? (
                                <small>{new Date(channel.last_checked).toLocaleString()}</small>
                              ) : (
                                <small className="text-muted">Never</small>
                              )}
                            </td>
                            <td>
                              <Button
                                variant="outline-primary"
                                size="sm"
                                onClick={() => window.open(channel.stream_url, '_blank')}
                                title="Open stream URL"
                              >
                                <i className="fas fa-external-link-alt"></i>
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                  
                  {/* Pagination */}
                  {channels.length === channelsPerPage && (
                    <div className="d-flex justify-content-center mt-3">
                      <Pagination>
                        <Pagination.Prev
                          disabled={currentPage === 1}
                          onClick={() => setCurrentPage(currentPage - 1)}
                        />
                        <Pagination.Item active>{currentPage}</Pagination.Item>
                        <Pagination.Next
                          onClick={() => setCurrentPage(currentPage + 1)}
                        />
                      </Pagination>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-5">
                  <i className="fas fa-tv fa-3x text-muted mb-3"></i>
                  <h5>No channels found</h5>
                  <p className="text-muted">Add playlists to see channels here</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Channels;
