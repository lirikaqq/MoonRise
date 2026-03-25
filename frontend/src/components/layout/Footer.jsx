export default function Footer() {
  return (
    <footer className="home-footer">
      <div className="home-footer-inner">

        <div className="home-footer-socials">
          <a href="#" className="home-footer-social">
            <img src="/assets/icons/discord.svg" alt="Discord" />
          </a>
          <a href="#" className="home-footer-social">
            <img src="/assets/icons/twitch.svg" alt="Twitch" />
          </a>
          <a href="#" className="home-footer-social">
            <img src="/assets/icons/youtube.svg" alt="YouTube" />
          </a>
          <a href="#" className="home-footer-social">
            <img src="/assets/icons/telegram.svg" alt="Telegram" />
          </a>
          <a href="#" className="home-footer-social">
            <img src="/assets/icons/tiktok.svg" alt="TikTok" />
          </a>
        </div>

        <div className="home-footer-logo">
          <img src="/assets/images/mascot.png" alt="MoonRise" />
        </div>

        <div className="home-footer-copy">
          <p>MOONRISE PROJECT&nbsp;///&nbsp;NOT AFFILIATED WITH BLIZZARD ENTERTAINMENT.</p>
        </div>

      </div>
    </footer>
  );
}