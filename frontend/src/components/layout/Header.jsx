import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authApi } from '../../api/auth'

export default function Header() {
  const { user, logout, loading } = useAuth()

  const handleLogin = () => {
    window.location.href = authApi.getDiscordLoginUrl()
  }

  return (
    <header className="home-header">
      <div className="home-header-inner">

        <nav className="home-nav">
          <Link to="/tournaments">TOURNAMENTS</Link>
          <Link to="/players">USERS</Link>
          <Link to="/faq">FAQ</Link>
        </nav>

        <Link to="/" className="home-logo">
          <img src="/assets/images/logo.svg" alt="MoonRise" />
        </Link>

        <div className="home-header-right">
          <a href="#" className="home-social">
            <img src="/assets/icons/twitch.svg" alt="Twitch" />
          </a>
          <a href="#" className="home-social">
            <img src="/assets/icons/youtube.svg" alt="YouTube" />
          </a>
          <a href="#" className="home-social">
            <img src="/assets/icons/telegram.svg" alt="Telegram" />
          </a>
          <a href="#" className="home-social">
            <img src="/assets/icons/tiktok.svg" alt="TikTok" />
          </a>

          {loading ? (
            <div className="home-login">
              <span className="home-login-text">...</span>
            </div>
            ) : user ? (
  // Авторизован — только MY PROFILE + выход
  <div className="home-user">
    <Link
      to={`/players/${user.id}`}
      className="home-profile-btn"
    >
      MY PROFILE
    </Link>
    <button className="home-logout-btn" onClick={logout}>
      ✕
    </button>
  </div>
) : (
        
            // Не авторизован
            <button className="home-login" onClick={handleLogin}>
              <img src="/assets/icons/discord.svg" alt="" />
              <span className="home-login-text">LOG IN</span>
            </button>
          )}

        </div>
      </div>
    </header>
  )
}