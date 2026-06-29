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
  Phone } from
'lucide-react';
import { NtaLogo } from './NtaLogo';
import { CONTAINER } from './motion';
const QUICK = [
  { label: 'About NTA', href: '#about' },
  { label: 'Programs', href: '#programs' },
  { label: 'Community', href: '#community' },
  { label: 'Partners', href: '#partners' },
  { label: 'News', href: '#news' },
  { label: 'Contact', href: '#contact' }
];

const CAMPUS = [
  'New Administrative Capital',
  'Cairo Campus',
  'Alexandria Hub',
  'Virtual Campus',
  'Library',
  'Alumni Portal'
];

const SOCIALS = [
{
  Icon: Facebook,
  label: 'NTA on Facebook'
},
{
  Icon: Twitter,
  label: 'NTA on X (Twitter)'
},
{
  Icon: Linkedin,
  label: 'NTA on LinkedIn'
},
{
  Icon: Youtube,
  label: 'NTA on YouTube'
},
{
  Icon: Instagram,
  label: 'NTA on Instagram'
}];

export function Footer({ id = 'contact' }: { id?: string }) {
  return (
    <footer id={id} className="bg-[#081827] text-white relative overflow-hidden scroll-mt-24">
      <div
        className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#E51B2B]/60 to-transparent"
        aria-hidden="true" />
      
      <div className={`${CONTAINER} pt-20 pb-10`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-4">
            <div className="mb-5 inline-flex bg-white/95 rounded-xl px-3 py-2.5">
              <NtaLogo className="h-10" />
            </div>
            <p className="text-white/75 leading-relaxed max-w-sm">
              Egypt's flagship institution for leadership development and
              executive education, equipping public servants to deliver
              meaningful national impact.
            </p>

            <address className="mt-6 space-y-2.5 text-white/75 text-sm not-italic">
              <div className="flex items-center gap-3">
                <MapPin
                  className="h-4 w-4 text-[#E51B2B] shrink-0"
                  aria-hidden="true" />
                
                New Administrative Capital, Egypt
              </div>
              <a
                href="mailto:info@nta.eg"
                className="flex items-center gap-3 hover:text-white transition-colors">
                
                <Mail
                  className="h-4 w-4 text-[#E51B2B] shrink-0"
                  aria-hidden="true" />
                
                info@nta.eg
              </a>
              <a
                href="tel:+20212345678"
                className="flex items-center gap-3 hover:text-white transition-colors">
                
                <Phone
                  className="h-4 w-4 text-[#E51B2B] shrink-0"
                  aria-hidden="true" />
                
                +20 (2) 1234 5678
              </a>
            </address>
          </div>

          <nav className="lg:col-span-2" aria-label="Quick links">
            <h2 className="text-white mb-5 tracking-[0.12em] uppercase text-xs font-semibold">
              Quick Links
            </h2>
            <ul className="space-y-3 text-white/75 text-sm">
              {QUICK.map((l) =>
              <li key={l.label}>
                  <a href={l.href} className="hover:text-white transition-colors">
                    {l.label}
                  </a>
                </li>
              )}
            </ul>
          </nav>

          <nav className="lg:col-span-2" aria-label="Campuses">
            <h2 className="text-white mb-5 tracking-[0.12em] uppercase text-xs font-semibold">
              Campuses
            </h2>
            <ul className="space-y-3 text-white/75 text-sm">
              {CAMPUS.map((l) =>
              <li key={l}>
                  <span className="text-white/75">
                    {l}
                  </span>
                </li>
              )}
            </ul>
          </nav>

          <div className="lg:col-span-4">
            <h2 className="text-white mb-5 tracking-[0.12em] uppercase text-xs font-semibold">
              Stay Updated
            </h2>
            <p className="text-white/75 text-sm mb-4">
              Subscribe for program announcements, research, and stories from
              across NTA.
            </p>
            <form
              onSubmit={(e) => e.preventDefault()}
              aria-label="Newsletter subscription"
              className="flex items-center gap-2 pl-4 pr-1.5 py-1.5 bg-white/[0.06] border border-white/10 rounded-full focus-within:border-[#E51B2B]/60 transition">
              
              <label htmlFor="nta-newsletter" className="sr-only">
                Email address
              </label>
              <input
                id="nta-newsletter"
                type="email"
                required
                placeholder="Your email address"
                aria-describedby="nta-newsletter-hint"
                className="flex-1 min-w-0 bg-transparent outline-none px-2 py-2 text-sm text-white placeholder:text-white/50" />
              
              <button
                type="submit"
                className="shrink-0 inline-flex items-center gap-1.5 px-5 h-10 rounded-full bg-[#E51B2B] hover:bg-[#c4131f] active:scale-[0.98] transition duration-200 text-sm font-semibold">
                
                Subscribe
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </button>
            </form>
            <p id="nta-newsletter-hint" className="mt-2 text-white/55 text-xs">
              We respect your privacy. Unsubscribe at any time.
            </p>

            <div className="mt-6 flex items-center gap-2">
              {SOCIALS.map(({ Icon, label }) =>
              <a
                key={label}
                href="https://www.linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="h-10 w-10 grid place-items-center rounded-full bg-white/[0.06] border border-white/10 hover:bg-[#E51B2B] hover:border-[#E51B2B] active:scale-95 transition duration-200"
                aria-label={label}>
                
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </a>
              )}
            </div>
          </div>
        </div>

        <div className="mt-14 pt-6 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4 text-white/60 text-xs">
          <div>
            © {new Date().getFullYear()} National Training Academy. All rights
            reserved.
          </div>
          <div className="flex items-center gap-6">
            <a href="#contact" className="hover:text-white transition-colors">
              Privacy Policy
            </a>
            <a href="#contact" className="hover:text-white transition-colors">
              Terms of Use
            </a>
            <a href="#contact" className="hover:text-white transition-colors">
              Accessibility
            </a>
          </div>
        </div>
      </div>
    </footer>);

}
