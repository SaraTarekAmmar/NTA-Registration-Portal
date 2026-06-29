# NTA Homepage — Source Export

All hand-written project code, organized by file path. The project is a React + Tailwind v4 single-page app. Boot with `pnpm install && pnpm dev`.

## Project structure

```
src/
├── app/
│   ├── App.tsx
│   └── components/
│       ├── figma/
│       │   └── ImageWithFallback.tsx
│       └── nta/
│           ├── Header.tsx
│           ├── Hero.tsx
│           ├── ExecutiveEducation.tsx
│           ├── FactsFigures.tsx
│           ├── Moments.tsx
│           ├── Partners.tsx
│           ├── Testimonials.tsx
│           ├── News.tsx
│           └── Footer.tsx
├── imports/
│   └── image.png            (NTA logo — binary asset)
└── styles/
    ├── fonts.css
    └── theme.css            (NTA additions only — see below)
```

---

## `src/styles/fonts.css`

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
```

---

## `src/styles/theme.css` (NTA additions)

Add the following to your existing `theme.css`. Inside the existing `:root { ... }` block add the NTA tokens; append the focus + skip-link rules at the end of the file.

```css
:root {
  /* …existing tokens… */
  --nta-red: #E51B2B;
  --nta-red-dark: #c4131f;
  --nta-navy: #081827;
  --nta-navy-2: #0f2238;
  --nta-gray: #F6F7F9;
  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
}

/* NTA — keyboard focus visibility */
a:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--nta-red);
  outline-offset: 2px;
  border-radius: 6px;
}

.nta-skip-link {
  position: absolute;
  left: 1rem;
  top: -100px;
  z-index: 100;
  background: var(--nta-red);
  color: #fff;
  padding: 0.625rem 1rem;
  border-radius: 0.75rem;
  font-weight: 600;
  transition: top 0.2s;
}
.nta-skip-link:focus {
  top: 1rem;
}
```

---

## `src/app/App.tsx`

```tsx
import { Header } from "./components/nta/Header";
import { Hero } from "./components/nta/Hero";
import { ExecutiveEducation } from "./components/nta/ExecutiveEducation";
import { FactsFigures } from "./components/nta/FactsFigures";
import { Moments } from "./components/nta/Moments";
import { Partners } from "./components/nta/Partners";
import { Testimonials } from "./components/nta/Testimonials";
import { News } from "./components/nta/News";
import { Footer } from "./components/nta/Footer";

export default function App() {
  return (
    <div
      className="min-h-screen bg-white text-[#081827]"
      style={{ fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif" }}
    >
      <a href="#main" className="nta-skip-link">Skip to main content</a>
      <Header />
      <main id="main">
        <Hero />
        <ExecutiveEducation />
        <FactsFigures />
        <Moments />
        <Partners />
        <Testimonials />
        <News />
      </main>
      <Footer />
    </div>
  );
}
```

---

## `src/app/components/figma/ImageWithFallback.tsx`

```tsx
import React, { useState } from 'react'

const ERROR_IMG_SRC =
  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODgiIGhlaWdodD0iODgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgc3Ryb2tlPSIjMDAwIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBvcGFjaXR5PSIuMyIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIzLjciPjxyZWN0IHg9IjE2IiB5PSIxNiIgd2lkdGg9IjU2IiBoZWlnaHQ9IjU2IiByeD0iNiIvPjxwYXRoIGQ9Im0xNiA1OCAxNi0xOCAzMiAzMiIvPjxjaXJjbGUgY3g9IjUzIiBjeT0iMzUiIHI9IjciLz48L3N2Zz4KCg=='

export function ImageWithFallback(props: React.ImgHTMLAttributes<HTMLImageElement>) {
  const [didError, setDidError] = useState(false)

  const handleError = () => {
    setDidError(true)
  }

  const { src, alt, style, className, ...rest } = props

  return didError ? (
    <div
      className={`inline-block bg-gray-100 text-center align-middle ${className ?? ''}`}
      style={style}
    >
      <div className="flex items-center justify-center w-full h-full">
        <img src={ERROR_IMG_SRC} alt="Error loading image" {...rest} data-original-url={src} />
      </div>
    </div>
  ) : (
    <img src={src} alt={alt} className={className} style={style} {...rest} onError={handleError} />
  )
}
```

---

## `src/app/components/nta/Header.tsx`

```tsx
import { useEffect, useRef, useState } from "react";
import { Search, Globe, Menu, X, ChevronDown, GraduationCap, Briefcase, BookOpen, Users } from "lucide-react";
import ntaLogo from "../../../imports/image.png";

type SubItem = { label: string; desc: string; icon: React.ComponentType<{ className?: string }> };
type NavItem = { label: string; children?: SubItem[] };

const NAV: NavItem[] = [
  { label: "About" },
  { label: "Programs" },
  { label: "News" },
  { label: "Partners" },
  {
    label: "Community",
    children: [
      { label: "Alumni", desc: "Network, events, and lifelong learning", icon: GraduationCap },
      { label: "Careers", desc: "Join the NTA team", icon: Briefcase },
      { label: "Research", desc: "Publications and insights", icon: BookOpen },
      { label: "Faculty", desc: "Meet our experts", icon: Users },
    ],
  },
  { label: "Contact" },
];

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [mobileSubOpen, setMobileSubOpen] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const closeTimer = useRef<number | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const hoverOpen = (label: string) => {
    if (closeTimer.current) window.clearTimeout(closeTimer.current);
    setOpenMenu(label);
  };
  const hoverClose = () => {
    closeTimer.current = window.setTimeout(() => setOpenMenu(null), 120);
  };

  const onDark = !scrolled;

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/90 backdrop-blur-md border-b border-gray-200/70 shadow-sm"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-[1200px] mx-auto px-6 h-[72px] flex items-center justify-between">
        <a href="#" className="flex items-center gap-3">
          <span
            className={`inline-flex items-center justify-center rounded-xl px-2 py-1 transition-colors duration-300 ${
              onDark ? "bg-white/95 shadow-sm" : "bg-transparent"
            }`}
          >
            <img
              src={ntaLogo}
              alt="National Training Academy"
              className="h-8 md:h-9 w-auto max-w-[180px] object-contain"
            />
          </span>
        </a>

        <nav className="hidden lg:flex items-center gap-5">
          {NAV.map((item) => {
            const isOpen = openMenu === item.label;
            return (
              <div
                key={item.label}
                className="relative"
                onMouseEnter={() => item.children && hoverOpen(item.label)}
                onMouseLeave={() => item.children && hoverClose()}
              >
                <a
                  href="#"
                  className={`relative inline-flex items-center gap-1 text-sm transition-colors group ${
                    onDark
                      ? "text-white/85 hover:text-white"
                      : "text-[#081827]/80 hover:text-[#E51B2B]"
                  }`}
                >
                  {item.label}
                  {item.children && (
                    <ChevronDown
                      className={`h-3.5 w-3.5 transition-transform ${
                        isOpen ? "rotate-180" : ""
                      }`}
                    />
                  )}
                  <span className="absolute -bottom-1 left-0 h-[2px] w-0 bg-[#E51B2B] transition-all duration-300 group-hover:w-full" />
                </a>

                {item.children && isOpen && (
                  <div
                    className="absolute left-1/2 -translate-x-1/2 top-full pt-4"
                    onMouseEnter={() => hoverOpen(item.label)}
                    onMouseLeave={hoverClose}
                  >
                    <div className="w-[420px] bg-white rounded-2xl border border-gray-200/70 shadow-xl shadow-gray-900/10 p-3 grid grid-cols-1 gap-1">
                      {item.children.map((sub) => (
                        <a
                          key={sub.label}
                          href="#"
                          className="group flex items-start gap-3 p-3 rounded-xl hover:bg-[#F6F7F9] transition-colors"
                        >
                          <span className="h-10 w-10 grid place-items-center rounded-lg bg-[#E51B2B]/10 text-[#E51B2B] group-hover:bg-[#E51B2B] group-hover:text-white transition-colors shrink-0">
                            <sub.icon className="h-5 w-5" />
                          </span>
                          <span className="leading-tight">
                            <span
                              className="block text-[#081827]"
                              style={{ fontWeight: 600, fontSize: "0.9rem" }}
                            >
                              {sub.label}
                            </span>
                            <span className="block text-[#081827]/60 text-xs mt-0.5">
                              {sub.desc}
                            </span>
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        <div className="hidden lg:flex items-center gap-1">
          <button
            onClick={() => setSearchOpen((s) => !s)}
            className={`h-10 w-10 grid place-items-center rounded-full transition ${
              onDark ? "text-white hover:bg-white/10" : "text-[#081827] hover:bg-gray-100"
            }`}
            aria-label="Search"
            aria-expanded={searchOpen}
            aria-controls="site-search"
          >
            <Search className="h-[18px] w-[18px]" />
          </button>
          <button
            className={`h-10 px-3 inline-flex items-center gap-2 rounded-full transition text-sm ${
              onDark ? "text-white hover:bg-white/10" : "text-[#081827] hover:bg-gray-100"
            }`}
          >
            <Globe className="h-[16px] w-[16px]" />
            <span>EN</span>
            <span className="opacity-40">|</span>
            <span className="opacity-60">AR</span>
          </button>

          <span className={`mx-2 h-6 w-px ${onDark ? "bg-white/20" : "bg-gray-200"}`} />

          <a
            href="#"
            className={`inline-flex items-center h-10 px-4 rounded-full transition-colors text-sm ${
              onDark
                ? "text-white hover:bg-white/10"
                : "text-[#081827] hover:bg-gray-100"
            }`}
            style={{ fontWeight: 600 }}
          >
            Log in
          </a>
          <a
            href="#"
            className="inline-flex items-center h-10 px-5 rounded-full bg-[#E51B2B] text-white hover:bg-[#c4131f] transition-colors text-sm shadow-sm"
            style={{ fontWeight: 600 }}
          >
            Sign up
          </a>
        </div>

        {searchOpen && (
          <form
            id="site-search"
            role="search"
            onSubmit={(e) => e.preventDefault()}
            className="absolute left-0 right-0 top-full bg-white border-t border-gray-200/70 shadow-md"
          >
            <div className="max-w-[1200px] mx-auto px-6 py-4 flex items-center gap-3">
              <label htmlFor="site-search-input" className="sr-only">
                Search the site
              </label>
              <Search className="h-5 w-5 text-[#081827]/50 shrink-0" />
              <input
                id="site-search-input"
                type="search"
                autoFocus
                placeholder="Search programs, news, alumni…"
                className="flex-1 h-11 bg-transparent outline-none text-[#081827] placeholder:text-[#081827]/40"
              />
              <button
                type="submit"
                className="h-10 px-5 rounded-full bg-[#E51B2B] text-white hover:bg-[#c4131f] text-sm"
                style={{ fontWeight: 600 }}
              >
                Search
              </button>
              <button
                type="button"
                onClick={() => setSearchOpen(false)}
                className="h-10 w-10 grid place-items-center rounded-full text-[#081827] hover:bg-gray-100"
                aria-label="Close search"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </form>
        )}

        <button
          className={`lg:hidden h-10 w-10 grid place-items-center rounded-lg ${
            onDark ? "text-white" : "text-[#081827]"
          }`}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="lg:hidden bg-white border-t border-gray-100 px-6 py-5 space-y-1 max-h-[calc(100vh-72px)] overflow-y-auto">
          {NAV.map((item) =>
            item.children ? (
              <div key={item.label}>
                <button
                  onClick={() =>
                    setMobileSubOpen(mobileSubOpen === item.label ? null : item.label)
                  }
                  className="w-full flex items-center justify-between py-3 text-[#081827] text-sm"
                  style={{ fontWeight: 600 }}
                >
                  {item.label}
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${
                      mobileSubOpen === item.label ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {mobileSubOpen === item.label && (
                  <div className="pl-4 pb-2 space-y-2">
                    {item.children.map((sub) => (
                      <a
                        key={sub.label}
                        href="#"
                        className="flex items-center gap-3 py-2 text-[#081827]/80 hover:text-[#E51B2B] text-sm"
                      >
                        <sub.icon className="h-4 w-4 text-[#E51B2B]" />
                        {sub.label}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <a
                key={item.label}
                href="#"
                className="block py-3 text-[#081827] hover:text-[#E51B2B] text-sm"
                style={{ fontWeight: 600 }}
              >
                {item.label}
              </a>
            )
          )}

          <div className="pt-4 mt-2 border-t border-gray-100 flex items-center gap-3">
            <a
              href="#"
              className="flex-1 inline-flex items-center justify-center h-11 rounded-full border border-gray-200 text-[#081827] text-sm"
              style={{ fontWeight: 600 }}
            >
              Log in
            </a>
            <a
              href="#"
              className="flex-1 inline-flex items-center justify-center h-11 rounded-full bg-[#E51B2B] text-white text-sm"
              style={{ fontWeight: 600 }}
            >
              Sign up
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
```

---

## `src/app/components/nta/Hero.tsx`

```tsx
import { ArrowRight, ChevronRight } from "lucide-react";
import { ImageWithFallback } from "../figma/ImageWithFallback";

export function Hero() {
  return (
    <section className="relative min-h-[760px] h-screen max-h-[860px] w-full overflow-hidden">
      <ImageWithFallback
        src="https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1920&q=80&auto=format&fit=crop"
        alt="Leadership conference"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[#081827]/95 via-[#081827]/70 to-[#081827]/30" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#081827]/90 via-transparent to-transparent" />

      <div className="relative z-10 max-w-[1200px] mx-auto px-6 pt-40 pb-24 h-full flex flex-col justify-center">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 backdrop-blur-sm mb-6">
            <span className="h-1.5 w-1.5 rounded-full bg-[#E51B2B]" />
            <span className="text-white/90 text-xs tracking-wider uppercase">
              National Training Academy
            </span>
          </div>

          <h1
            className="text-white tracking-tight"
            style={{ fontSize: "clamp(2.5rem, 5vw, 4.25rem)", fontWeight: 700, lineHeight: 1.05 }}
          >
            Empowering Leaders.
            <br />
            <span className="text-white/95">Transforming </span>
            <span className="relative inline-block">
              <span className="relative z-10">Communities.</span>
              <span className="absolute -bottom-1 left-0 right-0 h-[6px] bg-[#E51B2B]/80 -skew-x-6" />
            </span>
          </h1>

          <p className="mt-6 text-white/80 text-lg leading-relaxed max-w-xl">
            Egypt's premier institution for leadership development, capacity
            building, and executive education, preparing the next generation
            to shape national progress.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-4">
            <a
              href="#programs"
              className="group inline-flex items-center gap-2 h-12 px-6 rounded-xl bg-[#E51B2B] text-white hover:bg-[#c4131f] transition-all shadow-lg shadow-[#E51B2B]/30 hover:shadow-xl hover:shadow-[#E51B2B]/40"
              style={{ fontWeight: 600 }}
            >
              Explore Programs
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </a>
            <a
              href="#about"
              className="inline-flex items-center gap-2 h-12 px-6 rounded-xl border border-white/30 text-white hover:bg-white/10 backdrop-blur-sm transition-all"
              style={{ fontWeight: 600 }}
            >
              About NTA
              <ChevronRight className="h-4 w-4" />
            </a>
          </div>

          <div className="mt-14 flex items-center gap-2">
            {[0, 1, 2, 3].map((i) => (
              <button
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === 0 ? "w-10 bg-[#E51B2B]" : "w-6 bg-white/30 hover:bg-white/60"
                }`}
                aria-label={`Slide ${i + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/ExecutiveEducation.tsx`

```tsx
import {
  Crown,
  GraduationCap,
  Rocket,
  Scale,
  Cpu,
  Compass,
  ArrowRight,
} from "lucide-react";

const PROGRAMS = [
  {
    icon: Crown,
    title: "Presidential Leadership Program",
    desc: "An elite program shaping Egypt's most senior public-sector leaders through immersive strategic learning.",
  },
  {
    icon: GraduationCap,
    title: "Executive Education",
    desc: "Advanced programs designed for executives ready to drive organizational transformation at scale.",
  },
  {
    icon: Rocket,
    title: "Future Leaders",
    desc: "Cultivating ambitious young professionals with the vision and tools to lead Egypt's next chapter.",
  },
  {
    icon: Scale,
    title: "Public Policy",
    desc: "Evidence-based policy training that equips officials to design and implement effective national initiatives.",
  },
  {
    icon: Cpu,
    title: "Digital Transformation",
    desc: "Building digital fluency and innovation mindset across government and public services.",
  },
  {
    icon: Compass,
    title: "Strategic Management",
    desc: "Equipping leaders with frameworks to navigate complexity, ambiguity, and long-term strategy.",
  },
];

export function ExecutiveEducation() {
  return (
    <section id="programs" className="py-20 md:py-28 bg-white">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="max-w-2xl mb-14">
          <div className="mb-4">
            <span className="text-[#E51B2B] text-xs tracking-[0.2em] uppercase">
              Executive Education
            </span>
          </div>
          <h2
            className="text-[#081827] tracking-tight"
            style={{ fontSize: "clamp(2rem, 3.4vw, 3rem)", fontWeight: 700, lineHeight: 1.1 }}
          >
            Programs that shape national leaders.
          </h2>
          <p className="mt-5 text-[#081827]/65 text-lg leading-relaxed">
            Carefully designed curricula combining global best practice with
            local insight, preparing executives, policymakers, and emerging
            leaders to deliver lasting impact.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {PROGRAMS.map(({ icon: Icon, title, desc }) => (
            <article
              key={title}
              className="group relative bg-white rounded-2xl border border-gray-200/70 p-7 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-gray-200/60 hover:border-gray-200 overflow-hidden"
            >
              <span className="absolute top-0 left-0 right-0 h-[3px] bg-[#E51B2B] scale-x-0 group-hover:scale-x-100 origin-left transition-transform duration-300" />

              <div className="h-12 w-12 rounded-xl bg-[#E51B2B]/10 text-[#E51B2B] grid place-items-center mb-5 group-hover:bg-[#E51B2B] group-hover:text-white transition-colors">
                <Icon className="h-6 w-6" strokeWidth={1.75} />
              </div>

              <h3
                className="text-[#081827] mb-3"
                style={{ fontSize: "1.25rem", fontWeight: 600, lineHeight: 1.3 }}
              >
                {title}
              </h3>
              <p className="text-[#081827]/65 leading-relaxed text-[15px]">
                {desc}
              </p>

              <a
                href="#"
                className="mt-6 inline-flex items-center gap-1.5 text-[#E51B2B] text-sm group/link"
                style={{ fontWeight: 600 }}
              >
                Learn more
                <ArrowRight className="h-4 w-4 transition-transform group-hover/link:translate-x-1" />
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/FactsFigures.tsx`

```tsx
import { BookOpen, Users, Clock, Building2 } from "lucide-react";

const STATS = [
  { icon: BookOpen, value: "850+", label: "Training Programs" },
  { icon: Users, value: "45,000+", label: "Trainees Graduated" },
  { icon: Clock, value: "1.2M", label: "Training Hours" },
  { icon: Building2, value: "120+", label: "Partner Institutions" },
];

export function FactsFigures() {
  return (
    <section className="relative py-20 md:py-24 bg-[#081827] overflow-hidden">
      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 30%, #E51B2B 0%, transparent 40%), radial-gradient(circle at 80% 70%, #E51B2B 0%, transparent 35%)",
        }}
      />
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#E51B2B]/50 to-transparent" />

      <div className="relative max-w-[1200px] mx-auto px-6">
        <div className="text-center mb-14">
          <div className="mb-3">
            <span className="text-[#E51B2B] text-xs tracking-[0.2em] uppercase">
              Facts & Figures
            </span>
          </div>
          <h2
            className="text-white tracking-tight"
            style={{ fontSize: "clamp(1.75rem, 3vw, 2.5rem)", fontWeight: 700 }}
          >
            A decade of measurable impact.
          </h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 rounded-2xl overflow-hidden border border-white/10">
          {STATS.map(({ icon: Icon, value, label }) => (
            <div
              key={label}
              className="bg-[#081827] px-6 py-10 text-center group hover:bg-[#0f2238] transition-colors"
            >
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-[#E51B2B]/15 text-[#E51B2B] mb-5 group-hover:scale-110 transition-transform">
                <Icon className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <div
                className="text-white tracking-tight"
                style={{ fontSize: "clamp(2rem, 3.6vw, 3rem)", fontWeight: 700 }}
              >
                {value}
              </div>
              <div className="mt-2 text-white/60 text-sm tracking-wide uppercase">
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/Moments.tsx`

```tsx
import { Play } from "lucide-react";
import { ImageWithFallback } from "../figma/ImageWithFallback";

const FEATURED = {
  src: "https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=1400&q=80&auto=format&fit=crop",
  label: "Featured",
  title: "Presidential Leadership Program: 2026 Cohort Closing Ceremony",
  duration: "4:32",
};

const SECONDARY = [
  {
    src: "https://images.unsplash.com/photo-1559223607-a43c990c692c?w=800&q=80&auto=format&fit=crop",
    label: "Event",
    title: "NTA Summit on Public Sector Innovation",
    duration: "2:18",
  },
  {
    src: "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800&q=80&auto=format&fit=crop",
    label: "Story",
    title: "Future Leaders: Voices of the Next Generation",
    duration: "3:05",
  },
];

function PlayBadge({ size = "lg" }: { size?: "lg" | "sm" }) {
  return (
    <div
      className={`${
        size === "lg" ? "h-16 w-16" : "h-11 w-11"
      } rounded-full bg-white/95 grid place-items-center shadow-2xl group-hover:bg-[#E51B2B] group-hover:scale-110 transition-all duration-300`}
    >
      <Play
        className={`${
          size === "lg" ? "h-6 w-6 ml-1" : "h-4 w-4 ml-0.5"
        } text-[#E51B2B] group-hover:text-white fill-current`}
      />
    </div>
  );
}

export function Moments() {
  return (
    <section className="py-20 md:py-28 bg-[#F6F7F9]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="flex items-end justify-between mb-12 flex-wrap gap-4">
          <div className="max-w-xl">
            <div className="mb-4">
              <span className="text-[#E51B2B] text-xs tracking-[0.2em] uppercase">
                NTA Moments
              </span>
            </div>
            <h2
              className="text-[#081827] tracking-tight"
              style={{ fontSize: "clamp(2rem, 3.4vw, 3rem)", fontWeight: 700, lineHeight: 1.1 }}
            >
              Inside the Academy.
            </h2>
          </div>
          <a
            href="#"
            className="text-[#E51B2B] text-sm inline-flex items-center gap-1"
            style={{ fontWeight: 600 }}
          >
            View all videos →
          </a>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 group relative rounded-2xl overflow-hidden cursor-pointer aspect-[16/10] lg:aspect-auto">
            <ImageWithFallback
              src={FEATURED.src}
              alt={FEATURED.title}
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#081827]/90 via-[#081827]/20 to-transparent" />
            <div className="absolute inset-0 grid place-items-center">
              <PlayBadge />
            </div>
            <div className="absolute bottom-0 left-0 right-0 p-7">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#E51B2B] text-white text-[11px] tracking-wider uppercase mb-3">
                {FEATURED.label}
              </span>
              <h3
                className="text-white max-w-xl"
                style={{ fontSize: "1.5rem", fontWeight: 600, lineHeight: 1.25 }}
              >
                {FEATURED.title}
              </h3>
              <div className="mt-2 text-white/70 text-sm">{FEATURED.duration}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-6">
            {SECONDARY.map((v) => (
              <div
                key={v.title}
                className="group relative rounded-2xl overflow-hidden cursor-pointer aspect-[16/10] lg:aspect-[16/11]"
              >
                <ImageWithFallback
                  src={v.src}
                  alt={v.title}
                  className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#081827]/90 via-[#081827]/10 to-transparent" />
                <div className="absolute inset-0 grid place-items-center">
                  <PlayBadge size="sm" />
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-white/15 backdrop-blur text-white text-[10px] tracking-wider uppercase mb-2">
                    {v.label}
                  </span>
                  <h4
                    className="text-white"
                    style={{ fontSize: "1rem", fontWeight: 600, lineHeight: 1.3 }}
                  >
                    {v.title}
                  </h4>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/Partners.tsx`

```tsx
import { useState } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";

const PARTNERS = [
  "Harvard Kennedy School",
  "INSEAD",
  "IMD Business School",
  "Saïd Business School",
  "Cambridge Judge",
  "London Business School",
  "Wharton",
  "Singapore CSC",
];

export function Partners() {
  const [page, setPage] = useState(0);
  const perPage = 4;
  const pages = Math.ceil(PARTNERS.length / perPage);
  const visible = PARTNERS.slice(page * perPage, page * perPage + perPage);

  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="flex items-end justify-between mb-12 flex-wrap gap-6">
          <div className="max-w-xl">
            <div className="mb-4">
              <span className="text-[#E51B2B] text-xs tracking-[0.2em] uppercase">
                Our Partners
              </span>
            </div>
            <h2
              className="text-[#081827] tracking-tight"
              style={{ fontSize: "clamp(2rem, 3.4vw, 3rem)", fontWeight: 700, lineHeight: 1.1 }}
            >
              In collaboration with the world's leading institutions.
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPage((p) => (p - 1 + pages) % pages)}
              className="h-11 w-11 rounded-full border border-gray-200 grid place-items-center text-[#081827] hover:bg-[#E51B2B] hover:text-white hover:border-[#E51B2B] transition"
              aria-label="Previous"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage((p) => (p + 1) % pages)}
              className="h-11 w-11 rounded-full border border-gray-200 grid place-items-center text-[#081827] hover:bg-[#E51B2B] hover:text-white hover:border-[#E51B2B] transition"
              aria-label="Next"
            >
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          {visible.map((name) => (
            <div
              key={name}
              className="h-32 rounded-2xl bg-white border border-gray-200/80 grid place-items-center p-6 text-center hover:shadow-lg hover:border-gray-200 transition-all"
            >
              <span
                className="text-[#081827]/75 tracking-tight"
                style={{ fontWeight: 600, fontSize: "0.95rem" }}
              >
                {name}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {Array.from({ length: pages }).map((_, i) => (
              <button
                key={i}
                onClick={() => setPage(i)}
                className={`h-1.5 rounded-full transition-all ${
                  i === page ? "w-8 bg-[#E51B2B]" : "w-2 bg-gray-300 hover:bg-gray-400"
                }`}
                aria-label={`Page ${i + 1}`}
              />
            ))}
          </div>
          <a
            href="#"
            className="inline-flex items-center gap-2 h-11 px-5 rounded-full border border-[#081827]/15 text-[#081827] hover:bg-[#081827] hover:text-white transition text-sm"
            style={{ fontWeight: 600 }}
          >
            View All Partners
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/Testimonials.tsx`

```tsx
import { useState } from "react";
import { ArrowLeft, ArrowRight, Quote } from "lucide-react";
import { ImageWithFallback } from "../figma/ImageWithFallback";

const ITEMS = [
  {
    quote:
      "NTA reshaped how I think about leadership at a national scale. The program combined rigor, empathy, and a deep sense of purpose I have not encountered elsewhere.",
    name: "Dr. Layla Hassan",
    role: "Senior Advisor, Ministry of Planning",
    avatar:
      "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&q=80&auto=format&fit=crop",
  },
  {
    quote:
      "The Presidential Leadership Program brought together extraordinary peers and faculty. It is the most consequential professional experience of my career.",
    name: "Ahmed El-Sayed",
    role: "Director General, Digital Egypt",
    avatar:
      "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&q=80&auto=format&fit=crop",
  },
  {
    quote:
      "An institution that holds itself to a global standard while remaining grounded in Egypt's priorities. NTA is genuinely shaping the future of public service.",
    name: "Nour Abdelrahman",
    role: "Chief of Staff, Governorate Office",
    avatar:
      "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&q=80&auto=format&fit=crop",
  },
];

export function Testimonials() {
  const [i, setI] = useState(0);
  const item = ITEMS[i];

  return (
    <section className="relative py-24 md:py-32 bg-[#081827] overflow-hidden">
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.08]"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          <pattern id="lines" width="80" height="80" patternUnits="userSpaceOnUse">
            <path d="M0 80 L80 0" stroke="#E51B2B" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#lines)" />
      </svg>
      <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-[#E51B2B]/15 blur-3xl" />

      <div className="relative max-w-[1200px] mx-auto px-6">
        <div className="text-center mb-14">
          <div className="mb-3">
            <span className="text-[#E51B2B] text-xs tracking-[0.2em] uppercase">
              Testimonials
            </span>
          </div>
          <h2
            className="text-white tracking-tight"
            style={{ fontSize: "clamp(2rem, 3.4vw, 2.75rem)", fontWeight: 700 }}
          >
            Voices from our alumni.
          </h2>
        </div>

        <div className="max-w-3xl mx-auto bg-white/[0.04] border border-white/10 backdrop-blur-sm rounded-3xl p-10 md:p-14 text-center">
          <Quote className="h-10 w-10 text-[#E51B2B] mx-auto mb-6" strokeWidth={1.5} />
          <p
            className="text-white/90 leading-relaxed"
            style={{ fontSize: "clamp(1.125rem, 1.6vw, 1.4rem)", fontWeight: 400 }}
          >
            "{item.quote}"
          </p>
          <div className="mt-9 flex items-center justify-center gap-4">
            <div className="h-14 w-14 rounded-full overflow-hidden ring-2 ring-[#E51B2B]/40">
              <ImageWithFallback
                src={item.avatar}
                alt={item.name}
                className="h-full w-full object-cover"
              />
            </div>
            <div className="text-left">
              <div className="text-white" style={{ fontWeight: 600 }}>
                {item.name}
              </div>
              <div className="text-white/60 text-sm">{item.role}</div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex items-center justify-center gap-6">
          <button
            onClick={() => setI((i - 1 + ITEMS.length) % ITEMS.length)}
            className="h-11 w-11 rounded-full border border-white/20 grid place-items-center text-white hover:bg-[#E51B2B] hover:border-[#E51B2B] transition"
            aria-label="Previous"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            {ITEMS.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setI(idx)}
                className={`h-1.5 rounded-full transition-all ${
                  idx === i ? "w-8 bg-[#E51B2B]" : "w-2 bg-white/25 hover:bg-white/50"
                }`}
                aria-label={`Slide ${idx + 1}`}
              />
            ))}
          </div>
          <button
            onClick={() => setI((i + 1) % ITEMS.length)}
            className="h-11 w-11 rounded-full border border-white/20 grid place-items-center text-white hover:bg-[#E51B2B] hover:border-[#E51B2B] transition"
            aria-label="Next"
          >
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/News.tsx`

```tsx
import { ArrowRight, Calendar } from "lucide-react";
import { ImageWithFallback } from "../figma/ImageWithFallback";

const NEWS = [
  {
    img: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=900&q=80&auto=format&fit=crop",
    category: "Announcement",
    date: "May 28, 2026",
    title:
      "NTA Launches New Cohort of the Presidential Leadership Program",
    excerpt:
      "A new generation of senior officials begins an immersive 18-month journey across strategy, policy, and innovation.",
  },
  {
    img: "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=900&q=80&auto=format&fit=crop",
    category: "Partnership",
    date: "May 14, 2026",
    title:
      "Strategic Partnership Signed with Saïd Business School, Oxford",
    excerpt:
      "Expanded collaboration brings world-class executive curricula and joint research initiatives to Cairo.",
  },
  {
    img: "https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=900&q=80&auto=format&fit=crop",
    category: "Insight",
    date: "April 30, 2026",
    title: "Reimagining Capacity Building for the Digital Era",
    excerpt:
      "NTA faculty outline a new framework for upskilling public servants across data, AI, and digital service design.",
  },
];

export function News() {
  return (
    <section className="py-20 md:py-28 bg-[#F6F7F9]">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="flex items-end justify-between mb-12 flex-wrap gap-4">
          <div className="max-w-xl">
            <div className="mb-4">
              <span className="text-[#E51B2B] text-xs tracking-[0.2em] uppercase">
                In the News
              </span>
            </div>
            <h2
              className="text-[#081827] tracking-tight"
              style={{ fontSize: "clamp(2rem, 3.4vw, 3rem)", fontWeight: 700, lineHeight: 1.1 }}
            >
              Stories, updates, and insights.
            </h2>
          </div>
          <a
            href="#"
            className="inline-flex items-center gap-2 text-[#E51B2B] text-sm"
            style={{ fontWeight: 600 }}
          >
            All news
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {NEWS.map((n) => (
            <article
              key={n.title}
              className="group bg-white rounded-2xl overflow-hidden border border-gray-200/70 hover:shadow-xl hover:-translate-y-1 hover:border-gray-200 transition-all duration-300"
            >
              <div className="relative aspect-[16/10] overflow-hidden">
                <ImageWithFallback
                  src={n.img}
                  alt={n.title}
                  className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                <span className="absolute top-4 left-4 inline-flex items-center px-2.5 py-1 rounded-full bg-white/95 text-[#E51B2B] text-[11px] tracking-wider uppercase">
                  {n.category}
                </span>
              </div>
              <div className="p-6">
                <div className="flex items-center gap-2 text-[#081827]/55 text-xs mb-3">
                  <Calendar className="h-3.5 w-3.5" />
                  {n.date}
                </div>
                <h3
                  className="text-[#081827] mb-3 group-hover:text-[#E51B2B] transition-colors"
                  style={{ fontSize: "1.15rem", fontWeight: 600, lineHeight: 1.3 }}
                >
                  {n.title}
                </h3>
                <p className="text-[#081827]/65 text-[15px] leading-relaxed">
                  {n.excerpt}
                </p>
                <a
                  href="#"
                  className="mt-5 inline-flex items-center gap-1.5 text-[#E51B2B] text-sm group/link"
                  style={{ fontWeight: 600 }}
                >
                  Read More
                  <ArrowRight className="h-4 w-4 transition-transform group-hover/link:translate-x-1" />
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
```

---

## `src/app/components/nta/Footer.tsx`

```tsx
import ntaLogo from "../../../imports/image.png";
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
} from "lucide-react";

const QUICK = ["About NTA", "Programs", "Faculty", "Research", "News", "Careers"];
const CAMPUS = [
  "New Administrative Capital",
  "Cairo Campus",
  "Alexandria Hub",
  "Virtual Campus",
  "Library",
  "Alumni Portal",
];

export function Footer() {
  return (
    <footer className="bg-[#081827] text-white relative overflow-hidden">
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#E51B2B]/60 to-transparent" />
      <div className="max-w-[1200px] mx-auto px-6 pt-20 pb-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-4">
            <div className="mb-5 inline-flex bg-white/95 rounded-xl px-3 py-2">
              <img
                src={ntaLogo}
                alt="National Training Academy"
                className="h-10 w-auto max-w-[200px] object-contain"
              />
            </div>
            <p className="text-white/65 leading-relaxed max-w-sm">
              Egypt's flagship institution for leadership development and
              executive education, equipping public servants to deliver
              meaningful national impact.
            </p>

            <div className="mt-6 space-y-2.5 text-white/70 text-sm">
              <div className="flex items-center gap-3">
                <MapPin className="h-4 w-4 text-[#E51B2B]" />
                New Administrative Capital, Egypt
              </div>
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-[#E51B2B]" />
                info@nta.eg
              </div>
              <div className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-[#E51B2B]" />
                +20 (2) 1234 5678
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <h4 className="text-white mb-5 tracking-wide uppercase text-xs" style={{ fontWeight: 600 }}>
              Quick Links
            </h4>
            <ul className="space-y-3 text-white/70 text-sm">
              {QUICK.map((l) => (
                <li key={l}>
                  <a href="#" className="hover:text-[#E51B2B] transition-colors">
                    {l}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-2">
            <h4 className="text-white mb-5 tracking-wide uppercase text-xs" style={{ fontWeight: 600 }}>
              Campuses
            </h4>
            <ul className="space-y-3 text-white/70 text-sm">
              {CAMPUS.map((l) => (
                <li key={l}>
                  <a href="#" className="hover:text-[#E51B2B] transition-colors">
                    {l}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-4">
            <h4 className="text-white mb-5 tracking-wide uppercase text-xs" style={{ fontWeight: 600 }}>
              Stay Updated
            </h4>
            <p className="text-white/65 text-sm mb-4">
              Subscribe for program announcements, research, and stories from
              across NTA.
            </p>
            <form
              onSubmit={(e) => e.preventDefault()}
              aria-label="Newsletter subscription"
              className="flex items-center gap-2 pl-2 pr-1.5 py-1.5 bg-white/[0.06] border border-white/10 rounded-full focus-within:border-[#E51B2B]/60 transition overflow-hidden"
            >
              <label htmlFor="nta-newsletter" className="sr-only">
                Email address
              </label>
              <input
                id="nta-newsletter"
                type="email"
                required
                placeholder="Your email address"
                aria-describedby="nta-newsletter-hint"
                className="flex-1 bg-transparent outline-none px-4 py-2 text-sm text-white placeholder:text-white/40"
              />
              <button
                type="submit"
                className="shrink-0 inline-flex items-center gap-1.5 px-5 h-10 rounded-full bg-[#E51B2B] hover:bg-[#c4131f] transition text-sm"
                style={{ fontWeight: 600 }}
              >
                Subscribe
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>
            <p id="nta-newsletter-hint" className="mt-2 text-white/45 text-xs">
              We respect your privacy. Unsubscribe at any time.
            </p>

            <div className="mt-6 flex items-center gap-2">
              {[Facebook, Twitter, Linkedin, Youtube, Instagram].map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  className="h-10 w-10 grid place-items-center rounded-full bg-white/[0.06] border border-white/10 hover:bg-[#E51B2B] hover:border-[#E51B2B] transition-colors"
                  aria-label="Social"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-14 pt-6 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4 text-white/50 text-xs">
          <div>© {new Date().getFullYear()} National Training Academy. All rights reserved.</div>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Use</a>
            <a href="#" className="hover:text-white transition-colors">Accessibility</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
```
