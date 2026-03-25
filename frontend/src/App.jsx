import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Home from './pages/Home'
import Tournaments from './pages/Tournaments'
import TournamentDetail from './pages/TournamentDetail'
import PlayerProfile from './pages/PlayerProfile'
import AdminHomepage from './pages/AdminHomepage'      // ← добавить
import AuthCallback from './pages/AuthCallback'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tournaments" element={<Tournaments />} />
          <Route path="/tournaments/:id" element={<TournamentDetail />} />
          <Route path="/players/:id" element={<PlayerProfile />} />
          <Route path="/admin/homepage" element={<AdminHomepage />} />  {/* ← добавить */}
          <Route path="/auth/callback" element={<AuthCallback />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}