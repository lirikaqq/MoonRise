import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { tournamentsApi } from '../api/tournaments';
import Header from '../components/layout/Header';
import './AdminApplications.css';

const RANKS = [
  'Bronze 5', 'Bronze 4', 'Bronze 3', 'Bronze 2', 'Bronze 1',
  'Silver 5', 'Silver 4', 'Silver 3', 'Silver 2', 'Silver 1',
  'Gold 5', 'Gold 4', 'Gold 3', 'Gold 2', 'Gold 1',
  'Platinum 5', 'Platinum 4', 'Platinum 3', 'Platinum 2', 'Platinum 1',
  'Diamond 5', 'Diamond 4', 'Diamond 3', 'Diamond 2', 'Diamond 1',
  'Master 5', 'Master 4', 'Master 3', 'Master 2', 'Master 1',
  'Grandmaster 5', 'Grandmaster 4', 'Grandmaster 3', 'Grandmaster 2', 'Grandmaster 1',
  'Champion 5', 'Champion 4', 'Champion 3', 'Champion 2', 'Champion 1',
  'Unranked',
];

const STATUS_FILTERS = [
  { id: 'all', label: 'Все заявки' },
  { id: 'pending', label: 'На рассмотрении' },
  { id: 'registered', label: 'Одобренные' },
  { id: 'rejected', label: 'Отклонённые' },
];

export default function AdminApplications() {
  const { tournamentId } = useParams();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [ratingOverrides, setRatingOverrides] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        setLoading(true);
        const data = await tournamentsApi.getApplications(
          tournamentId,
          statusFilter === 'all' ? null : statusFilter
        );
        setApplications(data.applications || []);
      } catch (error) {
        console.error('Error loading applications:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchApplications();
  }, [tournamentId, statusFilter]);

  const handleApprove = async (userId) => {
    try {
      const ratingApproved = ratingOverrides[userId] || null;
      await tournamentsApi.approveApplication(tournamentId, userId, ratingApproved);

      const data = await tournamentsApi.getApplications(
        tournamentId,
        statusFilter === 'all' ? null : statusFilter
      );
      setApplications(data.applications || []);
    } catch (error) {
      console.error('Error approving application:', error);
    }
  };

  const handleReject = async (userId) => {
    const reason = prompt('Укажите причину отклонения:');
    if (!reason) return;

    try {
      await tournamentsApi.rejectApplication(tournamentId, userId, reason);

      const data = await tournamentsApi.getApplications(
        tournamentId,
        statusFilter === 'all' ? null : statusFilter
      );
      setApplications(data.applications || []);
    } catch (error) {
      console.error('Error rejecting application:', error);
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedApplications = React.useMemo(() => {
    const sortableItems = [...applications];
    if (sortConfig.key) {
      sortableItems.sort((a, b) => {
        const aValue = a[sortConfig.key] || (a.application_data?.[sortConfig.key] || '');
        const bValue = b[sortConfig.key] || (b.application_data?.[sortConfig.key] || '');

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sortableItems;
  }, [applications, sortConfig]);

  const filteredApplications = sortedApplications.filter(app => {
    const appData = app.application_data || {};
    const searchLower = searchQuery.toLowerCase();
    const userName = (app.user_username || '').toLowerCase();

    return (
      app.user_id.toString().includes(searchQuery) ||
      userName.includes(searchLower) ||
      (appData.primary_role || '').toLowerCase().includes(searchLower) ||
      (appData.secondary_role || '').toLowerCase().includes(searchLower) ||
      (appData.rating_claimed || '').toLowerCase().includes(searchLower) ||
      (appData.battletag_value || '').toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="admin-page">
      <Header />
      <div className="admin-container">
        <h1 className="admin-title">Управление заявками</h1>

        <div className="admin-controls">
          <div className="admin-search">
            <input
              type="text"
              placeholder="Поиск по нику или роли..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="admin-filters">
            {STATUS_FILTERS.map((filter) => (
              <button
                key={filter.id}
                className={`admin-filter-btn ${statusFilter === filter.id ? 'active' : ''}`}
                onClick={() => setStatusFilter(filter.id)}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="admin-loading">Загрузка...</div>
        ) : (
          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>№</th>
                  <th onClick={() => handleSort('user_username')}>
                    Игрок {sortConfig.key === 'user_username' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>Роли</th>
                  <th onClick={() => handleSort('rating_claimed')}>
                    Рейтинг {sortConfig.key === 'rating_claimed' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>BattleTag</th>
                  <th onClick={() => handleSort('status')}>
                    Статус {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {filteredApplications.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="admin-no-data">Нет заявок</td>
                  </tr>
                ) : (
                  filteredApplications.map((app, index) => {
                    const appData = app.application_data || {};
                    const isDraft = appData.rating_claimed !== undefined;

                    return (
                      <tr key={app.id} className={`admin-table-row ${app.status}`}>
                        <td className="font-digits">{index + 1}</td>
                        <td className="font-palui" style={{ color: '#13c8b0' }}>
                          {app.user_display_name || app.user_username || `ID: ${app.user_id}`}
                        </td>
                        <td>
                          {appData.primary_role}/{appData.secondary_role}
                        </td>
                        <td>
                          {isDraft && (
                            <div className="admin-rating-cell">
                              <span>{appData.rating_claimed}</span>
                              {app.status === 'pending' && (
                                <select
                                  value={ratingOverrides[app.user_id] || ''}
                                  onChange={(e) => setRatingOverrides(prev => ({
                                    ...prev,
                                    [app.user_id]: e.target.value
                                  }))}
                                  className="admin-rating-select"
                                >
                                  <option value="">Без изменений</option>
                                  {RANKS.map(rank => (
                                    <option key={rank} value={rank}>{rank}</option>
                                  ))}
                                </select>
                              )}
                            </div>
                          )}
                        </td>
                        <td>{appData.battletag_value || '—'}</td>
                        <td>
                          <span className={`admin-status-badge ${app.status}`}>
                            {app.status === 'pending' ? 'Ожидание' :
                             app.status === 'registered' ? 'Одобрено' : 'Отклонено'}
                          </span>
                        </td>
                        <td>
                          {app.status === 'pending' && (
                            <>
                              <button
                                className="admin-approve-btn"
                                onClick={() => handleApprove(app.user_id)}
                              >
                                ✓ Одобрить
                              </button>
                              <button
                                className="admin-reject-btn"
                                onClick={() => handleReject(app.user_id)}
                              >
                                ✗ Отклонить
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}