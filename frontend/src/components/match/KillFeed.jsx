import { useState, useEffect, useRef } from 'react';
import './KillFeed.css';

const WEAPON_ICONS = {
  'Primary Fire': '/assets/icons/weapon-primary.svg',
  'Secondary Fire': '/assets/icons/weapon-secondary.svg',
  'Ultimate': '/assets/icons/weapon-ultimate.svg',
  'Melee': '/assets/icons/weapon-melee.svg',
  'Ability 1': '/assets/icons/weapon-ability1.svg',
  'Ability 2': '/assets/icons/weapon-ability2.svg',
  'Crouch': '/assets/icons/weapon-melee.svg',
};

function getWeaponIcon(weapon) {
  return WEAPON_ICONS[weapon] || '/assets/icons/weapon-primary.svg';
}

function KillEntry({ kill, index }) {
  return (
    <div className={`kf-entry ${kill.is_first_blood ? 'kf-entry--fb' : ''}`} style={{ animationDelay: `${index * 0.05}s` }}>
      {/* Killer */}
      <div className="kf-side kf-killer">
        <div className="kf-hero-badge kf-hero-badge--killer" title={kill.killer_hero}>
          {kill.killer_hero?.substring(0, 3).toUpperCase() || '?'}
        </div>
        <span className="kf-name" title={kill.killer_name}>{kill.killer_name}</span>
        {kill.is_first_blood && <span className="kf-fb-badge" title="First Blood">FB</span>}
      </div>

      {/* Weapon / Kill info */}
      <div className="kf-weapon">
        <span className="kf-weapon-text" title={kill.weapon}>{kill.weapon?.split(' ')[0] || '?'}</span>
        {kill.is_headshot && <span className="kf-hs" title="Headshot">HS</span>}
        {kill.is_critical && !kill.is_headshot && <span className="kf-crit" title="Critical hit">!</span>}
      </div>

      {/* Victim */}
      <div className="kf-side kf-victim">
        <div className="kf-hero-badge kf-hero-badge--victim" title={kill.victim_hero}>
          {kill.victim_hero?.substring(0, 3).toUpperCase() || '?'}
        </div>
        <span className="kf-name" title={kill.victim_name}>{kill.victim_name}</span>
      </div>

      {/* Assists */}
      {(kill.offensive_assists?.length > 0 || kill.defensive_assists?.length > 0) && (
        <div className="kf-assists">
          {kill.offensive_assists?.map((a, i) => (
            <span
              key={`oa-${i}`}
              className="kf-assist kf-assist-off"
              title={`Offensive assist: ${a.player_name} (${a.hero_name})`}
            >
              {a.player_name.substring(0, 3).toUpperCase()}
            </span>
          ))}
          {kill.defensive_assists?.map((a, i) => (
            <span
              key={`da-${i}`}
              className="kf-assist kf-assist-def"
              title={`Defensive assist: ${a.player_name} (${a.hero_name})`}
            >
              {a.player_name.substring(0, 3).toUpperCase()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function KillFeed({ matchId }) {
  const [kills, setKills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeRound, setActiveRound] = useState(0);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!matchId) return;

    const fetchKills = async () => {
      try {
        setLoading(true);
        const data = await import('../../api/matches').then(m => m.getMatchKillFeed(matchId));
        setKills(data || []);
        if (data?.length > 0) {
          setActiveRound(data[0].round_number);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchKills();
  }, [matchId]);

  if (loading) return <div className="kf-loading">Loading kill feed...</div>;
  if (error) return <div className="kf-error">Error: {error}</div>;
  if (kills.length === 0) return <div className="kf-empty">No kills recorded</div>;

  const rounds = [...new Set(kills.map(k => k.round_number))].sort((a, b) => a - b);
  const roundKills = kills.filter(k => k.round_number === activeRound);

  return (
    <div className="kill-feed-container">
      <h3 className="kf-title">Kill Feed</h3>

      {/* Round selector */}
      {rounds.length > 1 && (
        <div className="kf-rounds">
          {rounds.map(r => (
            <button
              key={r}
              className={`kf-round-btn ${activeRound === r ? 'kf-round-btn--active' : ''}`}
              onClick={() => setActiveRound(r)}
            >
              Round {r}
            </button>
          ))}
        </div>
      )}

      {/* Kill entries */}
      <div className="kf-list" ref={containerRef}>
        {roundKills.map((kill, i) => (
          <KillEntry key={kill.id} kill={kill} index={i} />
        ))}
      </div>
    </div>
  );
}
