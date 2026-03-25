import "./home.css";
import Header from "../components/layout/Header";
import Footer from "../components/layout/Footer";
import HeroSection from "../components/hero/HeroSection";
import UpcomingTournamentSection from "../components/tournament/UpcomingTournamentSection";
import StatsSection from "../components/stats/StatsSection";
import useReveal from "../hooks/useReveal.jsx";

export default function Home() {
  useReveal();

  return (
    <div className="home-page">
      <Header />
      <HeroSection />
      <div className="second-screen">
        <UpcomingTournamentSection />
        <StatsSection />
        <Footer />
      </div>
    </div>
  );
}