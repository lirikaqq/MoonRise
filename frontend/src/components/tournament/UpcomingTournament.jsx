export default function UpcomingTournament() {
  return (
    <section className="py-20 flex flex-col justify-center min-h-screen">
      <div className="w-full max-w-[1920px] mx-auto px-6 lg:px-[120px]">
        
        {/* === БЛОК ТУРНИРА === */}
        <div className="cyber-panel px-16 py-12 mb-20 mt-10">
          
          {/* Левый заголовок перекрывающий рамку */}
          <div className="absolute -top-[10px] left-12 bg-[#0D1117] px-4 flex items-center gap-3 z-10">
            <div className="w-2 h-2 bg-[#2EECC0] rounded-full shadow-[0_0_8px_#2EECC0]"></div>
            <span className="font-heading text-[15px] tracking-[0.15em] text-[#2EECC0] uppercase mt-[2px]">
              Upcoming Tournament
            </span>
          </div>

          {/* Дата перекрывающая рамку */}
          <div className="absolute -top-[10px] right-12 bg-[#0D1117] px-4 z-10">
            <span className="font-heading text-[15px] tracking-[0.15em] text-[#2EECC0] uppercase mt-[2px]">
              08 - 09 MARCH
            </span>
          </div>

          <div className="relative z-20 flex justify-between items-center w-full">
            <div className="max-w-[650px]">
              <img
                src="/assets/images/tournament-mix-logo.png"
                alt="MoonRise MIX"
                className="h-[100px] mb-8"
              />
              <p className="font-body text-[14px] leading-[1.8] uppercase tracking-[0.04em] text-white mb-10 w-[85%]">
                Турнир, в котором команды формируются с помощью инструментов
                для баланса команд. Основной принцип формирования команд —
                баланс среднего рейтинга между всеми командами.
              </p>
              
              {/* Кнопки как в PDF */}
              <div className="flex gap-6">
                <a href="#" className="btn-solid cyber-cut">
                  <span className="mt-[2px]">Registration</span>
                </a>
                <a href="#" className="btn-outline-wrap cyber-cut">
                  <span className="btn-outline-inner cyber-cut mt-[2px]">Info</span>
                </a>
              </div>
            </div>
          </div>

          {/* Сомбра приклеена к низу */}
          <img
            src="/assets/images/tournament-hero.png"
            alt="Tournament Hero"
            className="absolute bottom-[-2px] right-[5%] h-[115%] object-contain pointer-events-none z-30" 
          />
        </div>

        {/* === БЛОК СТАТИСТИКИ === */}
        <div className="cyber-panel py-14">
          
          {/* Заголовок Stats */}
          <div className="absolute -top-[10px] left-12 bg-[#0D1117] px-4 flex items-center gap-3 z-10">
            <svg width="18" height="16" viewBox="0 0 16 14" fill="none">
              <rect x="0" y="8" width="3" height="6" fill="#2EECC0"/>
              <rect x="5" y="4" width="3" height="10" fill="#2EECC0"/>
              <rect x="10" y="0" width="3" height="14" fill="#2EECC0"/>
            </svg>
            <span className="font-heading text-[15px] tracking-[0.15em] text-[#2EECC0] uppercase mt-[2px]">
              Stats
            </span>
          </div>

          <div className="grid grid-cols-4 relative z-20">
            {[
              { value: '6', label: 'Турниров проведено' },
              { value: '100+', label: 'Участников' },
              { value: '100+', label: 'Команд' },
              { value: '18', label: 'Победителей' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="font-stats text-[75px] text-[#2EECC0] leading-none mb-3">
                  {stat.value}
                </div>
                <div className="font-body text-[13px] tracking-[0.1em] text-gray-400 uppercase font-bold">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}