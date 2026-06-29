import React, { useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { CONTAINER, SECTION, Eyebrow, Reveal } from './motion';
const PARTNERS = [
'Harvard Kennedy School',
'INSEAD',
'IMD Business School',
'Saïd Business School',
'Cambridge Judge',
'London Business School',
'Wharton',
'Singapore CSC'];

const EASE = [0.22, 1, 0.36, 1] as const;
export function Partners({ id = 'partners' }: { id?: string }) {
  const reduce = useReducedMotion();
  const [page, setPage] = useState(0);
  const perPage = 4;
  const pages = Math.ceil(PARTNERS.length / perPage);
  const visible = PARTNERS.slice(page * perPage, page * perPage + perPage);
  return (
    <section id={id} className={`${SECTION} bg-white scroll-mt-24`}>
      <div className={CONTAINER}>
        <Reveal className="flex items-end justify-between mb-12 flex-wrap gap-6">
          <div className="max-w-xl">
            <Eyebrow className="mb-4">Our Partners</Eyebrow>
            <h2
              className="text-[#081827] font-bold tracking-tight text-balance"
              style={{
                fontSize: 'clamp(2rem, 3.4vw, 2.875rem)',
                lineHeight: 1.1
              }}>
              
              In collaboration with the world's leading institutions.
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPage((p) => (p - 1 + pages) % pages)}
              className="h-11 w-11 rounded-full border border-gray-200 grid place-items-center text-[#081827] hover:bg-[#081827] hover:text-white hover:border-[#081827] active:scale-95 transition duration-200"
              aria-label="Previous partners">
              
              <ArrowLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage((p) => (p + 1) % pages)}
              className="h-11 w-11 rounded-full border border-gray-200 grid place-items-center text-[#081827] hover:bg-[#081827] hover:text-white hover:border-[#081827] active:scale-95 transition duration-200"
              aria-label="Next partners">
              
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </Reveal>

        <div className="relative">
          <AnimatePresence mode="wait">
            <motion.ul
              key={page}
              className="grid grid-cols-2 md:grid-cols-4 gap-5 list-none p-0 m-0"
              initial={{
                opacity: 0,
                y: reduce ? 0 : 8
              }}
              animate={{
                opacity: 1,
                y: 0
              }}
              exit={{
                opacity: 0,
                y: reduce ? 0 : -8
              }}
              transition={{
                duration: 0.3,
                ease: EASE
              }}>
              
              {visible.map((name) =>
              <li
                key={name}
                className="h-32 rounded-2xl bg-white border border-gray-200 grid place-items-center p-6 text-center hover:shadow-lg hover:shadow-gray-900/5 hover:border-gray-300 transition-[box-shadow,border-color] duration-300">
                
                  <span className="text-[#081827]/80 tracking-tight font-semibold text-[0.95rem]">
                    {name}
                  </span>
                </li>
              )}
            </motion.ul>
          </AnimatePresence>
        </div>

        <div className="mt-10 flex items-center justify-between">
          <div
            className="flex items-center gap-2"
            role="tablist"
            aria-label="Partner pages">
            
            {Array.from({
              length: pages
            }).map((_, i) => {
              const active = i === page;
              return (
                <button
                  key={i}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setPage(i)}
                  className={`h-1.5 rounded-full transition-all duration-300 ${active ? 'w-8 bg-[#E51B2B]' : 'w-2 bg-gray-300 hover:bg-gray-400'}`}
                  aria-label={`Partner page ${i + 1}`} />);


            })}
          </div>
          <a
            href="#contact"
            className="group inline-flex items-center gap-2 h-11 px-5 rounded-full border border-[#081827]/15 text-[#081827] font-semibold hover:bg-[#081827] hover:text-white active:scale-[0.98] transition duration-200 text-sm">
            
            View All Partners
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </a>
        </div>
      </div>
    </section>);

}
