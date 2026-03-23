import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Header() {
  const { user, login } = useAuth();

  return (
    <header className="fixed top-0 left-0 w-full z-50 bg-[#0D1117]/95 border-b border-[#2EECC0]/10 h-[72px] flex items-center">
      <div className="w-full max-w-[1920px] mx-auto px-6 lg:px-[60px] flex items-center justify-between relative">
        
        {/* Left nav */}
        <nav className="flex items-center gap-10">
          {['Tournaments', 'Users', 'FAQ'].map(item => (
            <Link
              key={item}
              to={`/${item.toLowerCase()}`}
              className="font-heading text-[#2EECC0] text-[15px] tracking-[0.15em] uppercase hover:text-white transition-colors"
            >
              {item}
            </Link>
          ))}
        </nav>

        {/* Center logo */}
        <Link to="/" className="absolute left-1/2 -translate-x-1/2">
          <img src="/assets/images/logo.svg" alt="MoonRise" className="h-[40px]" />
        </Link>

        {/* Right - Socials & Auth */}
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            <SocialIcon href="https://twitch.tv" icon="twitch.svg" alt="Twitch" />
            <SocialIcon href="https://youtube.com" icon="youtube.svg" alt="YouTube" />
            <SocialIcon href="https://t.me" icon="telegram.svg" alt="Telegram" />
            <SocialIcon href="https://tiktok.com" icon="tiktok.svg" alt="TikTok" />
          </div>

          {user ? (
            <Link to={`/players/${user.id}`} className="bracket-btn ml-4">
              <div className="flex items-center gap-3">
                <img src="/assets/icons/discord.svg" alt="Discord" className="w-[18px] h-[18px]" />
                <span className="font-heading text-[#2EECC0] text-[15px] tracking-[0.15em] uppercase mt-[2px]">Profile</span>
              </div>
            </Link>
          ) : (
            <button onClick={login} className="bracket-btn ml-4">
              <div className="flex items-center gap-3 group">
                <img src="/assets/icons/discord.svg" alt="Discord" className="w-[18px] h-[18px]" />
                <span className="font-heading text-[#2EECC0] text-[15px] tracking-[0.15em] uppercase mt-[2px]">Log In</span>
              </div>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

function SocialIcon({ href, icon, alt }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="bracket-icon">
      <img src={`/assets/icons/${icon}`} alt={alt} className="w-[18px] h-[18px] opacity-80 hover:opacity-100 transition-opacity" />
    </a>
  );
}