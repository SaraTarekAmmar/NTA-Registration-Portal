import React, { Children } from 'react';
import { motion, useReducedMotion, type Variants } from 'framer-motion';
/* ------------------------------------------------------------------ *
 * Shared design tokens — keep the system small and intentional.
 * ------------------------------------------------------------------ */
/** Consistent outer container for every section. */
export const CONTAINER = 'max-w-[1200px] mx-auto px-6 md:px-8';
/** Standard vertical rhythm for content sections. */
export const SECTION = 'py-24 md:py-32';
/** Easing used across the whole site (calm, institution-grade). */
const EASE = [0.22, 1, 0.36, 1] as const;
/* ------------------------------------------------------------------ *
 * Eyebrow — the uppercase red kicker, identical everywhere.
 * ------------------------------------------------------------------ */
export function Eyebrow({
  children,
  className = ''



}: {children: React.ReactNode;className?: string;}) {
  return (
    <span
      className={`block text-[#E51B2B] text-xs font-semibold uppercase tracking-[0.18em] ${className}`}>
      
      {children}
    </span>);

}
/* ------------------------------------------------------------------ *
 * Reveal — a single fade-up-on-scroll element.
 * Respects prefers-reduced-motion (fades only, no travel).
 * ------------------------------------------------------------------ */
export function Reveal({
  children,
  className = '',
  delay = 0,
  as = 'div'





}: {children: React.ReactNode;className?: string;delay?: number;as?: 'div' | 'section' | 'article' | 'span';}) {
  const reduce = useReducedMotion();
  const MotionTag = motion[as] as typeof motion.div;
  return (
    <MotionTag
      className={className}
      initial={{
        opacity: 0,
        y: reduce ? 0 : 16
      }}
      whileInView={{
        opacity: 1,
        y: 0
      }}
      viewport={{
        once: true,
        margin: '-80px'
      }}
      transition={{
        duration: 0.5,
        ease: EASE,
        delay
      }}>
      
      {children}
    </MotionTag>);

}
/* ------------------------------------------------------------------ *
 * RevealGroup / RevealItem — staggered reveals for card grids.
 * ------------------------------------------------------------------ */
export function RevealGroup({
  children,
  className = '',
  stagger = 0.06




}: {children: React.ReactNode;className?: string;stagger?: number;}) {
  const container: Variants = {
    hidden: {},
    show: {
      transition: {
        staggerChildren: stagger
      }
    }
  };
  return (
    <motion.div
      className={className}
      variants={container}
      initial="hidden"
      whileInView="show"
      viewport={{
        once: true,
        margin: '-60px'
      }}>
      
      {children}
    </motion.div>);

}
export function RevealItem({
  children,
  className = '',
  as = 'div'




}: {children: React.ReactNode;className?: string;as?: 'div' | 'article';}) {
  const reduce = useReducedMotion();
  const MotionTag = motion[as] as typeof motion.div;
  const item: Variants = {
    hidden: {
      opacity: 0,
      y: reduce ? 0 : 18
    },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: EASE
      }
    }
  };
  return (
    <MotionTag className={className} variants={item}>
      {children}
    </MotionTag>);

}