import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom'; // Убедись что Link импортирован
import { useAuth } from '../context/AuthContext';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { playersApi } from '../api/players';
import './PlayerProfile.css';
import PlayerMatchHistory from '../components/player/PlayerMatchHistory'; // Добавлен импорт

function TournamentHistoryCard({ tournament }) {
  const formattedDate = new Date(tournament.start_date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  return (
    <Link to={`/tournaments/${tournament.id}`} className="tournament-history-card">
      <img
        src={tournament.cover_url || '/assets/images/grid-bg.png'}
        alt={tournament.title}
        className="tournament-history-cover"
      />
      <div className="tournament-history-info">
        <h4 className="tournament-history-title">{tournament.title}</h4>
        <div className="tournament-history-meta">
          <span>{formattedDate}</span>
          <span>•</span>
          <span>{tournament.format.toUpperCase()}</span>
          <span>•</span>
          <span>{tournament.participants_count} / {tournament.max_participants || '∞'}</span>
        </div>
      </div>
    </Link>
  );
}

export default function PlayerProfile() {
  const { id } = useParams();
  const { user: currentUser } = useAuth();
  const [player, setPlayer] = useState(null);
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;

    const loadData = async () => {
      try {
        setLoading(true);
        const playerData = await playersApi.getById(id);
        setPlayer(playerData);
        
        try {
          const tournamentsData = await playersApi.getPlayerTournaments(id);
          setTournaments(tournamentsData);
        } catch {
          setTournaments([]);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id]);

  const isOwnProfile = currentUser && currentUser.id === parseInt(id);

  if (!id || (loading && !player)) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-main">
          <div style={{ textAlign: 'center', color: 'white', marginTop: '80px' }}>LOADING PROFILE...</div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !player) {
    return (
      <div className="profile-page">
        <Header />
        <main className="profile-main">
          <div style={{ textAlign: 'center', color: 'white', marginTop: '80px' }}>PLAYER NOT FOUND</div>
        </main>
        <Footer />
      </div>
    );
  }

  const primaryTag = player.battletags?.find(t => t.is_primary) || player.battletags?.[0];

  return (
    <div className="profile-page">
      <Header />
      <main className="profile-main">
        <div className="profile-container">
          <div className="profile-breadcrumb">
            <Link to="/tournaments">TOURNAMENTS</Link>
            <span className="profile-breadcrumb-sep">›</span>
            <Link to="/players">PLAYERS</Link>
            <span className="profile-breadcrumb-sep">›</span>
            <span>{player.username}</span>
          </div>

          <div className="profile-layout">
            <aside className="profile-sidebar">
              <div className="profile-card">
                <div className="profile-avatar-wrap">
                  {player.avatar_url ? (
                    <img src={player.avatar_url} alt={player.username} className="profile-avatar" />
                  ) : (
                    <div className="profile-avatar-placeholder">
                      {player.username ? player.username[0].toUpperCase() : '?'}
                    </div>
                  )}
                  <div className="profile-avatar-border"></div>
                </div>

                <h1 className="profile-username">{player.username}</h1>
                <span className={`profile-role-badge role-${player.role || 'player'}`}>
                  {player.role || 'player'}
                </span>

                {primaryTag && (
                  <div className="profile-battletag">{primaryTag.tag}</div>
                )}

                {player.division && (
                  <div className="profile-division">
                    <span className="profile-division-label">Main Role</span>
                    <span className="profile-division-value">{player.division}</span>
                  </div>
                )}

                <div className="profile-status" style={{ marginTop: '10px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent)' }}></span>
                  <span>Online</span>
                </div>
              </div>
              
              {/* ─── ИСПРАВЛЕНО: КНОПКА ЗАМЕНЕНА НА ССЫЛКУ ───────────────── */}
              {isOwnProfile && (
                <Link to={`/players/${id}/edit`} className="button-primary" style={{ width: '100%', textDecoration: 'none', display: 'block', textAlign: 'center' }}>
                  EDIT PROFILE
                </Link>
              )}
              {/* ────────────────────────────────────────────────────────── */}
            </aside>

            <div className="profile-content">
              {tournaments.length > 0 ? (
                tournaments.map(t => <TournamentHistoryCard key={t.id} tournament={t} />)
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', height: '100%', minHeight: '300px' }}>
                  <div style={{ fontSize: '40px', marginBottom: '16px' }}>🏆</div>
                  <h3 className="profile-username" style={{ fontSize: '20px' }}>NO TOURNAMENTS YET</h3>
                  <p style={{ color: 'var(--accent-dark)', margin: '8px 0 24px' }}>TOURNAMENT HISTORY WILL APPEAR HERE</p>
                  <Link to="/tournaments" className="button-primary" style={{ padding: '8px 24px' }}>FIND TOURNAMENT</Link>
                </div>
              )}
              
              {/* ─── ДОБАВЛЕНО: КОМПОНЕНТ ИСТОРИИ МАТЧЕЙ ────────────────── */}
              <PlayerMatchHistory userId={id} />
              {/* ────────────────────────────────────────────────────────── */}
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}