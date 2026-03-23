export default function Footer() {
  return (
    <footer className="bg-[#0D1117] border-t border-[#2EECC0]/10 h-[80px] flex items-center mt-auto relative z-10">
      <div className="w-full max-w-[1920px] mx-auto px-6 lg:px-[60px] flex items-center justify-between">
        
        {/* Left — social icons */}
        <div className="flex items-center gap-2">
          {[
            { href: 'https://discord.gg/moonrise', icon: 'discord.svg', alt: 'Discord' },
            { href: 'https://twitch.tv', icon: 'twitch.svg', alt: 'Twitch' },
            { href: 'https://youtube.com', icon: 'youtube.svg', alt: 'YouTube' },
            { href: 'https://t.me', icon: 'telegram.svg', alt: 'Telegram' },
            { href: 'https://tiktok.com', icon: 'tiktok.svg', alt: 'TikTok' },
          ].map(({ href, icon, alt }) => (
            <a key={alt} href={href} target="_blank" rel="noopener noreferrer" className="bracket-icon">
              <img src={`/assets/icons/${icon}`} alt={alt} className="w-[18px] h-[18px] opacity-80 hover:opacity-100" />
            </a>
          ))}
        </div>

        {/* Center — mini mascot */}
        <div className="absolute left-1/2 -translate-x-1/2">
          <img
            src="/assets/images/mascot.png"
            alt="MoonRise"
            className="h-[38px] opacity-70 grayscale"
          />
        </div>

        {/* Right — disclaimer */}
        <p className="font-heading text-[13px] tracking-[0.12em] uppercase text-[#2EECC0] mt-[2px]">
          MoonRise Project /// Not affiliated with Blizzard Entertainment.
        </p>
      </div>
    </footer>
  );
}