import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { playersApi } from '../api/players';
import './PlayersList.css';

import { useAuth } from '../context/AuthContext';
import { useDeleteItem } from '../hooks/useDeleteItem';
import ConfirmModal from '../components/ConfirmModal/ConfirmModal';

export default function PlayersList() {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { modalState, openDeleteModal, closeDeleteModal, confirmDelete } = useDeleteItem(
    (deletedId) => {
      setPlayers(prev => prev.filter(p => p.id !== deletedId));
    }
  );

  const fetchPlayers = async (searchQuery = '') => {
    setLoading(true);
    try {
      const data = await playersApi.getAll(searchQuery);
      
      // ДЕБАГ-ВЫВОД №1: ЧТО ПРИШЛО ИЗ API
      console.log('--- DEBUG: API Response Data ---', data);
      
      setPlayers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch players:', err);
      setPlayers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlayers();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchPlayers(search);
  };
  
  const handleConfirmDelete = () => {
    confirmDelete(async (id) => {
      await playersApi.delete(id);
    });
  };

  // ДЕБАГ-ВЫВОД №2: ЧТО ЛЕЖИТ В СОСТОЯНИИ ПЕРЕД РЕНДЕРОМ
  console.log('--- DEBUG: Component State (players) ---', players);

  return (
    <div className="players-catalog-page">
      <Header />
      <main className="profile-main">
        <div className="profile-container">
          <div className="players-header">
            <div className="players-title">
              <h1>Players Catalog</h1>
              <p>Find teammates or opponents</p>
            </div>
            <form onSubmit={handleSearch} className="players-search-form">
              <input
                type="text"
                placeholder="Search by nickname..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="players-search-input"
              />
              <button type="submit" className="players-search-button">Search</button>
            </form>
          </div>
          {loading ? (
            <div className="players-feedback-block"><h3>LOADING...</h3></div>
          ) : (
            <>
              {players && players.length > 0 ? (
                <div className="players-grid">
                  {players.map(player => (
                    <div key={player.id} className="profile-card-wrapper">
                      {isAdmin && (
                        <button
                          className="profile-card__delete-btn"
                          title={`Delete ${player.username}`}
                          onClick={() => openDeleteModal(player)}
                        >
                          🗑️
                        </button>
                      )}
                      <Link
                        to={`/players/${player.id}`}
                        state={{ from: { url: '/players', label: 'PLAYERS' } }}
                        className="profile-card"
                        style={{ textDecoration: 'none' }}
                      >
                        {/* 👇 ВОТ ЭТА ЧАСТЬ БЫЛА ПОТЕРЯНА 👇 */}
                        <div className="profile-avatar-wrap">
                          {player.avatar_url ? (
                            <img
                              src={player.avatar_url}
                              alt={player.username}
                              className="profile-avatar"
                            />
                          ) : (
                            <div className="profile-avatar-placeholder">
                              {player.username ? player.username[0].toUpperCase() : '?'}
                            </div>
                          )}
                          <div className="profile-avatar-border"></div>
                        </div>
                        <h2 className="profile-username">{player.username}</h2>
                        <span className={`profile-role-badge role-${player.role || 'player'}`}>
                          {player.role || 'player'}
                        </span>
                        {player.division && (
                          <div className="profile-division" style={{ marginTop: '12px' }}>
                            <span className="profile-division-label">Main Role</span>
                            <span className="profile-division-value">{player.division}</span>
                          </div>
                        )}
                        {/* 👆 КОНЕЦ ПОТЕРЯННОЙ ЧАСТИ 👆 */}
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="players-feedback-block"><h3>NO PLAYERS FOUND</h3></div>
              )}
            </>
          )}
        </div>
      </main>
      <Footer />
      <ConfirmModal
        isOpen={modalState.isOpen}
        title="Удалить игрока?"
        message={<>Вы уверены, что хотите удалить <strong>{modalState.item?.username}</strong>?<br/>Все данные игрока, включая статистику в матчах, будут уничтожены.</>}
        isLoading={modalState.isLoading}
        error={modalState.error}
        onConfirm={handleConfirmDelete}
        onCancel={closeDeleteModal}
      />
    </div>
  );
}