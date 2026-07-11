import React, { useState, useEffect } from 'react';
import { getAnalytics } from './adminApi';
import { TrendingUp, Users, MapPin, Database } from 'lucide-react';
import './admin.css';

const AnalyticsDashboard = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const res = await getAnalytics();
      setData(res);
    } catch (err) {
      console.error("Failed to fetch analytics", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={{padding: '2rem', textAlign: 'center'}}>Loading analytics...</div>;
  if (!data) return <div style={{padding: '2rem', textAlign: 'center'}}>Failed to load analytics</div>;

  return (
    <div>
      <div className="admin-header">
        <h2>Analytics Overview</h2>
      </div>

      {/* Summary Cards */}
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem'}}>
        
        <div className="glass-panel" style={{padding: '1.5rem'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
            <h3 style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>Total Bookings</h3>
            <Users size={20} color="var(--accent-primary)" />
          </div>
          <p style={{fontSize: '2rem', fontWeight: 'bold'}}>{data.total_bookings}</p>
        </div>

        <div className="glass-panel" style={{padding: '1.5rem'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
            <h3 style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>Total Revenue</h3>
            <TrendingUp size={20} color="#4ade80" />
          </div>
          <p style={{fontSize: '2rem', fontWeight: 'bold'}}>{data.total_revenue.toLocaleString()} EGP</p>
        </div>

        <div className="glass-panel" style={{padding: '1.5rem'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
            <h3 style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>Active Places</h3>
            <MapPin size={20} color="var(--accent-primary)" />
          </div>
          <p style={{fontSize: '2rem', fontWeight: 'bold'}}>{data.active_places}</p>
        </div>

        <div className="glass-panel" style={{padding: '1.5rem'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem'}}>
            <h3 style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>AI Indexed</h3>
            <Database size={20} color="#a78bfa" />
          </div>
          <p style={{fontSize: '2rem', fontWeight: 'bold'}}>{data.places_with_embeddings}</p>
          <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem'}}>
            {Math.round((data.places_with_embeddings / data.active_places) * 100)}% coverage
          </div>
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem'}}>
        {/* Top Booked Places */}
        <div className="admin-table-container" style={{padding: '1.5rem'}}>
          <h3 style={{marginBottom: '1rem', color: 'var(--accent-primary)'}}>Top 10 Most Booked</h3>
          <ul style={{listStyle: 'none', padding: 0}}>
            {data.top_booked_places.map((place: any, i: number) => (
              <li key={i} style={{
                display: 'flex', justifyContent: 'space-between', 
                padding: '0.8rem 0', borderBottom: '1px solid var(--border-color)'
              }}>
                <span>{place.name}</span>
                <span style={{fontWeight: 'bold', color: 'var(--accent-primary)'}}>{place.count}</span>
              </li>
            ))}
            {data.top_booked_places.length === 0 && <li style={{color: 'var(--text-secondary)'}}>No bookings yet.</li>}
          </ul>
        </div>

        {/* Bookings Status Breakdown */}
        <div className="admin-table-container" style={{padding: '1.5rem'}}>
          <h3 style={{marginBottom: '1rem', color: 'var(--accent-primary)'}}>Booking Status Breakdown</h3>
          <ul style={{listStyle: 'none', padding: 0}}>
            {Object.entries(data.bookings_by_status).map(([status, count]: [string, any]) => (
              <li key={status} style={{
                display: 'flex', justifyContent: 'space-between', 
                padding: '0.8rem 0', borderBottom: '1px solid var(--border-color)'
              }}>
                <span style={{textTransform: 'capitalize'}}>{status}</span>
                <span style={{fontWeight: 'bold'}}>{count}</span>
              </li>
            ))}
            {Object.keys(data.bookings_by_status).length === 0 && <li style={{color: 'var(--text-secondary)'}}>No data available.</li>}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
