import React, { useState, useEffect } from 'react';
import { getBookings, confirmBooking, cancelBooking } from './adminApi';
import { Check, X, Filter } from 'lucide-react';
import './admin.css';

interface Booking {
  id: number;
  place_id: number;
  place_name: string;
  visitor_name: string;
  visitor_type: string;
  visitor_count: int;
  visit_date: string;
  visit_time: string;
  status: string;
  total_price_egp?: number;
  confirmation_code: string;
  created_at: string;
}

const BookingsDashboard = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchBookings();
  }, [statusFilter]);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const data = await getBookings(statusFilter);
      setBookings(data);
    } catch (err) {
      console.error("Failed to fetch bookings", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (id: number) => {
    if (!window.confirm("Confirm this booking?")) return;
    try {
      await confirmBooking(id);
      fetchBookings();
    } catch (err) {
      alert("Failed to confirm booking");
    }
  };

  const handleCancel = async (id: number) => {
    if (!window.confirm("Cancel this booking? This action updates the status to cancelled.")) return;
    try {
      await cancelBooking(id);
      fetchBookings();
    } catch (err) {
      alert("Failed to cancel booking");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed': return <span className="admin-badge success">Confirmed</span>;
      case 'pending': return <span className="admin-badge warning">Pending</span>;
      case 'cancelled': return <span className="admin-badge danger">Cancelled</span>;
      default: return <span className="admin-badge">{status}</span>;
    }
  };

  return (
    <div>
      <div className="admin-header">
        <h2>Bookings Dashboard</h2>
      </div>

      <div className="admin-table-container">
        <div className="admin-table-header" style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
          <Filter size={16} color="var(--text-secondary)" />
          <select 
            className="admin-form-input" 
            style={{width: '200px', padding: '0.4rem 0.8rem'}}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          
          <span style={{color: 'var(--text-secondary)', marginLeft: 'auto'}}>
            Total Bookings: {bookings.length}
          </span>
        </div>

        {loading ? (
          <div style={{padding: '2rem', textAlign: 'center'}}>Loading...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Place</th>
                <th>Visitor</th>
                <th>Count</th>
                <th>Date / Time</th>
                <th>Status</th>
                <th>Total (EGP)</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {bookings.map(b => (
                <tr key={b.id}>
                  <td style={{fontFamily: 'monospace', fontWeight: 'bold'}}>{b.confirmation_code}</td>
                  <td>{b.place_name || `ID: ${b.place_id}`}</td>
                  <td>
                    {b.visitor_name}
                    <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)'}}>{b.visitor_type}</div>
                  </td>
                  <td>{b.visitor_count}</td>
                  <td>
                    {b.visit_date}
                    <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)'}}>{b.visit_time || 'N/A'}</div>
                  </td>
                  <td>{getStatusBadge(b.status)}</td>
                  <td>{b.total_price_egp ?? '-'}</td>
                  <td>
                    {b.status === 'pending' && (
                      <>
                        <button className="admin-btn-icon" style={{color: '#4ade80'}} onClick={() => handleConfirm(b.id)} title="Confirm">
                          <Check size={18} />
                        </button>
                        <button className="admin-btn-icon" style={{color: '#f87171'}} onClick={() => handleCancel(b.id)} title="Cancel">
                          <X size={18} />
                        </button>
                      </>
                    )}
                    {b.status === 'confirmed' && (
                      <button className="admin-btn-icon" style={{color: '#f87171'}} onClick={() => handleCancel(b.id)} title="Cancel">
                        <X size={18} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {bookings.length === 0 && (
                <tr>
                  <td colSpan={8} style={{textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)'}}>
                    No bookings found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default BookingsDashboard;
