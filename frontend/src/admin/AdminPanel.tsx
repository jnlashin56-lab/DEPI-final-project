import React from 'react';
import { Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom';
import { MapPin, Ticket, BookOpen, BarChart3, Users, LogOut, ArrowLeft } from 'lucide-react';
import './admin.css';

// We'll import these as we build them in Phase 3/4
import PlacesManager from './PlacesManager';
import PricesManager from './PricesManager';
import BookingsDashboard from './BookingsDashboard';
import AnalyticsDashboard from './AnalyticsDashboard';
import CrowdProfileEditor from './CrowdProfileEditor';

const AdminPanel = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('adminToken');

  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    navigate('/admin/login');
  };

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <h2>Admin Panel</h2>
        <nav className="admin-nav">
          <NavLink to="/admin/places" className={({isActive}) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <MapPin size={18} /> Places
          </NavLink>
          <NavLink to="/admin/prices" className={({isActive}) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <Ticket size={18} /> Ticket Prices
          </NavLink>
          <NavLink to="/admin/bookings" className={({isActive}) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <BookOpen size={18} /> Bookings
          </NavLink>
          <NavLink to="/admin/analytics" className={({isActive}) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <BarChart3 size={18} /> Analytics
          </NavLink>
          <NavLink to="/admin/crowd" className={({isActive}) => `admin-nav-item ${isActive ? 'active' : ''}`}>
            <Users size={18} /> Crowd Profiles
          </NavLink>
        </nav>
        
        <button onClick={handleLogout} className="admin-logout">
          <LogOut size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Logout
        </button>
      </aside>

      <main className="admin-content">
        <header className="admin-header">
          <h1>Dashboard</h1>
          <button onClick={() => navigate('/')} className="admin-action-btn" style={{background: 'var(--bg-tertiary)', color: 'var(--text-primary)'}}>
            <ArrowLeft size={16} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Back to Site
          </button>
        </header>
        
        <Routes>
          <Route path="/" element={<Navigate to="places" replace />} />
          <Route path="places" element={<PlacesManager />} />
          <Route path="prices" element={<PricesManager />} />
          <Route path="bookings" element={<BookingsDashboard />} />
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="crowd" element={<CrowdProfileEditor />} />
        </Routes>
      </main>
    </div>
  );
};

export default AdminPanel;
