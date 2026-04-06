// frontend/src/pages/DraftPage.jsx

import { useDraft } from '../hooks/useDraft';
import { useAuth } from '../context/AuthContext';

// Импортируем CSS
import './DraftPage.css'; 

// Импортируем наши компоненты-заглушки
import DraftPlayerPool from '../components/draft/DraftPlayerPool';
import DraftTeamsPanel from '../components/draft/DraftTeamsPanel';
import DraftTimer from '../components/draft/DraftTimer';



export default function DraftPage() {
  const { user } = useAuth();
  const sessionId = 2; // Хардкод для теста

  const { draftState, loading, error, isConnected, makePick } = useDraft(sessionId);

  if (loading) return <div style={{ textAlign: 'center', color: 'white', marginTop: '5rem' }}>Loading Draft...</div>;
  if (error) return <div style={{ textAlign: 'center', color: 'red', marginTop: '5rem' }}>{error}</div>;
  if (!draftState) return <div style={{ textAlign: 'center', color: 'gray', marginTop: '5rem' }}>No draft data found.</div>;

  return (
    <div className="draft-page">
      <div className="draft-component-placeholder" style={{ marginBottom: '1rem' }}>
        <DraftTimer 
          draftState={draftState} 
          currentUser={user}
          isConnected={isConnected}
        />
      </div>
      
      <main className="draft-main-area">
        <div className="draft-pool-container draft-component-placeholder">
          <DraftPlayerPool 
          players={draftState.player_pool}
          currentUser={user}
          draftState={draftState}
          makePick={makePick} // <-- ПЕРЕДАЕМ ФУНКЦИЮ
           />
        </div>
        
        <aside className="draft-teams-container draft-component-placeholder">
          <DraftTeamsPanel 
            captains={draftState.captains}
            picks={draftState.picks}
          />
        </aside>
      </main>
    </div>
  );
}