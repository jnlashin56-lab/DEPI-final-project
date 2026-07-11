import axios from 'axios';
import { API_BASE } from '../config';

const BASE_URL = `${API_BASE}/admin`;

// Request interceptor to attach JWT token
const api = axios.create({
  baseURL: BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('adminToken');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle 401s globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('adminToken');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string) => {
  const res = await api.post('/login', { username, password });
  return res.data; // { access_token, token_type }
};

// Places
export const getPlaces = async (page = 1, pageSize = 50, search = '') => {
  const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
  if (search) params.append('search', search);
  const res = await api.get(`/places?${params.toString()}`);
  return res.data;
};

export const createPlace = async (data: any) => {
  const res = await api.post('/places', data);
  return res.data;
};

export const updatePlace = async (id: number, data: any) => {
  const res = await api.put(`/places/${id}`, data);
  return res.data;
};

export const deletePlace = async (id: number) => {
  const res = await api.delete(`/places/${id}`);
  return res.data;
};

// Ticket Prices
export const getTicketPrices = async (search = '') => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  const res = await api.get(`/ticket-prices?${params.toString()}`);
  return res.data;
};

export const updateTicketPrice = async (id: number, data: any) => {
  const res = await api.put(`/ticket-prices/${id}`, data);
  return res.data;
};

// Bookings
export const getBookings = async (status = '') => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  const res = await api.get(`/bookings?${params.toString()}`);
  return res.data;
};

export const confirmBooking = async (id: number) => {
  const res = await api.patch(`/bookings/${id}/confirm`);
  return res.data;
};

export const cancelBooking = async (id: number) => {
  const res = await api.patch(`/bookings/${id}/cancel`);
  return res.data;
};

// Analytics
export const getAnalytics = async () => {
  const res = await api.get('/analytics');
  return res.data;
};

// Crowd Profiles
export const getCrowdProfiles = async () => {
  const res = await api.get('/crowd-profiles');
  return res.data;
};

export const updateCrowdProfile = async (placeId: number, data: any) => {
  const res = await api.put(`/crowd-profiles/${placeId}`, data);
  return res.data;
};
