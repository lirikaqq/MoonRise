// frontend/src/hooks/usePlayerProfileData.js
import { useState, useEffect } from 'react';
import { playersApi } from '../api/players';

const usePlayerProfileData = (playerId) => {
  const [player, setPlayer] = useState(null);
  const [stats, setStats] = useState(null);
  const [topHeroes, setTopHeroes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        if (!playerId) return;
        console.log("=== PLAYER ID ===", playerId);

        // Добавили .catch(), чтобы приложение не падало, если у игрока еще нет статистики
        const [data, statsRes, heroesRes] = await Promise.all([
          playersApi.getById(playerId).catch(() => null),
          playersApi.getProfileStats(playerId).catch(() => null),
          playersApi.getTopHeroes(playerId).catch(() => ({ heroes: [] })),
        ]);

        // Исправили имя переменной на data
        console.log("=== RAW API RESPONSE ===", { data, statsRes, heroesRes });

        setPlayer(data);

        // Проверяем, есть ли ошибка внутри statsRes (как было в твоем curl: {"detail": "No match data..."})
        if (!statsRes || statsRes.detail) {
          setStats(null);
          setError('no_data');
        } else {
          setStats(transformStatsForUI(statsRes));
        }

        const heroesList = heroesRes?.heroes || [];
        setTopHeroes(heroesList.map(transformHeroFromAPI));

      } catch (err) {
        console.error('Failed to load player data:', err);
        setError('load_error');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [playerId]);

  return { player, stats, topHeroes, loading, error };
};

// Функция для трансформации статистики в формат для UI (добавлена защита от undefined)
const transformStatsForUI = (stats) => {
  return {
    total_matches: stats?.total_matches ?? 0,
    wins: stats?.wins ?? 0,            // ← правильно
    losses: stats?.losses ?? 0,        // ← правильно
    winrate: stats?.winrate ?? 0,
    kda_ratio: stats?.kda_ratio ?? 0,
    elims_avg: stats?.elims_avg ?? 0,
    deaths_avg: stats?.deaths_avg ?? 0,
    playtime_hours: stats?.playtime_hours ?? 0,
    maps_count: stats?.maps_count ?? 0,
    mvp_count: stats?.mvp_count ?? 0,
    svp_count: stats?.svp_count ?? 0,
  };
};

// Функция для трансформации данных героев из API (добавлена защита от undefined)
const transformHeroFromAPI = (hero) => {
  // Нормализуем имя героя (убираем акценты для поиска иконки)
  const heroName = hero?.hero_name ?? 'Unknown';
  const iconKey = heroName
    .replace('Lúcio', 'Lucio')
    .replace('Torbjörn', 'Torbjorn')
    .replace('D.Va', 'DVa')
    .replace('Junker Queen', 'JunkerQueen')
    .replace('Wrecking Ball', 'WreckingBall')
    .replace('Soldier: 76', 'Soldier-76');

  return {
    name: heroName.toUpperCase(),
    avatar: HERO_ICONS[iconKey] || HERO_ICONS[heroName] || '/assets/icons_hero/Icon-Mercy.png',
    playtime: formatTime(hero?.time_played ?? 0),
    stats: [
      { label: 'ELIMS', value: hero?.eliminations?.toString() ?? '0', global: '—' },
      { label: 'DAMAGE', value: hero?.hero_damage_dealt?.toLocaleString('en', { maximumFractionDigits: 0 }) ?? '0', global: '—' },
      { label: 'DEATHS', value: hero?.deaths?.toString() ?? '0', global: '—' },
      { label: 'HEALING', value: hero?.healing_dealt?.toLocaleString('en', { maximumFractionDigits: 0 }) ?? '0', global: '—' },
    ],
  };
};

const HERO_ICONS = {
  'Ana': '/assets/icons_hero/Icon-Ana.png',
  'Anran': '/assets/icons_hero/Icon-Anran.png',
  'Ashe': '/assets/icons_hero/Icon-Ashe.png',
  'Baptiste': '/assets/icons_hero/Icon-Baptiste.png',
  'Bastion': '/assets/icons_hero/Icon-Bastion.png',
  'Brigitte': '/assets/icons_hero/Icon-Brigitte.png',
  'Cassidy': '/assets/icons_hero/Icon-Cassidy.png',
  'DVa': '/assets/icons_hero/Icon-DVa.png',
  'Domina': '/assets/icons_hero/Icon-Domina.png',
  'Doomfist': '/assets/icons_hero/Icon-Doomfist.png',
  'Echo': '/assets/icons_hero/Icon-Echo.png',
  'Emre': '/assets/icons_hero/Icon-Emre.png',
  'Freja': '/assets/icons_hero/Icon-Freja.png',
  'Genji': '/assets/icons_hero/Icon-Genji.png',
  'Hanzo': '/assets/icons_hero/Icon-Hanzo.png',
  'Hazard': '/assets/icons_hero/Icon-Hazard.png',
  'Illari': '/assets/icons_hero/Icon-Illari.png',
  'Jetpack_Cat': '/assets/icons_hero/Icon-Jetpack_Cat.png',
  'JunkerQueen': '/assets/icons_hero/Icon-Junker_Queen.png',
  'Junkrat': '/assets/icons_hero/Icon-Junkrat.png',
  'Juno': '/assets/icons_hero/Icon-Juno.png',
  'Kiriko': '/assets/icons_hero/Icon-kiriko.png',
  'Lifeweaver': '/assets/icons_hero/Icon-Lifeweaver.png',
  'Lucio': '/assets/icons_hero/Icon-Lucio.png',
  'Mauga': '/assets/icons_hero/Icon-Mauga.png',
  'Mei': '/assets/icons_hero/Icon-Mei.png',
  'Mercy': '/assets/icons_hero/Icon-Mercy.png',
  'Mizuki': '/assets/icons_hero/Icon-Mizuki.png',
  'Moira': '/assets/icons_hero/Icon-Moira.png',
  'Orisa': '/assets/icons_hero/Icon-Orisa.png',
  'Pharah': '/assets/icons_hero/Icon-Pharah.png',
  'Ramattra': '/assets/icons_hero/Icon-Ramattra.png',
  'Reaper': '/assets/icons_hero/Icon-Reaper.png',
  'Reinhardt': '/assets/icons_hero/Icon-Reinhardt.png',
  'Roadhog': '/assets/icons_hero/Icon-Roadhog.png',
  'Sigma': '/assets/icons_hero/Icon-Sigma.png',
  'Sojourn': '/assets/icons_hero/Icon-Sojourn.png',
  'Soldier-76': '/assets/icons_hero/Icon-Soldier-76.png',
  'Sombra': '/assets/icons_hero/Icon-Sombra.png',
  'Symmetra': '/assets/icons_hero/Icon-Symmetra.png',
  'Torbjorn': '/assets/icons_hero/Icon-Torbjorn.png',
  'Tracer': '/assets/icons_hero/Icon-Tracer.png',
  'Vendetta': '/assets/icons_hero/Icon-Vendetta.png',
  'Venture': '/assets/icons_hero/Icon-Venture.png',
  'Widowmaker': '/assets/icons_hero/Icon-Widowmaker.png',
  'Winston': '/assets/icons_hero/Icon-Winston.png',
  'WreckingBall': '/assets/icons_hero/Icon-WreckingBall.png',
  'Wuyang': '/assets/icons_hero/Icon-Wuyang.png',
  'Zarya': '/assets/icons_hero/Icon-Zarya.png',
  'Zenyatta': '/assets/icons_hero/Icon-Zenyatta.png',
};

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}H ${m}M`;
  return `${m}M`;
};

export default usePlayerProfileData;