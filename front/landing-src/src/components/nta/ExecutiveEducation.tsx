import React from 'react';
import {
  Crown,
  GraduationCap,
  Rocket,
  Scale,
  Cpu,
  Compass,
  ArrowRight } from
'lucide-react';
import {
  CONTAINER,
  SECTION,
  Eyebrow,
  Reveal,
  RevealGroup,
  RevealItem } from
'./motion';
import { useLang } from '../../i18n';
const PROGRAMS = [
{
  icon: Crown,
  title: 'Presidential Leadership Program',
  desc: "An elite program shaping Egypt's most senior public-sector leaders through immersive strategic learning."
},
{
  icon: GraduationCap,
  title: 'Executive Education',
  desc: 'Advanced programs designed for executives ready to drive organizational transformation at scale.'
},
{
  icon: Rocket,
  title: 'Future Leaders',
  desc: "Cultivating ambitious young professionals with the vision and tools to lead Egypt's next chapter."
},
{
  icon: Scale,
  title: 'Public Policy',
  desc: 'Evidence-based policy training that equips officials to design and implement effective national initiatives.'
},
{
  icon: Cpu,
  title: 'Digital Transformation',
  desc: 'Building digital fluency and innovation mindset across government and public services.'
},
{
  icon: Compass,
  title: 'Strategic Management',
  desc: 'Equipping leaders with frameworks to navigate complexity, ambiguity, and long-term strategy.'
}];

export function ExecutiveEducation({ id = 'programs' }: { id?: string }) {
  const { t } = useLang();
  return (
    <section id={id} className={`${SECTION} bg-white scroll-mt-24`}>
      <div className={CONTAINER}>
        <Reveal className="max-w-2xl mb-14">
          <Eyebrow className="mb-4">{t.programs.eyebrow}</Eyebrow>
          <h2
            className="text-[#081827] font-bold tracking-tight text-balance"
            style={{
              fontSize: 'clamp(2rem, 3.4vw, 2.875rem)',
              lineHeight: 1.1
            }}>

            {t.programs.heading}
          </h2>
          <p className="mt-5 text-[#081827]/70 text-lg leading-relaxed max-w-[60ch]">
            {t.programs.intro}
          </p>
        </Reveal>

        <RevealGroup className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {PROGRAMS.map(({ icon: Icon }, i) =>
          <RevealItem
            key={i}
            as="article"
            className="group relative bg-white rounded-2xl border border-gray-200 p-7 transition-[transform,box-shadow] duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-gray-900/5 overflow-hidden">
            
              <span className="absolute top-0 left-0 right-0 h-[3px] bg-[#E51B2B] scale-x-0 group-hover:scale-x-100 origin-left transition-transform duration-300" />

              <div className="h-12 w-12 rounded-xl bg-[#E51B2B]/10 text-[#E51B2B] grid place-items-center mb-5 group-hover:bg-[#E51B2B] group-hover:text-white transition-colors duration-300">
                <Icon className="h-6 w-6" strokeWidth={1.75} />
              </div>

              <h3 className="text-[#081827] mb-3 text-xl font-semibold leading-snug">
                {t.programs.items[i].title}
              </h3>
              <p className="text-[#081827]/70 leading-relaxed text-[15px]">
                {t.programs.items[i].desc}
              </p>

              <a
              href="#contact"
              className="mt-6 inline-flex items-center gap-1.5 text-[#E51B2B] text-sm font-semibold group/link">

                {t.programs.learnMore}
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover/link:translate-x-0.5" />
              </a>
            </RevealItem>
          )}
        </RevealGroup>
      </div>
    </section>);

}
