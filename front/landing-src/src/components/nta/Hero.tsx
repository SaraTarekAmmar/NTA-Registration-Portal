import React, { useState, Children } from 'react';
import { ArrowRight, ChevronRight } from 'lucide-react';
import { motion, useReducedMotion, type Variants } from 'framer-motion';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import { CONTAINER } from './motion';
import { useLang } from '../../i18n';
const EASE = [0.22, 1, 0.36, 1] as const;
export function Hero({ id = 'hero' }: { id?: string }) {
  const { t } = useLang();
  const reduce = useReducedMotion();
  const [slide, setSlide] = useState(0);
  const container: Variants = {
    hidden: {},
    show: {
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.05
      }
    }
  };
  const item: Variants = {
    hidden: {
      opacity: 0,
      y: reduce ? 0 : 18
    },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.55,
        ease: EASE
      }
    }
  };
  return (
    <section id={id} className="relative min-h-[760px] h-screen max-h-[860px] w-full overflow-hidden scroll-mt-24">
      <ImageWithFallback
        src="https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1920&q=80&auto=format&fit=crop"
        alt="Leadership conference attendees seated in an auditorium"
        className="absolute inset-0 h-full w-full object-cover" />
      
      {/* Functional overlays for text legibility */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#081827]/95 via-[#081827]/70 to-[#081827]/30" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#081827]/90 via-transparent to-transparent" />

      <div
        className={`relative z-10 ${CONTAINER} pt-40 pb-24 h-full flex flex-col justify-center`}>
        
        <motion.div
          className="max-w-2xl"
          variants={container}
          initial="hidden"
          animate="show">
          
          <motion.h1
            variants={item}
            className="text-white font-bold tracking-tight text-balance"
            style={{
              fontSize: 'clamp(2.5rem, 5vw, 4.25rem)',
              lineHeight: 1.05
            }}>
            
            {t.hero.lead}
            <br />
            {t.hero.rest}{' '}
            <span className="relative inline-block">
              <span className="relative z-10">{t.hero.highlight}</span>
              <span className="absolute -bottom-1 left-0 right-0 h-[6px] bg-[#E51B2B] -skew-x-6" />
            </span>
          </motion.h1>

          <motion.p
            variants={item}
            className="mt-6 text-white/85 text-lg leading-relaxed max-w-[58ch]">
            
            {t.hero.subtitle}
          </motion.p>

          <motion.div
            variants={item}
            className="mt-9 flex flex-wrap items-center gap-4">
            
            <a
              href="#programs"
              className="group inline-flex items-center gap-2 h-12 px-6 rounded-xl bg-[#E51B2B] text-white font-semibold hover:bg-[#c4131f] active:scale-[0.98] transition-[background-color,transform] duration-200 shadow-lg shadow-[#E51B2B]/25">
              
              {t.hero.explore}
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </a>
            <a
              href="#about"
              className="inline-flex items-center gap-2 h-12 px-6 rounded-xl border border-white/30 text-white font-semibold hover:bg-white/10 active:scale-[0.98] backdrop-blur-sm transition-[background-color,transform] duration-200">
              
              {t.hero.about}
              <ChevronRight className="h-4 w-4" />
            </a>
          </motion.div>

          <motion.div
            variants={item}
            className="mt-14 flex items-center gap-2"
            role="tablist"
            aria-label="Featured highlights">
            
            {[0, 1, 2, 3].map((i) => {
              const active = i === slide;
              return (
                <button
                  key={i}
                  role="tab"
                  aria-selected={active}
                  aria-label={`Highlight ${i + 1}`}
                  onClick={() => setSlide(i)}
                  className={`h-1.5 rounded-full transition-all duration-300 ${active ? 'w-10 bg-[#E51B2B]' : 'w-6 bg-white/40 hover:bg-white/70'}`} />);


            })}
          </motion.div>
        </motion.div>
      </div>
    </section>);

}
