import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import WaitingChats from './pages/WaitingChats'
import MyChats from './pages/MyChats'
import ChatDetail from './pages/ChatDetail'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/waiting" element={<WaitingChats />} />
        <Route path="/chats" element={<MyChats />} />
        <Route path="/chats/:sessionId" element={<ChatDetail />} />
      </Route>
    </Routes>
  )
}
