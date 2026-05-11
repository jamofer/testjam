export function LiveIndicator({ connected, className = "" }) {
  if (!connected) return null
  return (
    <span
      data-testid="live-indicator"
      className={`inline-flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-emerald-700 ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
      live
    </span>
  )
}
