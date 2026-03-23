export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col justify-center overflow-hidden pt-[72px]">
      <div className="w-full max-w-[1920px] mx-auto px-6 lg:px-[120px] flex items-center justify-between relative z-10">
        
        {/* ЛЕВАЯ ЧАСТЬ */}
        <div className="max-w-[700px]">
          <h1 className="font-heading text-[120px] lg:text-[140px] leading-[0.85] text-[#C8FFB0] uppercase tracking-[-2px] mb-12">
            Rise to<br />the<br />Moon
          </h1>

          <div className="flex gap-5 mb-14">
            {/* Толстый прямоугольник слева */}
            <div className="w-[8px] bg-[#2EECC0]"></div>
            <p className="font-body text-[15px] leading-[2.1] text-white uppercase tracking-[0.06em] pt-1">
              MoonRise объединяет тех, кто готов <span className="text-[#2EECC0] font-bold">сиять ярче</span>.
              <br />
              Мы проводим турниры всех форматов — от мини-ивентов
              <br />
              до масштабных турниров.
              <br />
              Стань частью проекта, побеждай и <span className="text-[#2EECC0] font-bold">занимай своё место среди звёзд</span>.
            </p>
          </div>

          {/* Кнопка с декоративной рамкой позади */}
          <div className="relative inline-block">
            {/* Тонкая рамка позади (смещение вниз-влево) */}
            <div className="absolute top-1 right-2 bottom-[-4px] left-[-4px] border border-[#2EECC0] cyber-cut pointer-events-none"></div>
            {/* Сама залитая зеленая кнопка */}
            <a href="https://discord.gg/moonrise" target="_blank" rel="noopener noreferrer" className="relative z-10 btn-solid cyber-cut">
              <span className="mt-[2px]">Join Discord</span>
            </a>
          </div>
        </div>

        {/* ПРАВАЯ ЧАСТЬ (Радар и Маскот) */}
        <div className="relative flex items-center justify-center w-[650px] h-[650px] pointer-events-none mr-10">
          
          {/* Свечение */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] bg-[#2EECC0]/20 rounded-full blur-[90px]"></div>

          {/* Радар - Тонкий Круг */}
          <div className="absolute w-[580px] h-[580px] border border-[#2EECC0]/20 rounded-full"></div>
          
          {/* Радар - Линии */}
          <div className="absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-[1px] bg-[#2EECC0]/20"></div>
          <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[1px] bg-[#2EECC0]/20"></div>

          {/* Радар - Светящаяся точка */}
          <div className="absolute top-[14.6%] right-[14.6%] w-1.5 h-1.5 bg-[#2EECC0] rounded-full shadow-[0_0_8px_2px_#2EECC0]"></div>

          {/* Маскот */}
          <img 
            src="/assets/images/mascot.png" 
            alt="MoonRise Mascot" 
            className="w-[480px] h-auto relative z-10"
          />
        </div>
      </div>

      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 z-20">
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-1.5 bg-[#2EECC0] rounded-full"></div>
          <span className="font-heading text-[12px] tracking-[0.2em] text-gray-400 uppercase">
            Upcoming Tournament
          </span>
        </div>
        <span className="text-gray-400 text-[10px] mt-1">▼</span>
      </div>
    </section>
  );
}