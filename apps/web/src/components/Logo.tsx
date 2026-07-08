export function Logo({ className = "h-6 w-auto" }: { className?: string }) {
  // eslint-disable-next-line @next/next/no-img-element
  return <img src="/broono-logo.svg" alt="Broono" className={className} />;
}
