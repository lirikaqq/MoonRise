// frontend/src/pages/AdminTournamentForm.jsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { tournamentsApi } from '../api/tournaments'; // Убедись, что путь верный

// Массивы для селекторов, чтобы не хардкодить
const FORMAT_OPTIONS = [
  { value: 'draft', label: 'Draft' },
  { value: 'mix', label: 'Mix' },
];

const STATUS_OPTIONS = [
  { value: 'upcoming', label: 'Upcoming' },
  { value: 'registration', label: 'Registration' },
  { value: 'checkin', label: 'Check-in' },
  { value: 'draft', label: 'Draft' },
  { value: 'ongoing', label: 'Ongoing' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];


// --- Компонент инпута для чистоты кода ---
const FormInput = ({ label, name, children, required }) => (
  <div>
    <label htmlFor={name} className="block mb-2 text-sm font-bold text-[var(--accent-light)]">
      {label} {required && <span className="text-red-400">*</span>}
    </label>
    {children}
  </div>
);


export default function AdminTournamentForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [tournament, setTournament] = useState({
    title: '',
    description: '',
    format: 'draft',
    status: 'upcoming',
    start_date: '',
    end_date: '',
    max_participants: 100,
    cover_url: '',
    registration_open: null,
    registration_close: null,
    checkin_open: null,
    checkin_close: null,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isEditing) {
      setLoading(true);
      tournamentsApi.getById(id)
        .then(data => {
          const formatDateTime = (dt) => dt ? new Date(dt).toISOString().slice(0, 16) : '';
          setTournament({
            ...data,
            start_date: formatDateTime(data.start_date),
            end_date: formatDateTime(data.end_date),
            registration_open: formatDateTime(data.registration_open),
            registration_close: formatDateTime(data.registration_close),
            checkin_open: formatDateTime(data.checkin_open),
            checkin_close: formatDateTime(data.checkin_close),
          });
        })
        .catch(() => setError('Failed to load tournament data.'))
        .finally(() => setLoading(false));
    }
  }, [id, isEditing]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTournament(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const toISOStringOrNull = (dt) => dt ? new Date(dt).toISOString() : null;

    const dataToSend = {
      ...tournament,
      start_date: toISOStringOrNull(tournament.start_date),
      end_date: toISOStringOrNull(tournament.end_date),
      registration_open: toISOStringOrNull(tournament.registration_open),
      registration_close: toISOStringOrNull(tournament.registration_close),
      checkin_open: toISOStringOrNull(tournament.checkin_open),
      checkin_close: toISOStringOrNull(tournament.checkin_close),
      // ВАЖНО: Принудительно конвертируем в число перед отправкой
      max_participants: parseInt(tournament.max_participants, 10),
    };

    try {
      if (isEditing) {
        // Тебе нужно будет добавить метод update в tournamentsApi
        await tournamentsApi.update(id, dataToSend); 
      } else {
        await tournamentsApi.create(dataToSend);
      }
      navigate('/admin/tournaments');
    } catch (err) {
      const errorDetail = err.response?.data?.detail;
      if (typeof errorDetail === 'string') {
        setError(errorDetail);
      } else {
        setError('An unexpected error occurred. Check console for details.');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEditing) return <div className="text-center mt-10 font-bold text-xl">Loading Tournament...</div>;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 text-white">
      <h1 className="text-4xl mb-8 font-bold" style={{ fontFamily: 'Palui', color: 'var(--accent-light)' }}>
        {isEditing ? 'Edit Tournament' : 'Create New Tournament'}
      </h1>
      
      {error && (
          <div className="bg-red-900 border border-red-600 text-white p-4 rounded-lg mb-6 text-sm">
              <p className="font-bold mb-2">Error:</p>
              <pre className="whitespace-pre-wrap break-all">{error}</pre>
          </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-8 bg-[var(--block-bg)] p-6 sm:p-8 rounded-lg border border-[var(--border)]">
        
        {/* --- Основная информация --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormInput label="Title" name="title" required>
            <input type="text" name="title" value={tournament.title} onChange={handleChange} required className="form-input" />
          </FormInput>
          <FormInput label="Max Participants" name="max_participants" required>
            <input type="number" name="max_participants" value={tournament.max_participants} onChange={handleChange} required className="form-input" />
          </FormInput>
        </div>

        <FormInput label="Description" name="description">
          <textarea name="description" value={tournament.description || ''} onChange={handleChange} rows="4" className="form-input"></textarea>
        </FormInput>

        {/* --- Формат и Статус --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormInput label="Format" name="format" required>
            <select name="format" value={tournament.format} onChange={handleChange} className="form-select">
              {FORMAT_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </FormInput>
          <FormInput label="Status" name="status" required>
            <select name="status" value={tournament.status} onChange={handleChange} className="form-select">
              {STATUS_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </FormInput>
        </div>

        {/* --- Даты турнира --- */}
        <div className="p-4 rounded-md bg-gray-900/50 border border-gray-700 space-y-6">
            <h3 className="font-bold text-lg text-[var(--accent)]">Tournament Dates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormInput label="Start Date" name="start_date" required>
                    <input type="datetime-local" name="start_date" value={tournament.start_date} onChange={handleChange} required className="form-input" />
                </FormInput>
                <FormInput label="End Date" name="end_date" required>
                    <input type="datetime-local" name="end_date" value={tournament.end_date} onChange={handleChange} required className="form-input" />
                </FormInput>
            </div>
        </div>

        {/* --- Даты регистрации (Опционально) --- */}
        <div className="p-4 rounded-md bg-gray-900/50 border border-gray-700 space-y-6">
            <h3 className="font-bold text-lg text-[var(--accent)]">Registration Dates (Optional)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormInput label="Registration Open" name="registration_open">
                    <input type="datetime-local" name="registration_open" value={tournament.registration_open || ''} onChange={handleChange} className="form-input" />
                </FormInput>
                <FormInput label="Registration Close" name="registration_close">
                    <input type="datetime-local" name="registration_close" value={tournament.registration_close || ''} onChange={handleChange} className="form-input" />
                </FormInput>
            </div>
        </div>


        {/* --- Кнопки --- */}
        <div className="flex justify-end gap-4 pt-4 border-t border-gray-700">
          <Link to="/admin/tournaments" className="px-6 py-2 rounded font-bold bg-gray-600 hover:bg-gray-500 transition-colors">
            Cancel
          </Link>
          <button type="submit" disabled={loading} className="px-6 py-2 rounded font-bold bg-[var(--accent)] hover:bg-[var(--accent-dark)] text-[var(--bg)] transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed">
            {loading ? 'Saving...' : 'Save Tournament'}
          </button>
        </div>
      </form>
    </div>
  );
}