import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Quote } from 'lucide-react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import { CONTAINER, Eyebrow, Reveal } from './motion';
const ITEMS = [
{
  quote:
  'NTA reshaped how I think about leadership at a national scale. The program combined rigor, empathy, and a deep sense of purpose I have not encountered elsewhere.',
  name: 'Dr. Layla Hassan',
  role: 'Senior Advisor, Ministry of Planning',
  avatar:
  'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&q=80&auto=format&fit=crop'
},
{
  quote:
  'The Presidential Leadership Program brought together extraordinary peers and faculty. It is the most consequential professional experience of my career.',
  name: 'Ahmed El-Sayed',
  role: 'Director General, Digital Egypt',
  avatar:
  'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&q=80&auto=format&fit=crop'
},
{
  quote:
  "An institution that holds itself to a global standard while remaining grounded in Egypt's priorities. NTA is genuinely shaping the future of public service.",
  name: 'Nour Abdelrahman',
  role: 'Chief of Staff, Governorate Office',
  avatar:
  'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&q=80&auto=format&fit=crop'
}];

const EASE = [0.22, 1, 0.36, 1] as const;
export function Testimonials({ id = 'testimonials' }: { id?: string }) {
  const reduce = useReducedMotion();
  const [i, setI] = useState(0);
  const item = ITEMS[i];
  return (
    <section id={id} className="relative py-24 md:py-32 bg-[#081827] overflow-hidden scroll-mt-24">
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.08]"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
        aria-hidden="true">
        
        <defs>
          <pattern
            id="lines"
            width="80"
            height="80"
            patternUnits="userSpaceOnUse">
            
            <path d="M0 80 L80 0" stroke="#E51B2B" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#lines)" />
      </svg>
      <div
        className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-[#E51B2B]/15 blur-3xl"
        aria-hidden="true" />
      

      <div className={`relative ${CONTAINER}`}>
        <Reveal className="text-center mb-14">
          <Eyebrow className="mb-3">Testimonials</Eyebrow>
          <h2
            className="text-white font-bold tracking-tight"
            style={{
              fontSize: 'clamp(2rem, 3.4vw, 2.75rem)'
            }}>
            
            Voices from our alumni.
          </h2>
        </Reveal>

        <div
          className="max-w-3xl mx-auto bg-white/[0.04] border border-white/10 backdrop-blur-sm rounded-3xl p-10 md:p-14 text-center"
          aria-live="polite">
          
          <Quote
            className="h-10 w-10 text-[#E51B2B] mx-auto mb-6"
            strokeWidth={1.5}
            aria-hidden="true" />
          
          <AnimatePresence mode="wait">
            <motion.figure
              key={i}
              initial={{
                opacity: 0,
                y: reduce ? 0 : 10
              }}
              animate={{
                opacity: 1,
                y: 0
              }}
              exit={{
                opacity: 0,
                y: reduce ? 0 : -10
              }}
              transition={{
                duration: 0.35,
                ease: EASE
              }}
              className="m-0">
              
              <blockquote className="text-white/90 leading-relaxed text-[clamp(1.125rem,1.6vw,1.4rem)]">
                “{item.quote}”
              </blockquote>
              <figcaption className="mt-9 flex items-center justify-center gap-4">
                <span className="h-14 w-14 rounded-full overflow-hidden ring-2 ring-[#E51B2B]/40 shrink-0">
                  <ImageWithFallback
                    src={item.avatar}
                    alt={`Portrait of ${item.name}`}
                    className="h-full w-full object-cover" />
                  
                </span>
                <span className="text-left">
                  <span className="block text-white font-semibold">
                    {item.name}
                  </span>
                  <span className="block text-white/70 text-sm">
                    {item.role}
                  </span>
                </span>
              </figcaption>
            </motion.figure>
          </AnimatePresence>
        </div>

        <div className="mt-10 flex items-center justify-center gap-6">
          <button
            onClick={() => setI((i - 1 + ITEMS.length) % ITEMS.length)}
            className="h-11 w-11 rounded-full border border-white/25 grid place-items-center text-white hover:bg-[#E51B2B] hover:border-[#E51B2B] active:scale-95 transition duration-200"
            aria-label="Previous testimonial">
            
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div
            className="flex items-center gap-2"
            role="tablist"
            aria-label="Testimonials">
            
            {ITEMS.map((_, idx) => {
              const active = idx === i;
              return (
                <button
                  key={idx}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setI(idx)}
                  className={`h-1.5 rounded-full transition-all duration-300 ${active ? 'w-8 bg-[#E51B2B]' : 'w-2 bg-white/30 hover:bg-white/60'}`}
                  aria-label={`Testimonial ${idx + 1}`} />);


            })}
          </div>
          <button
            onClick={() => setI((i + 1) % ITEMS.length)}
            className="h-11 w-11 rounded-full border border-white/25 grid place-items-center text-white hover:bg-[#E51B2B] hover:border-[#E51B2B] active:scale-95 transition duration-200"
            aria-label="Next testimonial">
            
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </section>);

}
