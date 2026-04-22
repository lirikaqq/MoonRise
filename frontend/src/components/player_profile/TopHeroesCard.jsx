import React from 'react';
import './TopHeroesCard.css';

const DEFAULT_HEROES = [
  {
    name: 'MERCY',
    avatar: '/assets/icons_hero/Icon-Mercy.png',
    playtime: '10H 9M',
    stats: [
      { label: 'ELIMS', value: '0.19', global: '0.65' },
      { label: 'DAMAGE', value: '37.51', global: '119.9' },
      { label: 'DEATHS', value: '5.15', global: '4.26' },
      { label: 'HEALING', value: '7,191', global: '6,345' },
    ],
  },
  {
    name: 'GENJI',
    avatar: '/assets/icons_hero/Icon-Genji.png',
    playtime: '5H 58M',
    stats: [
      { label: 'ELIMS', value: '11.7', global: '10.93' },
      { label: 'DAMAGE', value: '5,215', global: '119.9' },
      { label: 'DEATHS', value: '3.85', global: '4.26' },
      { label: 'HEALING', value: '—', global: '—' },
    ],
  },
  {
    name: 'D.VA',
    avatar: '/assets/icons_hero/Icon-D.Va.png',
    playtime: '48M',
    stats: [
      { label: 'ELIMS', value: '10.87', global: '11.68' },
      { label: 'DAMAGE', value: '6,247', global: '5,125' },
      { label: 'DEATHS', value: '5.15', global: '4.26' },
      { label: 'HEALING', value: '—', global: '—' },
    ],
  },
];

function HeroStatBlock({ label, value, global }) {
  const parseNum = (s) => {
    const clean = s.replace(/,/g, '');
    const n = parseFloat(clean);
    return isNaN(n) ? null : n;
  };
  const valNum = parseNum(value);
  const globNum = parseNum(global);
  let diff = null;
  if (valNum !== null && globNum !== null) {
    diff = (valNum - globNum).toFixed(valNum % 1 === 0 ? 0 : 2);
    diff = diff > 0 ? `+${diff}` : diff;
  }

  return (
    <div className="hero-stat-block">
      <div className="hero-stat-front">
        <div className="hero-stat-front__content">
          <div className="hero-stat__label">{label}</div>
          <div className="hero-stat__value">{value}</div>
        </div>
      </div>
      <div className="hero-stat-back">
        <div className="hero-stat-back__content">
          <div className="hero-stat__label">GLOBAL AVG</div>
          <div className="hero-stat__value">{global}</div>
          {diff !== null && (
            <div className={`hero-stat__diff ${diff.startsWith('-') ? 'negative' : 'positive'}`}>
              {diff}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function HeroBlock({ hero }) {
  return (
    <div className="hero-block">
      {/* Вертикальная акцентная полоска слева */}
      <div className="hero-block__accent-line" />

      {/* Левая часть: имя + playtime + рамка аватара */}
      <div className="hero-block__left">
        <div className="hero-block__name">{hero.name}</div>
        <div className="hero-block__playtime">PLAYTIME {hero.playtime}</div>
        <div className="hero-block__avatar-frame">
          <img src={hero.avatar} alt={hero.name} />
        </div>
      </div>

      {/* Правая часть: стат-карточки 2x2 */}
      <div className="hero-block__stats">
        {hero.stats.slice(0, 4).map((stat) => (
          <HeroStatBlock key={stat.label} {...stat} />
        ))}
      </div>
    </div>
  );
}

export default function TopHeroesCard({ heroes }) {
  const heroList = heroes || DEFAULT_HEROES;

  return (
    <div className="top-heroes-card">
      <div className="top-heroes-card__content">
        {/* Header */}
        <div className="top-heroes-card__header">
          <h3 className="top-heroes-card__title">TOP HEROES</h3>
          <span className="top-heroes-card__subtitle">
            DELTAS ARE COMPUTED VS GLOBAL AVERAGES. FOR SOME STATS (DEATHS, DAMAGE TAKEN), LOWER IS BETTER.
          </span>
        </div>

        {/* Divider */}
        <div className="top-heroes-card__line" />

        {/* Герои */}
        <div className="top-heroes-card__heroes">
          {heroList.map((hero) => (
            <HeroBlock key={hero.name} hero={hero} />
          ))}
        </div>
      </div>
    </div>
  );
}
