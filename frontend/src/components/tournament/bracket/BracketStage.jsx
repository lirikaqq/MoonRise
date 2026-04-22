import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import client from '../../../api/client';
import MatchCard from './MatchCard';
import './Bracket.css';

// Трансформация encounters → rounds формат для BracketStage
function transformEncountersToRounds(encounters, teams) {
  // Группируем по round_number
  const roundsMap = {};
  encounters.forEach(enc => {
    const rnd = enc.round_number || 1;
    if (!roundsMap[rnd]) roundsMap[rnd] = [];
    
    const t1 = teams.find(t => t.id === enc.team1_id);
    const t2 = teams.find(t => t.id === enc.team2_id);
    const isCompleted = !!enc.winner_team_id;
    
    roundsMap[rnd].push({
      id: enc.id,
      isEmpty: false,
      team1: {
        name: t1?.name || 'TBD',
        score: enc.team1_score ?? 0,
        isWinner: enc.winner_team_id === enc.team1_id,
      },
      team2: {
        name: t2?.name || 'TBD',
        score: enc.team2_score ?? 0,
        isWinner: enc.winner_team_id === enc.team2_id,
      },
      status: isCompleted ? 'completed' : 'pending',
    });
  });

  // Превращаем в массив раундов
  const roundNames = ['ROUND 1', 'ROUND 2', 'ROUND 3', 'SEMI-FINAL', 'QUARTER-FINAL', 'GRAND FINAL'];
  return Object.entries(roundsMap)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([roundNum, matches], idx) => ({
      round_name: roundNames[idx] || `ROUND ${roundNum}`,
      matches,
    }));
}

const BracketStage = () => {
  const { id: tournamentId } = useParams();
  const [activeTab, setActiveTab] = useState('playoff'); // 'playoff' | 'group'
  const [encounters, setEncounters] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadBracket = useCallback(async () => {
    if (!tournamentId) return;
    setLoading(true);
    try {
      const [encData, teamsData] = await Promise.all([
        client.get(`matches/encounters/tournament/${tournamentId}`).then(r => r.data),
        client.get(`matches/teams/tournament/${tournamentId}`).then(r => r.data),
      ]);
      setEncounters(Array.isArray(encData) ? encData : []);
      setTeams(Array.isArray(teamsData) ? teamsData : []);
      setError(null);
    } catch (e) {
      console.error('Failed to load bracket:', e);
      setError('Не удалось загрузить сетку');
    } finally {
      setLoading(false);
    }
  }, [tournamentId]);

  useEffect(() => { loadBracket(); }, [loadBracket]);

  // Авто-обновление каждые 30 секунд
  useEffect(() => {
    const interval = setInterval(loadBracket, 30000);
    return () => clearInterval(interval);
  }, [loadBracket]);

  // ==========================================
  // ФИЛЬТРАЦИЯ ПО СТАДИИ (Группа / Плей-офф)
  // ==========================================
  const filteredEncounters = encounters.filter(enc => {
    // Приводим к нижнему регистру один раз для всех проверок
    const stageName = (enc.stage || '').toLowerCase();

    if (activeTab === 'group') {
      // Всё, что связано с группами или round-robin — это групповой этап
      return stageName.includes('group') ||
             stageName.includes('групп') ||
             stageName.includes('round robin') ||
             stageName.includes('round-robin');
    }

    if (activeTab === 'playoff') {
      // Исключаем групповые стадии явно
      if (stageName.includes('group') ||
          stageName.includes('групп') ||
          stageName.includes('round robin') ||
          stageName.includes('round-robin')) {
        return false;
      }
      // Всё остальное (single elimination, double, round 1, final и т.д.) считаем плей-офф
      return true;
    }

    return false;
  });

  // Трансформируем отфильтрованные encounters в раунды
  const upperBracket = transformEncountersToRounds(filteredEncounters, teams);
  const hasData = filteredEncounters.length > 0;
  const hasAnyData = encounters.length > 0;

  return (
    <div className="bracket-section">

      {/* ПЕРЕКЛЮЧАТЕЛЬ */}
      <div className="bracket-tabs-container">
        <div
          className={`bracket-tab ${activeTab === 'group' ? 'active' : ''}`}
          onClick={() => setActiveTab('group')}
        >
          ГРУППОВОЙ ЭТАП
        </div>
        <div
          className={`bracket-tab ${activeTab === 'playoff' ? 'active' : ''}`}
          onClick={() => setActiveTab('playoff')}
        >
          ПЛЕЙ-ОФФ
        </div>
      </div>

      {activeTab === 'group' && (
        <div className="group-stage-content">
          {loading && !hasAnyData ? (
            <div className="bracket-loading" style={{ padding: '40px', textAlign: 'center', color: '#A7F2A2', fontFamily: 'Ponter' }}>
              Загрузка сетки...
            </div>
          ) : error && !hasAnyData ? (
            <div className="bracket-error" style={{ padding: '40px', textAlign: 'center', color: '#ff6b6b', fontFamily: 'Ponter' }}>
              {error}
            </div>
          ) : !hasData ? (
            <div className="bracket-empty" style={{ padding: '40px', textAlign: 'center', color: '#A7F2A2', fontFamily: 'Ponter' }}>
              Матчи для этого этапа еще не сгенерированы
            </div>
          ) : (
            <div className="group-grid">
              {/* Групповой этап рендерится так же, как плей-офф */}
              {upperBracket.map((round, roundIndex) => {
                const metrics = getRoundMetrics(roundIndex);
                const hasNextRound = roundIndex < upperBracket.length - 1;

                return (
                  <div key={`round-${roundIndex}`} className="group-col">
                    <div className="round-header">{round.round_name}</div>
                    <div className="group-col-cards">
                      {round.matches.map((match, matchIndex) => {
                        return (
                          <div key={match.id} className="group-match-wrapper">
                            <MatchCard match={match} />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =========================================
          ПЛЕЙ-ОФФ (ДИНАМИЧЕСКИЙ РЕНДЕР ИЗ API)
          ========================================= */}
      {activeTab === 'playoff' && (
        <div className="playoff-container">

          <div className="playoff-bracket">
            <div className="group-header" style={{ color: '#13AD91' }}>
              <div className="group-marker" style={{ backgroundColor: '#13AD91' }}></div>
              ВЕРХНЯЯ СЕТКА
            </div>

            {loading && !hasAnyData ? (
              <div className="bracket-loading" style={{ padding: '40px', textAlign: 'center', color: '#A7F2A2', fontFamily: 'Ponter' }}>
                Загрузка сетки...
              </div>
            ) : error && !hasAnyData ? (
              <div className="bracket-error" style={{ padding: '40px', textAlign: 'center', color: '#ff6b6b', fontFamily: 'Ponter' }}>
                {error}
              </div>
            ) : !hasData ? (
              <div className="bracket-empty" style={{ padding: '40px', textAlign: 'center', color: '#A7F2A2', fontFamily: 'Ponter' }}>
                Матчи для этого этапа еще не сгенерированы
              </div>
            ) : (
              <div className="playoff-grid">
                {/* ПРОХОДИМСЯ ПО МАССИВУ РАУНДОВ */}
                {upperBracket.map((round, roundIndex) => {
                  const metrics = getRoundMetrics(roundIndex);
                  const hasNextRound = roundIndex < upperBracket.length - 1;

                  return (
                    <div key={`round-${roundIndex}`} className="playoff-col">
                      <div className="round-header">{round.round_name}</div>
                      <div className="playoff-col-cards">

                        {/* ПРОХОДИМСЯ ПО МАТЧАМ В РАУНДЕ */}
                        {round.matches.map((match, matchIndex) => {
                          const isTopPair = matchIndex % 2 === 0;
                          const isBottomPair = matchIndex % 2 !== 0;
                          const isChild = roundIndex > 0;

                          const topPosition = metrics.startOffset + (matchIndex * metrics.step);
                          const connectorHeight = (metrics.step / 2) + 2;

                          return (
                            <div
                              key={match.id}
                              className={`playoff-match-wrapper
                                ${hasNextRound ? 'has-next' : ''}
                                ${isChild ? 'is-child' : ''}
                                ${hasNextRound && isTopPair ? 'is-top-pair' : ''}
                                ${hasNextRound && isBottomPair ? 'is-bottom-pair' : ''}
                              `}
                              style={{
                                top: `${topPosition}px`,
                                '--connector-height': `${connectorHeight}px`,
                              }}
                            >
                              <MatchCard match={match} />
                            </div>
                          );
                        })}

                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="playoff-bracket" style={{ marginTop: '40px' }}>
            <div className="group-header" style={{ color: '#13AD91' }}>
              <div className="group-marker" style={{ backgroundColor: '#13AD91' }}></div>
              НИЖНЯЯ СЕТКА
            </div>
            <div className="bracket-grid">
               <h3 style={{ color: 'rgba(19, 173, 145, 0.5)', fontFamily: 'Ponter', padding: '20px', letterSpacing: '0.05em' }}>
                 МАТЧИ НИЖНЕЙ СЕТКИ...
               </h3>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

// МАТЕМАТИЧЕСКОЕ ЯДРО СЕТКИ
// Высчитывает координаты карточек и высоту линий для каждого раунда
const BASE_STEP = 80; // Расстояние между карточками в 1 раунде (50px карточка + 30px gap)

const getRoundMetrics = (roundIndex) => {
  if (roundIndex === 0) return { startOffset: 0, step: BASE_STEP };

  let offset = 0;
  let currentStep = BASE_STEP;

  // Каждый следующий раунд начинается со смещением на половину предыдущего шага,
  // а шаг увеличивается в 2 раза
  for (let i = 1; i <= roundIndex; i++) {
    offset = offset + (currentStep / 2);
    currentStep = currentStep * 2;
  }

  return { startOffset: offset, step: currentStep };
};

export default BracketStage;