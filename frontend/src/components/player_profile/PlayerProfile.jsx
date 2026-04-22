// frontend/src/components/player_profile/PlayerProfile.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import './PlayerProfile.css';

import PlayerCard from './PlayerCard';
import AchievementsCard from './AchievementsCard';
import DivisionsCard from './DivisionsCard';
import ProfileTabs from './ProfileTabs';
import FilterRow from './FilterRow';
import StatsTopRow from './StatsTopRow';
import StatsBottomRow from './StatsBottomRow';
import TopHeroesCard from './TopHeroesCard';

import usePlayerProfileData from '../../hooks/usePlayerProfileData';

// Маппинг имён героев на иконки
const HERO_ICONS = {
  'Ana': '/assets/icons_hero/Icon-Ana.png',
  'Ashe': '/assets/icons_hero/Icon-Ashe.png',
  'Baptiste': '/assets/icons_hero/Icon-Baptiste.png',
  'Bastion': '/assets/icons_hero/Icon-Bastion.png',
  'Brigitte': '/assets/icons_hero/Icon-Brigitte.png',
  'Cassidy': '/assets/icons_hero/Icon-Cassidy.png',
  'D.Va': '/assets/icons_hero/Icon-D.Va.png',
  'Doomfist': '/assets/icons_hero/Icon-Doomfist.png',
  'Echo': '/assets/icons_hero/Icon-Echo.png',
  'Genji': '/assets/icons_hero/Icon-Genji.png',
  'Hanzo': '/assets/icons_hero/Icon-Hanzo.png',
  'Illari': '/assets/icons_hero/Icon-Illari.png',
  'Junker Queen': '/assets/icons_hero/Icon-JunkerQueen.png',
  'Junkrat': '/assets/icons_hero/Icon-Junkrat.png',
  'Kiriko': '/assets/icons_hero/Icon-Kiriko.png',
  'Lifeweaver': '/assets/icons_hero/Icon-Lifeweaver.png',
  'Lúcio': '/assets/icons_hero/Icon-Lucio.png',
  'Mauga': '/assets/icons_hero/Icon-Mauga.png',
  'Mei': '/assets/icons_hero/Icon-Mei.png',
  'Mercy': '/assets/icons_hero/Icon-Mercy.png',
  'Moira': '/assets/icons_hero/Icon-Moira.png',
  'Orisa': '/assets/icons_hero/Icon-Orisa.png',
  'Pharah': '/assets/icons_hero/Icon-Pharah.png',
  'Ramattra': '/assets/icons_hero/Icon-Ramattra.png',
  'Reaper': '/assets/icons_hero/Icon-Reaper.png',
  'Reinhardt': '/assets/icons_hero/Icon-Reinhardt.png',
  'Roadhog': '/assets/icons_hero/Icon-Roadhog.png',
  'Sigma': '/assets/icons_hero/Icon-Sigma.png',
  'Sojourn': '/assets/icons_hero/Icon-Sojourn.png',
  'Soldier: 76': '/assets/icons_hero/Icon-Soldier76.png',
  'Sombra': '/assets/icons_hero/Icon-Sombra.png',
  'Symmetra': '/assets/icons_hero/Icon-Symmetra.png',
  'Torbjörn': '/assets/icons_hero/Icon-Torbjorn.png',
  'Tracer': '/assets/icons_hero/Icon-Tracer.png',
  'Venture': '/assets/icons_hero/Icon-Venture.png',
  'Widowmaker': '/assets/icons_hero/Icon-Widowmaker.png',
  'Winston': '/assets/icons_hero/Icon-Winston.png',
  'Wrecking Ball': '/assets/icons_hero/Icon-WreckingBall.png',
  'Zarya': '/assets/icons_hero/Icon-Zarya.png',
  'Zenyatta': '/assets/icons_hero/Icon-Zenyatta.png',
};

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}H ${m}M`;
  return `${m}M`;
}

function transformHeroFromAPI(hero) {
  return {
    name: hero.hero_name?.toUpperCase() ?? 'UNKNOWN',
    avatar: HERO_ICONS[hero.hero_name] || '/assets/icons_hero/Icon-Mercy.png',
    playtime: formatTime(hero.time_played ?? 0),
    stats: [
      { label: 'ELIMS', value: hero.eliminations?.toString() ?? '0', global: '—' },
      { label: 'DAMAGE', value: hero.hero_damage_dealt?.toLocaleString('en', {maximumFractionDigits: 0}) ?? '0', global: '—' },
      { label: 'DEATHS', value: hero.deaths?.toString() ?? '0', global: '—' },
      { label: 'HEALING', value: hero.healing_dealt?.toLocaleString('en', {maximumFractionDigits: 0}) ?? '0', global: '—' },
    ],
  };
}

export default function PlayerProfile({ playerId, activeTab, onTabChange }) {
  const { player, stats, topHeroes, loading, error } = usePlayerProfileData(playerId);

  if (loading) {
    return <div style={{ color: 'white', textAlign: 'center', padding: 100 }}>Loading...</div>;
  }

  if (error === 'no_data' || (stats && stats.total_matches === 0)) {
    return (
      <div className="profile-page">
        <nav className="breadcrumbs">
          <Link to="/players">USERS</Link>
          <span className="separator">›</span>
          <span className="current">
            {player ? player.username || player.nickname : 'PLAYER'}
          </span>
        </nav>
        <div style={{
          textAlign: 'center',
          padding: '80px 40px',
          color: '#A7F2A2',
          fontFamily: 'Ponter',
        }}>
          <div style={{ fontSize: 48, marginBottom: 20 }}>📊</div>
          <h2 style={{ color: '#13AD91', fontSize: 28, marginBottom: 12 }}>
            Нет данных о матчах
          </h2>
          <p style={{ fontSize: 16, maxWidth: 500, margin: '0 auto' }}>
            Игрок ещё не участвовал в матчах или логи не были загружены.
            Статистика появится после первого распарсенного матча.
          </p>
        </div>
      </div>
    );
  }

  if (error === 'load_error') {
    return (
      <div className="profile-page">
        <div style={{ textAlign: 'center', padding: '80px 40px', color: '#ff6b6b', fontFamily: 'Ponter' }}>
          <h2>Ошибка загрузки данных</h2>
          <p style={{ marginTop: 12 }}>Попробуйте обновить страницу</p>
        </div>
      </div>
    );
  }

  const filterRowStats = stats ? {
    playtime: `${stats.playtime_hours}H PLAYTIME`,
    maps: `${stats.maps_count} MAPS`,
    wins: stats.wins,
    losses: stats.losses,
    winrate: `${stats.winrate}%`,
  } : {};

  const statsTopRowStats = stats ? {
    place: null,
    role: player?.division || null,
    mvpScore: stats.mvp_count > 0 ? stats.mvp_count.toString() : '0',
    mvpFrom: `FROM ${stats.total_matches} MATCHES`,
    svpScore: stats.svp_count > 0 ? stats.svp_count.toString() : '0',
    svpFrom: `FROM ${stats.total_matches} MATCHES`,
  } : {};

  const statsBottomRowStats = stats ? {
    winrate: `${stats.winrate}%`,
    winrateSub: `${stats.wins} FROM ${stats.total_matches}`,
    kdaRatio: stats.kda_ratio?.toString() || '0',
    kdaSub: `KDA RATIO`,
    elims: stats.elims_avg?.toString() || '0',
    elimsSub: `AVG FROM ${stats.total_matches}`,
    deaths: stats.deaths_avg?.toString() || '0',
    deathsSub: `AVG FROM ${stats.total_matches}`,
  } : {};

  return (
    <div className="profile-page">
      <nav className="breadcrumbs">
        <Link to="/players">USERS</Link>
        <span className="separator">›</span>
        <span className="current">{player ? player.username || player.nickname : 'PLAYER'}</span>
      </nav>

      <div className="profile-bands">
        <div className="profile-band-1">
          <div className="profile-left">
            <PlayerCard player={player} stats={stats} />
          </div>
          <div className="profile-right-content">
            <ProfileTabs activeTab={activeTab} onTabChange={onTabChange} />
            <FilterRow stats={filterRowStats} />
            <StatsTopRow stats={statsTopRowStats} />
          </div>
        </div>

        <div className="profile-band-2">
          <div className="profile-left">
            <AchievementsCard />
          </div>
          <div className="profile-right-content">
            <StatsBottomRow stats={statsBottomRowStats} />
          </div>
        </div>

        <div className="profile-band-3">
          <div className="profile-left">
            <DivisionsCard />
          </div>
          <div className="profile-right-content">
            <TopHeroesCard heroes={topHeroes} />
          </div>
        </div>
      </div>

      <div style={{ marginTop: 30, paddingTop: 20, borderTop: '1px solid var(--accent)', paddingBottom: 30 }}>
        <Link to="/tournaments" style={{
          fontFamily: '"Digits"',
          fontSize: 14,
          color: 'var(--accent)',
          textDecoration: 'none',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
            <path d="M8 1L3 6L8 11" stroke="currentColor" strokeWidth="2" fill="none" />
          </svg>
          BACK TO TOURNAMENTS
        </Link>
      </div>
    </div>
  );
}