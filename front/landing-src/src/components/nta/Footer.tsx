import React from 'react';
import {
  Facebook,
  Twitter,
  Linkedin,
  Youtube,
  Instagram,
  ArrowRight,
  MapPin,
  Mail,
  Phone,
} from 'lucide-react';
import { NtaLogo } from './NtaLogo';
import { CONTAINER } from './motion';
import { useLang } from '../../i18n';

export function Footer({ id = 'contact' }: { id?: string }) {
  const { t, lang } = useLang();
  const quick = [
    { label: t.header.nav[0], href: '#about' },
    { label: t.header.nav[1], href: '#programs' },
    { label: t.header.nav[2], href: '#community' },
    { label: t.header.nav[3], href: '#partners' },
    { label: t.header.nav[4], href: '#news' },
    { label: t.header.nav[5], href: '#contact' },
  ];
  const campuses = t.footer.campuses;
  const socials = [
    { Icon: Facebook, label: lang === 'ar' ? 'الأكاديمية على فيسبوك' : 'NTA on Facebook' },
    { Icon: Twitter, label: lang === 'ar' ? 'الأكاديمية على X' : 'NTA on X (Twitter)' },
    { Icon: Linkedin, label: lang === 'ar' ? 'الأكاديمية على لينكدإن' : 'NTA on LinkedIn' },
    { Icon: Youtube, label: lang === 'ar' ? 'الأكاديمية على يوتيوب' : 'NTA on YouTube' },
    { Icon: Instagram, label: lang === 'ar' ? 'الأكاديمية على إنستغرام' : 'NTA on Instagram' },
  ];

  return (
    <footer id={id} className="bg-[#081827] text-white relative overflow-hidden scroll-mt-24">
      <div
        className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#E51B2B]/60 to-transparent"
        aria-hidden="true"
      />

      <div className={`${CONTAINER} pt-20 pb-10`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-4">
            <div className="mb-5 inline-flex bg-white/95 rounded-xl px-3 py-2.5">
              <NtaLogo className="h-10" />
            </div>
            <p className="text-white/75 leading-relaxed max-w-sm">{t.footer.desc}</p>

            <address className="mt-6 space-y-2.5 text-white/75 text-sm not-italic">
              <div className="flex items-center gap-3">
                <MapPin className="h-4 w-4 text-[#E51B2B] shrink-0" aria-hidden="true" />
                {t.footer.address}
              </div>
              <a href="mailto:info@nta.eg" className="flex items-center gap-3 hover:text-white transition-colors">
                <Mail className="h-4 w-4 text-[#E51B2B] shrink-0" aria-hidden="true" />
                info@nta.eg
              </a>
              <a href="tel:+20212345678" className="flex items-center gap-3 hover:text-white transition-colors">
                <Phone className="h-4 w-4 text-[#E51B2B] shrink-0" aria-hidden="true" />
                +20 (2) 1234 5678
              </a>
            </address>
          </div>

          <nav className="lg:col-span-2" aria-label={t.footer.quickLinks}>
            <h2 className="text-white mb-5 tracking-[0.12em] uppercase text-xs font-semibold">
              {t.footer.quickLinks}
            </h2>
            <ul className="space-y-3 text-white/75 text-sm">
              {quick.map((item) => (
                <li key={item.label}>
                  <a href={item.href} className="hover:text-white transition-colors">
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <nav className="lg:col-span-2" aria-label={t.footer.campusesTitle}>
            <h2 className="text-white mb-5 tracking-[0.12em] uppercase text-xs font-semibold">
              {t.footer.campusesTitle}
            </h2>
            <ul className="space-y-3 text-white/75 text-sm">
              {campuses.map((item) => (
                <li key={item}>
                  <span className="text-white/75">{item}</span>
                </li>
              ))}
            </ul>
          </nav>

          <div className="lg:col-span-4">
            <h2 className="text-white mb-5 tracking-[0.12em] uppercase text-xs font-semibold">
              {t.footer.stayUpdated}
            </h2>
            <p className="text-white/75 text-sm mb-4">{t.footer.newsletterDesc}</p>
            <form
              onSubmit={(e) => e.preventDefault()}
              aria-label={lang === 'ar' ? 'الاشتراك في النشرة البريدية' : 'Newsletter subscription'}
              className="flex items-center gap-2 pl-4 pr-1.5 py-1.5 bg-white/[0.06] border border-white/10 rounded-full focus-within:border-[#E51B2B]/60 transition"
            >
              <label htmlFor="nta-newsletter" className="sr-only">
                {lang === 'ar' ? 'البريد الإلكتروني' : 'Email address'}
              </label>
              <input
                id="nta-newsletter"
                type="email"
                required
                placeholder={t.footer.emailPlaceholder}
                aria-describedby="nta-newsletter-hint"
                className="flex-1 min-w-0 bg-transparent outline-none px-2 py-2 text-sm text-white placeholder:text-white/50"
              />

              <button
                type="submit"
                className="shrink-0 inline-flex items-center gap-1.5 px-5 h-10 rounded-full bg-[#E51B2B] hover:bg-[#c4131f] active:scale-[0.98] transition duration-200 text-sm font-semibold"
              >
                {t.footer.subscribe}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </button>
            </form>
            <p id="nta-newsletter-hint" className="mt-2 text-white/55 text-xs">
              {t.footer.privacyHint}
            </p>

            <div className="mt-6 flex items-center gap-2">
              {socials.map(({ Icon, label }) => (
                <a
                  key={label}
                  href="https://www.linkedin.com"
                  target="_blank"
                  rel="noreferrer"
                  className="h-10 w-10 grid place-items-center rounded-full bg-white/[0.06] border border-white/10 hover:bg-[#E51B2B] hover:border-[#E51B2B] active:scale-95 transition duration-200"
                  aria-label={label}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-14 pt-6 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4 text-white/60 text-xs">
          <div>
            © {new Date().getFullYear()} {t.footer.rights}
          </div>
          <div className="flex items-center gap-6">
            <a href="#contact" className="hover:text-white transition-colors">
              {t.footer.privacy}
            </a>
            <a href="#contact" className="hover:text-white transition-colors">
              {t.footer.terms}
            </a>
            <a href="#contact" className="hover:text-white transition-colors">
              {t.footer.accessibility}
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
