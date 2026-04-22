import React from 'react';
import './PlayerCard.css';

const PlayerCard = ({ player, stats = {} }) => {
  if (!player || !stats) {
    return null;
  }

  // maps_count вместо tournaments_count (так называется поле в API)
  const { maps_count = 0, wins = 0, winrate = 0 } = stats;

  return (
    <div className="player-card">
      <div className="player-card__accent-line" />

      <div className="player-card__header">
        <div className="player-card__avatar-wrapper">
            <img
              className="player-card__avatar"
            src={player.avatar_url || '/assets/avatars/default.png'}
              alt={player.username || player.nickname}
            />
          {!player.avatar_url && (
            <div className="player-card__avatar-letter">
              {player.username?.[0]?.toUpperCase() || '?'}
            </div>
          )}
        </div>

        <div className="player-card__profile-info">
          <div className="player-card__nickname">{player.nickname || player.username || 'Unknown Player'}</div>

          <div className="player-card__battletag-row">
            <span className="player-card__battletag">{player.battle_tag || player.username + '#0000'}</span>
            {player.battle_tag_count && (
              <span className="player-card__battletag-badge">+{player.battle_tag_count}</span>
            )}
          </div>
          
          {(player.twitch_username || player.twitch) && (
            <div className="player-card__usertag">
              <img
                className="player-card__usertag-icon"
                src="/assets/icons/mini_twitch.svg"
                alt="Twitch"
              />
              <span className="player-card__usertag-text">
                {player.twitch_username || player.twitch}
              </span>
            </div>
          )}
        </div>
      </div>
      <hr className="player-card__divider" />

      <div className="player-card__statsrow">
        <div className="player-card__stat-item">
          {/* maps_count вместо tournaments_count */}
          <span className="player-card__stat-value">{maps_count}</span>
          <span className="player-card__stat-label">Tournaments</span>
        </div>
        <div className="player-card__stat-item">
          <span className="player-card__stat-value">{wins}</span>
          <span className="player-card__stat-label">Wins</span>
        </div>
        <div className="player-card__stat-item">
          <span className="player-card__stat-value">{Math.round(winrate) || 0}%</span>
          <span className="player-card__stat-label">Winrate</span>
        </div>
      </div>
    </div>
  );
};

export default PlayerCard;