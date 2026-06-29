import React from 'react';
import { BookOpen, Users, Clock, Building2 } from 'lucide-react';
import { CONTAINER, Eyebrow, Reveal, RevealGroup, RevealItem } from './motion';
const STATS = [
{
  icon: BookOpen,
  value: '850+',
  label: 'Training Programs'
},
{
  icon: Users,
  value: '45,000+',
  label: 'Trainees Graduated'
},
{
  icon: Clock,
  value: '1.2M',
  label: 'Training Hours'
},
{
  icon: Building2,
  value: '120+',
  label: 'Partner Institutions'
}];

export function FactsFigures({ id = 'about' }: { id?: string }) {
  return (
    <section id={id} className="relative py-20 md:py-24 bg-[#081827] overflow-hidden scroll-mt-24">
      {/* Intentionally tighter than content sections — a dense punctuation band */}
      <div
        className="absolute inset-0 opacity-[0.08]"
        aria-hidden="true"
        style={{
          backgroundImage:
          'radial-gradient(circle at 20% 30%, #E51B2B 0%, transparent 40%), radial-gradient(circle at 80% 70%, #E51B2B 0%, transparent 35%)'
        }} />
      
      <div
        className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#E51B2B]/50 to-transparent"
        aria-hidden="true" />
      
      <div className={`relative ${CONTAINER}`}>
        <Reveal className="text-center mb-14">
          <Eyebrow className="mb-3">Facts &amp; Figures</Eyebrow>
          <h2
            className="text-white font-bold tracking-tight"
            style={{
              fontSize: 'clamp(1.75rem, 3vw, 2.5rem)'
            }}>
            
            A decade of measurable impact.
          </h2>
        </Reveal>

        <RevealGroup className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 rounded-2xl overflow-hidden border border-white/10">
          {STATS.map(({ icon: Icon, value, label }) =>
          <RevealItem
            key={label}
            className="bg-[#081827] px-6 py-10 text-center group hover:bg-[#0f2238] transition-colors duration-300">
            
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-[#E51B2B]/15 text-[#E51B2B] mb-5 group-hover:scale-110 transition-transform duration-300">
                <Icon className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <div
              className="text-white font-bold tracking-tight"
              style={{
                fontSize: 'clamp(2rem, 3.6vw, 3rem)'
              }}>
              
                {value}
              </div>
              <div className="mt-2 text-white/70 text-sm tracking-wide uppercase">
                {label}
              </div>
            </RevealItem>
          )}
        </RevealGroup>
      </div>
    </section>);

}
