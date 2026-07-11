import React, { useState, useEffect } from 'react';
import { getCrowdProfiles, updateCrowdProfile } from './adminApi';
import { Edit2 } from 'lucide-react';
import './admin.css';

interface CrowdProfile {
  place_id: number;
  place_name: string;
  base_crowd_level: string;
  peak_hours: string[];
  peak_season_months: number[];
  is_outdoor: boolean;
  notes?: string;
}

const CrowdProfileEditor = () => {
  const [profiles, setProfiles] = useState<CrowdProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<CrowdProfile | null>(null);
  const [formData, setFormData] = useState<Partial<CrowdProfile>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    try {
      setLoading(true);
      const data = await getCrowdProfiles();
      setProfiles(data);
    } catch (err) {
      console.error("Failed to fetch crowd profiles", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredProfiles = profiles.filter(p => 
    p.place_name?.toLowerCase().includes(search.toLowerCase())
  );

  const openModal = (profile: CrowdProfile) => {
    setEditingProfile(profile);
    setFormData(profile);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProfile) return;
    
    setIsSaving(true);
    try {
      await updateCrowdProfile(editingProfile.place_id, formData);
      setIsModalOpen(false);
      fetchProfiles();
    } catch (err) {
      alert("Failed to update crowd profile");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <div className="admin-header">
        <h2>Crowd Profiles</h2>
      </div>

      <div className="admin-table-container">
        <div className="admin-table-header">
          <input 
            type="text" 
            placeholder="Search places..." 
            className="admin-search-input"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <span style={{color: 'var(--text-secondary)', alignSelf: 'center', marginLeft: 'auto'}}>
            Total: {filteredProfiles.length}
          </span>
        </div>

        {loading ? (
          <div style={{padding: '2rem', textAlign: 'center'}}>Loading...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Place</th>
                <th>Base Crowd Level</th>
                <th>Peak Hours</th>
                <th>Peak Months</th>
                <th>Type</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredProfiles.map(profile => (
                <tr key={profile.place_id}>
                  <td>{profile.place_name || `ID: ${profile.place_id}`}</td>
                  <td>
                    <span className={`admin-badge crowd-${profile.base_crowd_level}`}>
                      {profile.base_crowd_level}
                    </span>
                  </td>
                  <td>{profile.peak_hours?.join(', ') || '-'}</td>
                  <td>{profile.peak_season_months?.join(', ') || '-'}</td>
                  <td>{profile.is_outdoor ? 'Outdoor' : 'Indoor'}</td>
                  <td>
                    <button className="admin-btn-icon" onClick={() => openModal(profile)} title="Edit Profile">
                      <Edit2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredProfiles.length === 0 && (
                <tr>
                  <td colSpan={6} style={{textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)'}}>
                    No crowd profiles found matching search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Edit Modal */}
      {isModalOpen && editingProfile && (
        <div className="modal-overlay" onClick={() => !isSaving && setIsModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{marginBottom: '0.5rem', color: 'var(--accent-primary)'}}>Edit Crowd Profile</h3>
            <p style={{color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>{editingProfile.place_name}</p>
            
            <form onSubmit={handleSubmit}>
              <div className="admin-form-group">
                <label>Base Crowd Level</label>
                <select 
                  className="admin-form-input"
                  value={formData.base_crowd_level || 'medium'}
                  onChange={e => setFormData({...formData, base_crowd_level: e.target.value})}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div className="admin-form-group">
                <label>Peak Hours (comma separated)</label>
                <input type="text" className="admin-form-input"
                  value={formData.peak_hours?.join(', ') || ''} 
                  onChange={e => {
                    const hours = e.target.value.split(',').map(s => s.trim()).filter(s => s);
                    setFormData({...formData, peak_hours: hours});
                  }} 
                  placeholder="e.g. 10:00-14:00, 16:00-18:00"
                />
              </div>

              <div className="admin-form-group">
                <label>Peak Season Months (comma separated numbers 1-12)</label>
                <input type="text" className="admin-form-input"
                  value={formData.peak_season_months?.join(', ') || ''} 
                  onChange={e => {
                    const months = e.target.value.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
                    setFormData({...formData, peak_season_months: months});
                  }} 
                  placeholder="e.g. 10, 11, 12, 1, 2, 3, 4"
                />
              </div>

              <div className="admin-form-group" style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                <input type="checkbox" id="is_outdoor"
                  checked={formData.is_outdoor ?? true}
                  onChange={e => setFormData({...formData, is_outdoor: e.target.checked})}
                />
                <label htmlFor="is_outdoor" style={{marginBottom: 0}}>Is Outdoor Location?</label>
              </div>

              <div className="admin-form-group" style={{marginTop: '1rem'}}>
                <label>Notes</label>
                <textarea className="admin-form-textarea"
                  value={formData.notes || ''} 
                  onChange={e => setFormData({...formData, notes: e.target.value})} 
                  placeholder="Any specific crowd behavior notes..."
                />
              </div>

              <div style={{display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem'}}>
                <button type="button" className="admin-btn-icon" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="admin-action-btn" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CrowdProfileEditor;
