import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import AdminPanel from './admin/AdminPanel'
import AdminLogin from './admin/AdminLogin'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        {/* User-facing app on root */}
        <Route path="/" element={<App />} />
        
        {/* Admin login */}
        <Route path="/admin/login" element={<AdminLogin />} />
        
        {/* Admin panel layout with nested routes */}
        <Route path="/admin/*" element={<AdminPanel />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
