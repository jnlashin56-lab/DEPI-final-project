import React, { useState, useEffect } from 'react';
import { getTicketPrices, updateTicketPrice } from './adminApi';
import { Edit2, Search } from 'lucide-react';
import './admin.css';

interface TicketPrice {
  id: number;
  site_name: string;
  governorate?: string;
  heritage_type?: string;
  egyptian_egp?: number;
  egyptian_student_egp?: number;
  foreign_egp?: number;
  foreign_student_egp?: number;
  visiting_hours?: string;
}

const PricesManager = () => {
  const [prices, setPrices] = useState<TicketPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPrice, setEditingPrice] = useState<TicketPrice | null>(null);
  const [formData, setFormData] = useState<Partial<TicketPrice>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchPrices();
  }, [search]);

  const fetchPrices = async () => {
    try {
      setLoading(true);
      const data = await getTicketPrices(search);
      setPrices(data);
    } catch (err) {
      console.error("Failed to fetch ticket prices", err);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (price: TicketPrice) => {
    setEditingPrice(price);
    setFormData(price);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPrice) return;
    
    setIsSaving(true);
    try {
      await updateTicketPrice(editingPrice.id, formData);
      setIsModalOpen(false);
      fetchPrices();
    } catch (err) {
      alert("Failed to update ticket price");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <div className="admin-header">
        <h2>Ticket Prices Management</h2>
      </div>

      <div className="admin-table-container">
        <div className="admin-table-header">
          <div style={{position: 'relative', width: '300px'}}>
            <Search size={16} style={{position: 'absolute', left: '10px', top: '10px', color: 'var(--text-secondary)'}}/>
            <input 
              type="text" 
              placeholder="Search by site or governorate..." 
              className="admin-search-input"
              style={{paddingLeft: '2rem', width: '100%'}}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <span style={{color: 'var(--text-secondary)', alignSelf: 'center', marginLeft: 'auto'}}>
            Total: {prices.length}
          </span>
        </div>

        {loading ? (
          <div style={{padding: '2rem', textAlign: 'center'}}>Loading...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Site Name</th>
                <th>Governorate</th>
                <th>Egyptian</th>
                <th>EGY Student</th>
                <th>Foreign</th>
                <th>FOR Student</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {prices.map(price => (
                <tr key={price.id}>
                  <td>
                    {price.site_name}
                    {price.visiting_hours && <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)'}}>{price.visiting_hours}</div>}
                  </td>
                  <td>{price.governorate}</td>
                  <td>{price.egyptian_egp ?? '-'} EGP</td>
                  <td>{price.egyptian_student_egp ?? '-'} EGP</td>
                  <td>{price.foreign_egp ?? '-'} EGP</td>
                  <td>{price.foreign_student_egp ?? '-'} EGP</td>
                  <td>
                    <button className="admin-btn-icon" onClick={() => openModal(price)} title="Edit Prices">
                      <Edit2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Edit Modal */}
      {isModalOpen && editingPrice && (
        <div className="modal-overlay" onClick={() => !isSaving && setIsModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{marginBottom: '0.5rem', color: 'var(--accent-primary)'}}>Edit Ticket Prices</h3>
            <p style={{color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>{editingPrice.site_name}</p>
            
            <form onSubmit={handleSubmit}>
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
                <div className="admin-form-group">
                  <label>Egyptian (EGP)</label>
                  <input type="number" className="admin-form-input" step="any"
                    value={formData.egyptian_egp ?? ''} 
                    onChange={e => setFormData({...formData, egyptian_egp: e.target.value ? parseFloat(e.target.value) : undefined})} />
                </div>
                <div className="admin-form-group">
                  <label>Egyptian Student (EGP)</label>
                  <input type="number" className="admin-form-input" step="any"
                    value={formData.egyptian_student_egp ?? ''} 
                    onChange={e => setFormData({...formData, egyptian_student_egp: e.target.value ? parseFloat(e.target.value) : undefined})} />
                </div>
                <div className="admin-form-group">
                  <label>Foreign (EGP)</label>
                  <input type="number" className="admin-form-input" step="any"
                    value={formData.foreign_egp ?? ''} 
                    onChange={e => setFormData({...formData, foreign_egp: e.target.value ? parseFloat(e.target.value) : undefined})} />
                </div>
                <div className="admin-form-group">
                  <label>Foreign Student (EGP)</label>
                  <input type="number" className="admin-form-input" step="any"
                    value={formData.foreign_student_egp ?? ''} 
                    onChange={e => setFormData({...formData, foreign_student_egp: e.target.value ? parseFloat(e.target.value) : undefined})} />
                </div>
              </div>
              
              <div className="admin-form-group" style={{marginTop: '1rem'}}>
                <label>Visiting Hours</label>
                <input type="text" className="admin-form-input"
                  value={formData.visiting_hours || ''} 
                  onChange={e => setFormData({...formData, visiting_hours: e.target.value})} />
              </div>

              <div style={{display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem'}}>
                <button type="button" className="admin-btn-icon" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="admin-action-btn" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Prices'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PricesManager;
