import React, { useState } from 'react';
import { Container, Row, Col, Card, Button, Table, Modal, Form, Alert, Badge, Spinner } from 'react-bootstrap';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import { toast } from 'react-toastify';

const Playlists = () => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    source_url: ''
  });
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadName, setUploadName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');

  const queryClient = useQueryClient();

  // Fetch playlists
  const { data: playlists, isLoading, error } = useQuery(
    'playlists',
    () => axios.get('/api/playlists/').then(res => res.data)
  );

  // Add playlist mutation
  const addPlaylistMutation = useMutation(
    (playlistData) => axios.post('/api/playlists/', playlistData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('playlists');
        setShowAddModal(false);
        setFormData({ name: '', description: '', source_url: '' });
        toast.success('Playlist added successfully');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to add playlist');
      }
    }
  );

  // Upload playlist mutation
  const uploadPlaylistMutation = useMutation(
    (formData) => axios.post('/api/playlists/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('playlists');
        setShowUploadModal(false);
        setUploadFile(null);
        setUploadName('');
        setUploadDescription('');
        toast.success('Playlist uploaded successfully');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to upload playlist');
      }
    }
  );

  // Delete playlist mutation
  const deletePlaylistMutation = useMutation(
    (playlistId) => axios.delete(`/api/playlists/${playlistId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('playlists');
        toast.success('Playlist deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete playlist');
      }
    }
  );

  // Refresh playlist mutation
  const refreshPlaylistMutation = useMutation(
    (playlistId) => axios.post(`/api/playlists/${playlistId}/refresh`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('playlists');
        toast.success('Playlist refreshed successfully');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to refresh playlist');
      }
    }
  );

  const handleAddSubmit = (e) => {
    e.preventDefault();
    addPlaylistMutation.mutate(formData);
  };

  const handleUploadSubmit = (e) => {
    e.preventDefault();
    
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('name', uploadName);
    formData.append('description', uploadDescription);
    formData.append('file', uploadFile);

    uploadPlaylistMutation.mutate(formData);
  };

  const handleDelete = (playlistId) => {
    if (window.confirm('Are you sure you want to delete this playlist?')) {
      deletePlaylistMutation.mutate(playlistId);
    }
  };

  const handleRefresh = (playlistId) => {
    refreshPlaylistMutation.mutate(playlistId);
  };

  if (isLoading) {
    return (
      <Container>
        <div className="text-center py-5">
          <Spinner animation="border" />
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert variant="danger">
          Error loading playlists: {error.message}
        </Alert>
      </Container>
    );
  }

  return (
    <Container fluid>
      <Row className="mb-4">
        <Col>
          <div className="page-header d-flex justify-content-between align-items-center">
            <div>
              <h1>Playlists</h1>
              <p className="text-muted">Manage your IPTV playlist sources</p>
            </div>
            <div>
              <Button variant="outline-primary" className="me-2" onClick={() => setShowUploadModal(true)}>
                <i className="fas fa-upload me-2"></i>
                Upload File
              </Button>
              <Button variant="primary" onClick={() => setShowAddModal(true)}>
                <i className="fas fa-plus me-2"></i>
                Add from URL
              </Button>
            </div>
          </div>
        </Col>
      </Row>

      {/* Playlists Table */}
      <Row>
        <Col>
          <Card>
            <Card.Body>
              {playlists && playlists.length > 0 ? (
                <div className="table-responsive">
                  <Table striped hover>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Source</th>
                        <th>Channels</th>
                        <th>Status</th>
                        <th>Last Updated</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {playlists.map((playlist) => (
                        <tr key={playlist.id}>
                          <td>
                            <strong>{playlist.name}</strong>
                            {playlist.description && (
                              <><br /><small className="text-muted">{playlist.description}</small></>
                            )}
                          </td>
                          <td>
                            {playlist.source_url ? (
                              <a href={playlist.source_url} target="_blank" rel="noopener noreferrer">
                                <i className="fas fa-external-link-alt me-1"></i>
                                URL
                              </a>
                            ) : (
                              <span>
                                <i className="fas fa-file me-1"></i>
                                Uploaded File
                              </span>
                            )}
                          </td>
                          <td>
                            <Badge bg="info">{playlist.channel_count || 0}</Badge>
                          </td>
                          <td>
                            <Badge bg={playlist.is_active ? 'success' : 'secondary'}>
                              {playlist.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td>
                            <small>{new Date(playlist.updated_at).toLocaleString()}</small>
                          </td>
                          <td>
                            <div className="btn-group btn-group-sm">
                              {playlist.source_url && (
                                <Button
                                  variant="outline-primary"
                                  size="sm"
                                  onClick={() => handleRefresh(playlist.id)}
                                  disabled={refreshPlaylistMutation.isLoading}
                                >
                                  <i className="fas fa-sync-alt"></i>
                                </Button>
                              )}
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => handleDelete(playlist.id)}
                                disabled={deletePlaylistMutation.isLoading}
                              >
                                <i className="fas fa-trash"></i>
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-5">
                  <i className="fas fa-list fa-3x text-muted mb-3"></i>
                  <h5>No playlists found</h5>
                  <p className="text-muted">Add your first playlist to get started</p>
                  <Button variant="primary" onClick={() => setShowAddModal(true)}>
                    <i className="fas fa-plus me-2"></i>
                    Add Playlist
                  </Button>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Add Playlist Modal */}
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)} size="lg">
        <Form onSubmit={handleAddSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>Add Playlist from URL</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Playlist Name</Form.Label>
              <Form.Control
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="Enter playlist name"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Description (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Enter description"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>M3U URL</Form.Label>
              <Form.Control
                type="url"
                value={formData.source_url}
                onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                required
                placeholder="https://example.com/playlist.m3u"
              />
              <Form.Text className="text-muted">
                Example: https://iptv-org.github.io/iptv/index.m3u
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              type="submit"
              disabled={addPlaylistMutation.isLoading}
            >
              {addPlaylistMutation.isLoading ? (
                <>
                  <Spinner size="sm" className="me-2" />
                  Adding...
                </>
              ) : (
                'Add Playlist'
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Upload Playlist Modal */}
      <Modal show={showUploadModal} onHide={() => setShowUploadModal(false)} size="lg">
        <Form onSubmit={handleUploadSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>Upload Playlist File</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Playlist Name</Form.Label>
              <Form.Control
                type="text"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                required
                placeholder="Enter playlist name"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Description (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={uploadDescription}
                onChange={(e) => setUploadDescription(e.target.value)}
                placeholder="Enter description"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>M3U File</Form.Label>
              <Form.Control
                type="file"
                accept=".m3u,.m3u8"
                onChange={(e) => setUploadFile(e.target.files[0])}
                required
              />
              <Form.Text className="text-muted">
                Supported formats: .m3u, .m3u8
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowUploadModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              type="submit"
              disabled={uploadPlaylistMutation.isLoading}
            >
              {uploadPlaylistMutation.isLoading ? (
                <>
                  <Spinner size="sm" className="me-2" />
                  Uploading...
                </>
              ) : (
                'Upload Playlist'
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
};

export default Playlists;
