import React, { useState } from 'react';
import RoleSelector from '../RoleSelector/RoleSelector';
import BattleTagSelector from '../BattleTagSelector/BattleTagSelector';
import tournamentsApi from '../../api/tournaments';
import './RegisterModal.css';

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

export default function RegisterModal({
  tournament,
  isOpen,
  onClose,
  onSuccess,
  userBattletags = [],
}) {
  const [formData, setFormData] = useState({
    primaryRole: '',
    secondaryRole: '',
    bio: '',
    ratingClaimed: '',
    selectedBattletagId: null,
    newBattletag: null,
    confirmedFriendRequest: false,
    confirmedRules: false, // ← Новый стейт
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const isDraft = tournament?.format === 'draft';

  const validateForm = () => {
    const newErrors = {};

    if (!formData.primaryRole) newErrors.primaryRole = 'Выберите основную роль';
    if (!formData.secondaryRole) newErrors.secondaryRole = 'Выберите дополнительную роль';
    if (formData.primaryRole && formData.secondaryRole && formData.primaryRole === formData.secondaryRole) {
      newErrors.roles = 'Роли не могут совпадать';
    }

    if (isDraft) {
      if (!formData.ratingClaimed) newErrors.ratingClaimed = 'Выберите рейтинг';
      if (!formData.selectedBattletagId && !formData.newBattletag) {
        newErrors.battletag = 'Выберите или добавьте BattleTag';
      }
    }

    // Чекбоксы проверяем всегда!
    if (!formData.confirmedFriendRequest) {
      newErrors.confirmedFriendRequest = 'Необходимо подтвердить';
    }
    if (!formData.confirmedRules) {
      newErrors.confirmedRules = 'Необходимо подтвердить';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsLoading(true);
    setSubmitError(null);

    try {
      if (isDraft) {
        await tournamentsApi.registerForDraft(tournament.id, {
          primaryRole: formData.primaryRole,
          secondaryRole: formData.secondaryRole,
          bio: formData.bio,
          ratingClaimed: formData.ratingClaimed,
          battletagId: formData.selectedBattletagId,
          newBattletag: formData.newBattletag,
          confirmedFriendRequest: formData.confirmedFriendRequest,
          confirmedRules: formData.confirmedRules
        });
      } else {
        await tournamentsApi.registerForMix(tournament.id, {
          primaryRole: formData.primaryRole,
          secondaryRole: formData.secondaryRole,
          bio: formData.bio,
          confirmedFriendRequest: formData.confirmedFriendRequest,
          confirmedRules: formData.confirmedRules
        });
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Registration error:', error);
      setSubmitError(
        error.response?.data?.detail || 'Ошибка при подаче заявки. Попробуйте позже.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="modal-close" onClick={onClose}>✕</button>

        <h2 className="modal-title font-palui">
          РЕГИСТРАЦИЯ НА {isDraft ? 'DRAFT' : 'MIX'}-ТУРНИР
        </h2>
        <p className="modal-subtitle font-palui">{tournament?.title}</p>

        <form onSubmit={handleSubmit} className="registration-form">
          
          <RoleSelector
            primaryRole={formData.primaryRole}
            secondaryRole={formData.secondaryRole}
            onPrimaryChange={(value) => setFormData(prev => ({ ...prev, primaryRole: value }))}
            onSecondaryChange={(value) => setFormData(prev => ({ ...prev, secondaryRole: value }))}
            error={errors.roles || errors.primaryRole || errors.secondaryRole}
            disabled={isLoading}
          />

          <div className="form-group">
            <label htmlFor="bio" className="font-palui">О СЕБЕ (ОПЦИОНАЛЬНО)</label>
            <textarea
              id="bio"
              value={formData.bio}
              onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
              maxLength={500}
              placeholder="Например: Играю 2 года..."
              disabled={isLoading}
              className="bio-textarea font-ponter"
            />
            <p className="char-count font-digits">{formData.bio.length}/500</p>
          </div>

          {isDraft && (
            <>
              <div className="form-group">
                <label htmlFor="rating" className="font-palui">
                  <span className="required">*</span> ВАШ РЕЙТИНГ
                </label>
                <select
                  id="rating"
                  value={formData.ratingClaimed || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, ratingClaimed: e.target.value }))}
                  disabled={isLoading}
                  className={`font-ponter ${errors.ratingClaimed ? 'input-error' : ''}`}
                >
                  <option value="">ВЫБЕРИТЕ РЕЙТИНГ...</option>
                  {RANKS.map((rank) => (
                    <option key={rank} value={rank}>{rank.toUpperCase()}</option>
                  ))}
                </select>
                {errors.ratingClaimed && <div className="form-error font-ponter">{errors.ratingClaimed}</div>}
              </div>

              <BattleTagSelector
                userBattletags={userBattletags}
                selectedBattletagId={formData.selectedBattletagId}
                newBattletag={formData.newBattletag}
                onSelectExisting={(id) => setFormData(prev => ({
                  ...prev,
                  selectedBattletagId: id,
                  newBattletag: null
                }))}
                onAddNew={(tag) => setFormData(prev => ({
                  ...prev,
                  newBattletag: tag,
                  selectedBattletagId: null
                }))}
                onRemoveNew={() => setFormData(prev => ({
                  ...prev,
                  newBattletag: null
                }))}
                error={errors.battletag}
                disabled={isLoading}
              />
            </>
          )}

          {/* ЧЕКБОКСЫ ТЕПЕРЬ ТУТ, ОНИ ВИДНЫ ДЛЯ ВСЕХ ТУРНИРОВ */}
          <div className="form-group checkbox-group" style={{ marginTop: '1rem' }}>
            <label className="font-palui" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={formData.confirmedFriendRequest}
                onChange={(e) => setFormData(prev => ({ ...prev, confirmedFriendRequest: e.target.checked }))}
                disabled={isLoading}
                style={{ width: '18px', height: '18px', marginRight: '10px' }}
              />
              <span className="required" style={{ marginRight: '5px' }}>*</span> Я ДОБАВИЛ STEVE#24919 В ДРУЗЬЯ
            </label>
            {errors.confirmedFriendRequest && (
              <div className="form-error font-ponter" style={{ marginTop: '5px' }}>{errors.confirmedFriendRequest}</div>
            )}
          </div>

          <div className="form-group checkbox-group">
            <label className="font-palui" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={formData.confirmedRules}
                onChange={(e) => setFormData(prev => ({ ...prev, confirmedRules: e.target.checked }))}
                disabled={isLoading}
                style={{ width: '18px', height: '18px', marginRight: '10px' }}
              />
              <span className="required" style={{ marginRight: '5px' }}>*</span> Я ОЗНАКОМИЛСЯ С РЕГЛАМЕНТОМ ТУРНИРА
            </label>
            {errors.confirmedRules && (
              <div className="form-error font-ponter" style={{ marginTop: '5px' }}>{errors.confirmedRules}</div>
            )}
          </div>

          {submitError && (
            <div className="alert alert-error font-ponter" style={{ marginTop: '1rem' }}>
              <strong>Ошибка:</strong> {submitError}
            </div>
          )}

          <div className="form-actions" style={{ marginTop: '1.5rem' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="btn-secondary font-palui"
            >
              ОТМЕНА
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary font-palui"
            >
              {isLoading ? 'ОТПРАВКА...' : 'ПОДАТЬ ЗАЯВКУ'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}