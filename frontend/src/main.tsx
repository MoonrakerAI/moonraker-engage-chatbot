import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Analytics from './components/Analytics'
import ChatbotSetup from './components/ChatbotSetup'
import Sidebar from './components/Sidebar'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <div className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/chatbot-setup" element={<ChatbotSetup />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)