import React, { useEffect, useState } from 'react';
import { Search, Globe, Menu, X, GraduationCap, UserRound } from 'lucide-react';
import { NtaLogo } from './NtaLogo';
import { useLang } from '../../i18n';
type HeaderProps = {
  onOpenLogin: (role: 'trainee' | 'trainer') => void;
  onOpenSignup: () => void;
};

const HREFS = ['#about', '#programs', '#community', '#partners', '#news', '#contact'];

export function Header({ onOpenLogin, onOpenSignup }: HeaderProps) {
  const { t, toggle } = useLang();
  const NAV = HREFS.map((href, i) => ({ href, label: t.header.nav[i] }));
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, {
      passive: true
    });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target) return;
      if (!target.closest('#login-menu-anchor')) {
        setLoginOpen(false);
      }
      if (!target.closest('#site-search') && !target.closest('#site-search-toggle')) {
        setSearchOpen(false);
      }
    };
    window.addEventListener('click', onClick);
    return () => window.removeEventListener('click', onClick);
  }, []);
  const onDark = !scrolled;
  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-[background-color,box-shadow,border-color] duration-300 ${scrolled ? 'bg-white/90 backdrop-blur-md border-b border-gray-200/70 shadow-sm' : 'bg-transparent'}`}>
      
      <div className="max-w-[1200px] mx-auto px-6 md:px-8 h-[72px] flex items-center justify-between gap-4">
        <a
          href="#hero"
          className="flex items-center gap-3 shrink-0"
          aria-label="National Training Academy — home">
          
          <span
            className={`inline-flex items-center justify-center rounded-xl px-3 py-1.5 transition-[background-color,box-shadow] duration-300 ${onDark ? 'bg-white/95 shadow-sm' : 'bg-transparent'}`}>
            
            <NtaLogo className="h-8" />
          </span>
        </a>

        <nav className="hidden lg:flex items-center gap-7" aria-label="Primary">
          {NAV.map((item) =>
          <a
            key={item.label}
            href={item.href}
            className={`relative inline-flex items-center text-sm font-medium transition-colors duration-200 group ${onDark ? 'text-white/90 hover:text-white' : 'text-[#081827]/80 hover:text-[#E51B2B]'}`}>
            
              {item.label}
              <span className="absolute -bottom-1 left-0 h-[2px] w-0 bg-[#E51B2B] transition-all duration-300 group-hover:w-full" />
            </a>
          )}
        </nav>

        <div className="hidden lg:flex items-center gap-1 shrink-0">
          <button
            id="site-search-toggle"
            onClick={() => {
              setSearchOpen((s) => !s);
              setLoginOpen(false);
            }}
            className={`h-10 w-10 grid place-items-center rounded-full transition duration-200 ${onDark ? 'text-white hover:bg-white/10' : 'text-[#081827] hover:bg-gray-100'}`}
            aria-label={t.header.search}
            aria-expanded={searchOpen}
            aria-controls="site-search">
            
            <Search className="h-[18px] w-[18px]" aria-hidden="true" />
          </button>
          <button
            onClick={toggle}
            className={`h-10 px-3 inline-flex items-center gap-2 rounded-full transition duration-200 text-sm font-semibold ${onDark ? 'text-white hover:bg-white/10' : 'text-[#081827] hover:bg-gray-100'}`}
            aria-label="Switch language / تبديل اللغة">

            <Globe className="h-[16px] w-[16px]" aria-hidden="true" />
            <span>{t.header.other}</span>
          </button>

          <span
            className={`mx-2 h-6 w-px ${onDark ? 'bg-white/25' : 'bg-gray-200'}`}
            aria-hidden="true" />
          

          <div id="login-menu-anchor" className="relative">
            <button
              onClick={() => {
                setLoginOpen((s) => !s);
                setSearchOpen(false);
              }}
              className={`inline-flex items-center h-10 px-4 rounded-full font-semibold transition duration-200 text-sm ${onDark ? 'text-white hover:bg-white/10' : 'text-[#081827] hover:bg-gray-100'}`}>

              {t.header.login}
            </button>
            {loginOpen &&
            <div className="absolute top-full right-0 mt-3 w-56 rounded-2xl border border-gray-200 bg-white shadow-xl p-2">
                <button
                type="button"
                onClick={() => {
                  onOpenLogin('trainer');
                  setLoginOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-[#081827] hover:bg-gray-50 transition">

                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E51B2B]/10 text-[#E51B2B]">
                    <GraduationCap className="h-4 w-4" />
                  </span>
                  {t.header.trainerPortal}
                </button>
                <button
                type="button"
                onClick={() => {
                  onOpenLogin('trainee');
                  setLoginOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-[#081827] hover:bg-gray-50 transition">

                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E51B2B]/10 text-[#E51B2B]">
                    <UserRound className="h-4 w-4" />
                  </span>
                  {t.header.traineePortal}
                </button>
              </div>
            }
          </div>
          <button
            onClick={onOpenSignup}
            className="inline-flex items-center h-10 px-5 rounded-full bg-[#E51B2B] text-white font-semibold hover:bg-[#c4131f] active:scale-[0.98] transition duration-200 text-sm shadow-sm">

            {t.header.signup}
          </button>
        </div>

        {searchOpen &&
        <form
          id="site-search"
          role="search"
          onSubmit={(e) => e.preventDefault()}
          className="absolute left-0 right-0 top-full bg-white border-t border-gray-200/70 shadow-md">
          
              <div className="max-w-[1200px] mx-auto px-6 md:px-8 py-4 flex items-center gap-3">
              <label htmlFor="site-search-input" className="sr-only">
                {t.header.searchSite}
              </label>
              <Search
              className="h-5 w-5 text-[#081827]/60 shrink-0"
              aria-hidden="true" />
            
              <input
              id="site-search-input"
              type="search"
              autoFocus
              placeholder={t.header.searchPlaceholder}
              className="flex-1 h-11 bg-transparent outline-none text-[#081827] placeholder:text-[#081827]/50" />
            
              <button
              type="submit"
              className="h-10 px-5 rounded-full bg-[#E51B2B] text-white font-semibold hover:bg-[#c4131f] active:scale-[0.98] transition duration-200 text-sm">
              
                {t.header.search}
              </button>
              <button
              type="button"
              onClick={() => setSearchOpen(false)}
              className="h-10 w-10 grid place-items-center rounded-full text-[#081827] hover:bg-gray-100 transition duration-200"
              aria-label={t.header.closeSearch}>
              
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
        </form>
        }

        <button
          className={`lg:hidden h-10 w-10 grid place-items-center rounded-lg transition-colors ${onDark ? 'text-white' : 'text-[#081827]'}`}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? t.header.closeMenu : t.header.openMenu}
          aria-expanded={mobileOpen}>
          
          {mobileOpen ?
          <X className="h-5 w-5" aria-hidden="true" /> :

          <Menu className="h-5 w-5" aria-hidden="true" />
          }
        </button>
      </div>

      {mobileOpen &&
      <div className="lg:hidden bg-white border-t border-gray-100 px-6 py-5 space-y-1 max-h-[calc(100vh-72px)] overflow-y-auto">
          <nav aria-label="Mobile primary">
            {NAV.map((item) =>
          <a
            key={item.label}
            href={item.href}
            className="block py-3 text-[#081827] hover:text-[#E51B2B] text-sm font-semibold transition-colors">
            
                {item.label}
              </a>
          )}
          </nav>

          <div className="pt-4 mt-2 border-t border-gray-100 flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                setMobileOpen(false);
                onOpenLogin('trainee');
              }}
              className="flex-1 inline-flex items-center justify-center h-11 rounded-full border border-gray-200 text-[#081827] text-sm font-semibold hover:bg-gray-50 transition">

              {t.header.login}
            </button>
            <a
            href="#signup"
            onClick={(event) => {
              event.preventDefault();
              setMobileOpen(false);
              onOpenSignup();
            }}
            className="flex-1 inline-flex items-center justify-center h-11 rounded-full bg-[#E51B2B] text-white text-sm font-semibold hover:bg-[#c4131f] transition">

              {t.header.signup}
            </a>
          </div>
        </div>
      }
    </header>);

}
