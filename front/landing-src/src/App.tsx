import React from 'react';
import { useScreenInit } from './useScreenInit.js';
import { Header } from './components/nta/Header';
import { Hero } from './components/nta/Hero';
import { ExecutiveEducation } from './components/nta/ExecutiveEducation';
import { FactsFigures } from './components/nta/FactsFigures';
import { Moments } from './components/nta/Moments';
import { Partners } from './components/nta/Partners';
import { Testimonials } from './components/nta/Testimonials';
import { News } from './components/nta/News';
import { Footer } from './components/nta/Footer';
import { AuthModal } from './components/nta/AuthModal';
import { LangProvider, useLang } from './i18n';
export function App() {
  return (
    <LangProvider>
      <AppInner />
    </LangProvider>);

}
function AppInner() {
  useScreenInit();
  const { dir, lang } = useLang();
  const [authOpen, setAuthOpen] = React.useState(false);
  const [authMode, setAuthMode] = React.useState<'login' | 'signup'>('login');
  const [loginRole, setLoginRole] = React.useState<'trainee' | 'trainer'>('trainee');

  const openLogin = (role: 'trainee' | 'trainer') => {
    setLoginRole(role);
    setAuthMode('login');
    setAuthOpen(true);
  };

  const openSignup = () => {
    setAuthMode('signup');
    setAuthOpen(true);
  };

  return (
    <div
      dir={dir}
      className="min-h-screen w-full bg-white text-[#081827]"
      style={{
        fontFamily: lang === 'ar'
          ? 'Tajawal, ui-sans-serif, system-ui, sans-serif'
          : 'Inter, ui-sans-serif, system-ui, sans-serif'
      }}>
      
      <a href="#main" className="nta-skip-link">
        Skip to main content
      </a>
      <Header onOpenLogin={openLogin} onOpenSignup={openSignup} />
      <main id="main">
        <Hero />
        <FactsFigures id="about" />
        <ExecutiveEducation id="programs" />
        <Moments id="community" />
        <Partners id="partners" />
        <Testimonials id="testimonials" />
        <News id="news" />
      </main>
      <Footer id="contact" />
      <AuthModal
        open={authOpen}
        mode={authMode}
        loginRole={loginRole}
        onClose={() => setAuthOpen(false)}
        onLoginRoleChange={setLoginRole}
      />
    </div>);

}
