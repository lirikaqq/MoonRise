import { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import { tournamentsApi } from '../api/tournaments';
import './AdminTournamentsList.css'; // Создадим этот файл

import { useAuth } from '../context/AuthContext'; // <-- Используем хук
import { useDeleteItem } from '../hooks/useDeleteItem';
import ConfirmModal from '../components/ConfirmModal/ConfirmModal';

export default function AdminTournamentsList() {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

   const { modalState, openDeleteModal, closeDeleteModal, confirmDelete } = useDeleteItem(
    (deletedId) => {
      setTournaments(prev => prev.filter(t => t.id !== deletedId));
    }
  );

  useEffect(() => {
    const fetchTournaments = async () => {
      setLoading(true);
      try {
        const data = await tournamentsApi.getAll();
        setTournaments(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Failed to fetch tournaments:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTournaments();
  }, []);
  
  const handleConfirmDelete = () => {
    confirmDelete(async (id) => {
      await tournamentsApi.delete(id);
    });
  };

  if (!user || user.role !== 'admin') {
    return (
      <div>
        <Header />
        <main className="admin-list-main">
          <div className="admin-list-container">
            <h1>Access Denied</h1>
            <p>You must be an administrator to view this page.</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="admin-list-page">
      <Header />
      <main className="admin-list-main">
        <div className="admin-list-container">
          <div className="admin-list-header">
            <h1>Tournaments Management</h1>
            <Link to="/admin/tournaments/new" className="admin-list-header__add-btn">
              + Create Tournament
            </Link>
          </div>

          {loading ? (
            <div className="admin-list-feedback">Loading tournaments...</div>
          ) : (
            <div className="admin-list">
              {tournaments.map(t => (
                <div key={t.id} className="admin-list-item">
                  <div className="admin-list-item__info">
                    <span className={`admin-list-item__status-dot status--${t.status}`}></span>
                    <Link to={`/admin/tournaments/edit/${t.id}`} className="admin-list-item__title">{t.title}</Link>
                    <span className="admin-list-item__meta">{t.format} &middot; {new Date(t.start_date).toLocaleDateString()}</span>
                  </div>
                  <div className="admin-list-item__actions">
                    <Link to={`/tournaments/${t.id}`} className="admin-list-item__action-btn" title="View Public Page">👁️</Link>
                    <Link to={`/admin/tournaments/edit/${t.id}`} className="admin-list-item__action-btn" title="Edit">✏️</Link>
                    <button 
                      className="admin-list-item__action-btn admin-list-item__action-btn--delete" 
                      title="Delete Tournament"
                      onClick={() => openDeleteModal(t)}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />

      <ConfirmModal
        isOpen={modalState.isOpen}
        title="Удалить турнир?"
        message={
          <>
            Вы уверены, что хотите удалить <strong>{modalState.item?.title}</strong>?
            <br/>
            Это действие удалит все команды, матчи и статистику турнира.
          </>
        }
        isLoading={modalState.isLoading}
        error={modalState.error}
        onConfirm={handleConfirmDelete}
        onCancel={closeDeleteModal}
      />
    </div>
  );
}