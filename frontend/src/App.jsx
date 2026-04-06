import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import Home from './pages/Home';
import Tournaments from './pages/Tournaments';
import TournamentDetail from './pages/TournamentDetail';
import PlayerProfile from './pages/PlayerProfile';
import PlayersList from './pages/PlayersList';
import AdminHomepage from './pages/AdminHomepage';
import AuthCallback from './pages/AuthCallback';
import AdminTournamentsList from './pages/AdminTournamentsList';
import AdminMatchUpload from './pages/AdminMatchUpload';
import MatchDetail from './pages/MatchDetail';
import PlayerProfileEdit from './pages/PlayerProfileEdit'; // Добавлен импорт
import AdminApplications from './pages/AdminApplications';
import AdminTournamentForm from './pages/AdminTournamentForm';
import DraftPage from './pages/DraftPage';

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'white'}}>Loading...</div>;
  }
  
  if (!user || user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* ПУБЛИЧНЫЕ МАРШРУТЫ */}
          <Route path="/" element={<Home />} />
          <Route path="/tournaments" element={<Tournaments />} />
          <Route path="/tournaments/:id" element={<TournamentDetail />} />
          
          <Route path="/players" element={<PlayersList />} />
          <Route path="/players/:id" element={<PlayerProfile />} />
          <Route path="/players/:id/edit" element={<PlayerProfileEdit />} /> {/* Добавлен маршрут */}
          
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/draft/:tournamentId" element={<DraftPage />} />
          <Route path="/matches/:id" element={<MatchDetail />} />
          {/* <Route path="/encounters/:id" element={<div>Encounter page — coming soon</div>} /> */}

          {/* АДМИНСКАЯ ЗОНА */}
          <Route path="/admin/homepage" element={<AdminRoute><AdminHomepage /></AdminRoute>} />
          <Route path="/admin/tournaments" element={<AdminRoute><AdminTournamentsList /></AdminRoute>} />
          <Route path="/admin/tournaments/new" element={<AdminRoute><AdminTournamentForm /></AdminRoute>} />
          <Route path="/admin/matches/upload" element={<AdminRoute><AdminMatchUpload /></AdminRoute>} />
          <Route path="/admin/tournaments/:tournamentId/applications" element={<AdminApplications />} />
          <Route path="/admin/tournaments/new" element={<AdminTournamentForm />} />
          <Route path="/admin/tournaments/:id/edit" element={<AdminRoute><AdminTournamentForm /></AdminRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}