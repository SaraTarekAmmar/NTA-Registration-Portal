import React from 'react';
import { ArrowRight, Calendar } from 'lucide-react';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import {
  CONTAINER,
  SECTION,
  Eyebrow,
  Reveal,
  RevealGroup,
  RevealItem,
} from './motion';
import { useLang } from '../../i18n';

export function News({ id = 'news' }: { id?: string }) {
  const { t } = useLang();
  const imgs = [
    'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=900&q=80&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=900&q=80&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=900&q=80&auto=format&fit=crop',
  ];
  const items = t.news.items.map((item, index) => ({
    ...item,
    img: imgs[index],
  }));

  return (
    <section id={id} className={`${SECTION} bg-[#F6F7F9] scroll-mt-24`}>
      <div className={CONTAINER}>
        <Reveal className="flex items-end justify-between mb-12 flex-wrap gap-4">
          <div className="max-w-xl">
            <Eyebrow className="mb-4">{t.news.eyebrow}</Eyebrow>
            <h2
              className="text-[#081827] font-bold tracking-tight"
              style={{
                fontSize: 'clamp(2rem, 3.4vw, 2.875rem)',
                lineHeight: 1.1,
              }}
            >
              {t.news.heading}
            </h2>
          </div>
          <a
            href="#news"
            className="group inline-flex items-center gap-2 text-[#E51B2B] text-sm font-semibold"
          >
            {t.news.allNews}
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </a>
        </Reveal>

        <RevealGroup className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {items.map((n) => (
            <RevealItem
              key={n.title}
              as="article"
              className="group bg-white rounded-2xl overflow-hidden border border-gray-200 hover:shadow-lg hover:shadow-gray-900/5 hover:-translate-y-1 transition-[transform,box-shadow] duration-300"
            >
              <div className="relative aspect-[16/10] overflow-hidden">
                <ImageWithFallback
                  src={n.img}
                  alt={n.title}
                  className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.04]"
                />

                <span className="absolute top-4 left-4 inline-flex items-center px-2.5 py-1 rounded-full bg-white/95 text-[#E51B2B] text-[11px] font-semibold tracking-wider uppercase">
                  {n.category}
                </span>
              </div>
              <div className="p-6">
                <div className="flex items-center gap-2 text-[#081827]/60 text-xs mb-3">
                  <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                  <time>{n.date}</time>
                </div>
                <h3 className="text-[#081827] mb-3 text-[1.15rem] font-semibold leading-snug group-hover:text-[#E51B2B] transition-colors duration-200">
                  {n.title}
                </h3>
                <p className="text-[#081827]/70 text-[15px] leading-relaxed">
                  {n.excerpt}
                </p>
                <a
                  href="#news"
                  className="mt-5 inline-flex items-center gap-1.5 text-[#E51B2B] text-sm font-semibold group/link"
                >
                  {t.news.readMore}
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover/link:translate-x-0.5" />
                </a>
              </div>
            </RevealItem>
          ))}
        </RevealGroup>
      </div>
    </section>
  );
}
