import React from 'react';
import { Play } from 'lucide-react';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import {
  CONTAINER,
  SECTION,
  Eyebrow,
  Reveal,
  RevealGroup,
  RevealItem } from
'./motion';
const FEATURED = {
  src: 'https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=1400&q=80&auto=format&fit=crop',
  label: 'Featured',
  title: 'Presidential Leadership Program: 2026 Cohort Closing Ceremony',
  duration: '4:32'
};
const SECONDARY = [
{
  src: 'https://images.unsplash.com/photo-1559223607-a43c990c692c?w=800&q=80&auto=format&fit=crop',
  label: 'Event',
  title: 'NTA Summit on Public Sector Innovation',
  duration: '2:18'
},
{
  src: 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800&q=80&auto=format&fit=crop',
  label: 'Story',
  title: 'Future Leaders: Voices of the Next Generation',
  duration: '3:05'
}];

function PlayBadge({ size = 'lg' }: {size?: 'lg' | 'sm';}) {
  return (
    <div
      aria-hidden="true"
      className={`${size === 'lg' ? 'h-16 w-16' : 'h-11 w-11'} rounded-full bg-white/95 grid place-items-center shadow-2xl group-hover:bg-[#E51B2B] group-hover:scale-110 transition-[background-color,transform] duration-300`}>
      
      <Play
        className={`${size === 'lg' ? 'h-6 w-6 ml-1' : 'h-4 w-4 ml-0.5'} text-[#E51B2B] group-hover:text-white fill-current`} />
      
    </div>);

}
export function Moments({ id = 'community' }: { id?: string }) {
  return (
    <section id={id} className={`${SECTION} bg-[#F6F7F9] scroll-mt-24`}>
      <div className={CONTAINER}>
        <Reveal className="flex items-end justify-between mb-12 flex-wrap gap-4">
          <div className="max-w-xl">
            <Eyebrow className="mb-4">NTA Moments</Eyebrow>
            <h2
              className="text-[#081827] font-bold tracking-tight"
              style={{
                fontSize: 'clamp(2rem, 3.4vw, 2.875rem)',
                lineHeight: 1.1
              }}>
              
              Inside the Academy.
            </h2>
          </div>
          <a
            href="#contact"
            className="group inline-flex items-center gap-1.5 text-[#E51B2B] text-sm font-semibold">
            
            View all videos
            <span className="transition-transform duration-200 group-hover:translate-x-0.5">
              →
            </span>
          </a>
        </Reveal>

        <RevealGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RevealItem className="lg:col-span-2">
            <button
              type="button"
              className="group relative block w-full rounded-2xl overflow-hidden text-left aspect-[16/10] lg:h-full">
              
              <ImageWithFallback
                src={FEATURED.src}
                alt={FEATURED.title}
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.04]" />
              
              <div className="absolute inset-0 bg-gradient-to-t from-[#081827]/90 via-[#081827]/20 to-transparent" />
              <div className="absolute inset-0 grid place-items-center">
                <PlayBadge />
              </div>
              <div className="absolute bottom-0 left-0 right-0 p-7">
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#E51B2B] text-white text-[11px] font-semibold tracking-wider uppercase mb-3">
                  {FEATURED.label}
                </span>
                <h3 className="text-white max-w-xl text-2xl font-semibold leading-snug">
                  {FEATURED.title}
                </h3>
                <div className="mt-2 text-white/75 text-sm">
                  {FEATURED.duration}
                </div>
              </div>
            </button>
          </RevealItem>

          <RevealItem className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-6">
            {SECONDARY.map((v) =>
            <button
              key={v.title}
              type="button"
              className="group relative block w-full rounded-2xl overflow-hidden text-left aspect-[16/10] lg:aspect-[16/11]">
              
                <ImageWithFallback
                src={v.src}
                alt={v.title}
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.04]" />
              
                <div className="absolute inset-0 bg-gradient-to-t from-[#081827]/90 via-[#081827]/10 to-transparent" />
                <div className="absolute inset-0 grid place-items-center">
                  <PlayBadge size="sm" />
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-white/20 backdrop-blur text-white text-[10px] font-semibold tracking-wider uppercase mb-2">
                    {v.label}
                  </span>
                  <h3 className="text-white text-base font-semibold leading-snug">
                    {v.title}
                  </h3>
                </div>
              </button>
            )}
          </RevealItem>
        </RevealGroup>
      </div>
    </section>);

}
