export function LogoMark({ size = 28, className = "" }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} className={className} aria-hidden="true">
      <g>
        <rect x="6"  y="8"   width="18" height="18" rx="3.2" fill="#fda4af" transform="rotate(-14 15 17)"/>
        <rect x="7"  y="7.5" width="18" height="18" rx="3.2" fill="#f43f5e" transform="rotate(-2 16 16.5)"/>
        <rect x="8"  y="7"   width="18" height="18" rx="3.2" fill="#e11d48" transform="rotate(11 17 16)"/>
      </g>
      <path d="M13.7 16.6l3 3 6.6-7.4" stroke="#fff" strokeWidth="2.6"
        fill="none" strokeLinecap="round" strokeLinejoin="round"
        transform="rotate(11 17 16)" />
    </svg>
  )
}

export function Logo({ size = 28, className = "" }) {
  return (
    <span className={`flex items-center gap-2 ${className}`}>
      <LogoMark size={size} />
      <span className="text-xl font-bold tracking-tight text-primary-600">Testjam</span>
    </span>
  )
}
