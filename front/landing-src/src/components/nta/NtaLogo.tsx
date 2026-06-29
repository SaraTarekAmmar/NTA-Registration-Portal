import React from 'react';
type Props = {
  className?: string;
};
/**
 * Official National Training Academy logo.
 */
export function NtaLogo({ className = 'h-8' }: Props) {
  return (
    <img
      src="/nta-logo.png"
      alt="National Training Academy"
      className={`${className} w-auto max-w-[200px] object-contain`} />);


}