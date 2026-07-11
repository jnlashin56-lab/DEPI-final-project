import React, { useState, useEffect } from 'react';
import { getPlaces, createPlace, updatePlace, deletePlace } from './adminApi';
import { Edit2, Trash2, Plus, AlertCircle, CheckCircle2 } from 'lucide-react';
import './admin.css';

interface Place {
  id: number;
  name: string;
  name_ar?: string;
  category?: string;
  category_ar?: string;
  description?: string;
  description_ar?: string;
  price_egp?: number;
  latitude?: number;
  longitude?: number;
  has_embedding: boolean;
}

const PlacesManager = () => {
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlace, setEditingPlace] = useState<Place | null>(null);
  const [formData, setFormData] = useState<Partial<Place>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchPlaces();
  }, [page, search]);

  const fetchPlaces = async () => {
    try {
      setLoading(true);
      const data = await getPlaces(page, 50, search);
      setPlaces(data.places);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch places", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this place? This will also delete related crowd profiles and bookings.")) return;
    try {
      await deletePlace(id);
      fetchPlaces();
    } catch (err) {
      alert("Failed to delete place");
    }
  };

  const openModal = (place?: Place) => {
    if (place) {
      setEditingPlace(place);
      setFormData(place);
    } else {
      setEditingPlace(null);
      setFormData({
        name: '', name_ar: '', category: '', category_ar: '', 
        description: '', description_ar: '', price_egp: undefined, 
        latitude: undefined, longitude: undefined
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      if (editingPlace) {
        await updatePlace(editingPlace.id, formData);
      } else {
        await createPlace(formData);
      }
      setIsModalOpen(false);
      fetchPlaces();
    } catch (err) {
      alert("Failed to save place");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <div className="admin-header">
        <h2>Places Management</h2>
        <button className="admin-action-btn" onClick={() => openModal()}>
          <Plus size={16} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Add Place
        </button>
      </div>

      <div className="admin-table-container">
        <div className="admin-table-header">
          <input 
            type="text" 
            placeholder="Search places..." 
            className="admin-search-input"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
          />
          <span style={{color: 'var(--text-secondary)', alignSelf: 'center'}}>
            Total: {total}
          </span>
        </div>

        {loading ? (
          <div style={{padding: '2rem', textAlign: 'center'}}>Loading...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Category</th>
                <th>Price (EGP)</th>
                <th>Vector Indexed</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {places.map(place => (
                <tr key={place.id}>
                  <td>{place.id}</td>
                  <td>
                    {place.name}
                    {place.name_ar && <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)'}}>{place.name_ar}</div>}
                  </td>
                  <td>{place.category}</td>
                  <td>{place.price_egp ?? '-'}</td>
                  <td>
                    {place.has_embedding 
                      ? <span className="admin-badge success"><CheckCircle2 size={12} style={{verticalAlign: 'middle'}}/> Yes</span>
                      : <span className="admin-badge warning"><AlertCircle size={12} style={{verticalAlign: 'middle'}}/> No</span>
                    }
                  </td>
                  <td>
                    <button className="admin-btn-icon" onClick={() => openModal(place)} title="Edit">
                      <Edit2 size={18} />
                    </button>
                    <button className="admin-btn-icon delete" onClick={() => handleDelete(place.id)} title="Delete">
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Edit Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => !isSaving && setIsModalOpen(false)}>
          <div className="modal-content" style={{maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto'}} onClick={e => e.stopPropagation()}>
            <h3 style={{marginBottom: '1.5rem', color: 'var(--accent-primary)'}}>
              {editingPlace ? 'Edit Place' : 'Add New Place'}
            </h3>
            
            <form onSubmit={handleSubmit}>
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
                <div className="admin-form-group">
                  <label>Name (English) *</label>
                  <input type="text" className="admin-form-input" required
                    value={formData.name || ''} onChange={e => setFormData({...formData, name: e.target.value})} />
                </div>
                <div className="admin-form-group">
                  <label>Name (Arabic)</label>
                  <input type="text" className="admin-form-input" dir="rtl"
                    value={formData.name_ar || ''} onChange={e => setFormData({...formData, name_ar: e.target.value})} />
                </div>
                
                <div className="admin-form-group">
                  <label>Category (English)</label>
                  <input type="text" className="admin-form-input" 
                    value={formData.category || ''} onChange={e => setFormData({...formData, category: e.target.value})} />
                </div>
                <div className="admin-form-group">
                  <label>Category (Arabic)</label>
                  <input type="text" className="admin-form-input" dir="rtl"
                    value={formData.category_ar || ''} onChange={e => setFormData({...formData, category_ar: e.target.value})} />
                </div>

                <div className="admin-form-group">
                  <label>Price (EGP)</label>
                  <input type="number" className="admin-form-input" step="0.01"
                    value={formData.price_egp || ''} onChange={e => setFormData({...formData, price_egp: parseFloat(e.target.value)})} />
                </div>
                <div className="admin-form-group">
                  <label>Coordinates (Lat, Lng)</label>
                  <div style={{display: 'flex', gap: '0.5rem'}}>
                    <input type="number" className="admin-form-input" step="any" placeholder="Latitude"
                      value={formData.latitude || ''} onChange={e => setFormData({...formData, latitude: parseFloat(e.target.value)})} />
                    <input type="number" className="admin-form-input" step="any" placeholder="Longitude"
                      value={formData.longitude || ''} onChange={e => setFormData({...formData, longitude: parseFloat(e.target.value)})} />
                  </div>
                </div>
              </div>

              <div className="admin-form-group">
                <label>Description (English)</label>
                <textarea className="admin-form-textarea" 
                  value={formData.description || ''} onChange={e => setFormData({...formData, description: e.target.value})} />
                <small style={{color: 'var(--text-secondary)'}}>Editing description will auto-trigger AI re-embedding on save.</small>
              </div>

              <div className="admin-form-group">
                <label>Description (Arabic)</label>
                <textarea className="admin-form-textarea" dir="rtl"
                  value={formData.description_ar || ''} onChange={e => setFormData({...formData, description_ar: e.target.value})} />
              </div>

              <div style={{display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem'}}>
                <button type="button" className="admin-btn-icon" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="admin-action-btn" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Place'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlacesManager;
