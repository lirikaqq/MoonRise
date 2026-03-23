import Header from '../components/layout/Header';
import HeroSection from '../components/hero/HeroSection';
import UpcomingTournament from '../components/tournament/UpcomingTournament';
import Footer from '../components/layout/Footer';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Шапка фиксированная */}
      <Header />

      {/* Основной контент */}
      <main className="flex-grow flex flex-col">
        <HeroSection />
        <UpcomingTournament />
      </main>

      {/* Футер */}
      <Footer />
    </div>
  );
}