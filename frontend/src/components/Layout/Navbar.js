import React from 'react';
import { Navbar as BootstrapNavbar, Nav, Container, NavDropdown } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

const Navbar = ({ title }) => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <BootstrapNavbar bg="dark" variant="dark" expand="lg" className="px-3">
      <Container fluid>
        <BootstrapNavbar.Brand>
          <i className="fas fa-tv me-2"></i>
          {title}
        </BootstrapNavbar.Brand>
        
        <BootstrapNavbar.Toggle aria-controls="basic-navbar-nav" />
        <BootstrapNavbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <NavDropdown title={`Welcome, ${user?.username}`} id="user-dropdown">
              <NavDropdown.Item disabled>
                <small className="text-muted">
                  {user?.is_admin ? 'Administrator' : 'User'}
                </small>
              </NavDropdown.Item>
              <NavDropdown.Divider />
              <NavDropdown.Item onClick={handleLogout}>
                <i className="fas fa-sign-out-alt me-2"></i>
                Logout
              </NavDropdown.Item>
            </NavDropdown>
          </Nav>
        </BootstrapNavbar.Collapse>
      </Container>
    </BootstrapNavbar>
  );
};

export default Navbar;
