import React from 'react';
import { Nav } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { useLocation } from 'react-router-dom';

const Sidebar = () => {
  const location = useLocation();
  
  const menuItems = [
    { path: '/', icon: 'fas fa-tachometer-alt', label: 'Dashboard' },
    { path: '/playlists', icon: 'fas fa-list', label: 'Playlists' },
    { path: '/channels', icon: 'fas fa-tv', label: 'Channels' },
    { path: '/validation', icon: 'fas fa-check-circle', label: 'Validation' },
    { path: '/settings', icon: 'fas fa-cog', label: 'Settings' },
  ];

  return (
    <div className="sidebar d-flex flex-column" style={{ width: '250px' }}>
      <div className="p-3">
        <h5 className="text-center mb-4">
          <i className="fas fa-broadcast-tower me-2 text-primary"></i>
          IPTV Manager
        </h5>
        
        <Nav className="flex-column">
          {menuItems.map((item) => (
            <LinkContainer key={item.path} to={item.path}>
              <Nav.Link 
                className={`mb-2 rounded ${location.pathname === item.path ? 'bg-primary text-white' : ''}`}
              >
                <i className={`${item.icon} me-2`}></i>
                {item.label}
              </Nav.Link>
            </LinkContainer>
          ))}
        </Nav>
      </div>
      
      {/* Footer */}
      <div className="mt-auto p-3 border-top">
        <small className="text-muted">
          <i className="fas fa-info-circle me-1"></i>
          Version 1.0.0
        </small>
      </div>
    </div>
  );
};

export default Sidebar;
