import React, { useState } from 'react';
import MatchCard from './MatchCard';
import './Bracket.css';

// ФЕЙКОВЫЙ JSON С БЭКЕНДА
const MOCK_TOURNAMENT_DATA = {
  upper_bracket: [
    {
      round_name: "ROUND 1",
      matches: [
        { id: 1, team1: { name: 'PŨPȒƐMŜKƖYǁ2 team', score: 2, isWinner: true }, team2: { name: 'Ocelot team', score: 0, isWinner: false } },
        { id: 2, team1: { name: 'Alpha Squad', score: 1, isWinner: false }, team2: { name: 'Beta Force', score: 2, isWinner: true } },
        { id: 3, isEmpty: true },
        { id: 4, isEmpty: true }
      ]
    },
    {
      round_name: "SEMI-FINAL",
      matches: [
        { id: 5, team1: { name: 'PŨPȒƐMŜKƖYǁ2 team', score: 0, isWinner: false }, team2: { name: 'Beta Force', score: 0, isWinner: false } },
        { id: 6, isEmpty: true }
      ]
    },
    {
      round_name: "GRAND FINAL",
      matches: [
        { id: 7, isEmpty: true }
      ]
    }
  ]
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

const BracketStage = () => {
  const [activeTab, setActiveTab] = useState('playoff');

  const upperBracket = MOCK_TOURNAMENT_DATA.upper_bracket;

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
          <h2 style={{ color: '#13AD91', fontFamily: 'Ponter' }}>Группы в разработке...</h2>
        </div>
      )}

      {/* =========================================
          ПЛЕЙ-ОФФ (ДИНАМИЧЕСКИЙ РЕНДЕР ИЗ JSON)
          ========================================= */}
      {activeTab === 'playoff' && (
        <div className="playoff-container">
          
          <div className="playoff-bracket">
            <div className="group-header" style={{ color: '#13AD91' }}>
              <div className="group-marker" style={{ backgroundColor: '#13AD91' }}></div>
              ВЕРХНЯЯ СЕТКА
            </div>
            
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
                        // Определяем роли карточки для рисования коннекторов
                        const isTopPair = matchIndex % 2 === 0;
                        const isBottomPair = matchIndex % 2 !== 0;
                        const isChild = roundIndex > 0;
                        
                        // 1. Вычисляем Y-координату: Стартовый отступ раунда + (Индекс * Шаг раунда)
                        const topPosition = metrics.startOffset + (matchIndex * metrics.step);
                        
                        // 2. Вычисляем высоту скобки ┐ и ┘: Половина шага ТЕКУЩЕГО раунда + 2px на border
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
                              '--connector-height': `${connectorHeight}px` // Передаем высоту в CSS
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

export default BracketStage;