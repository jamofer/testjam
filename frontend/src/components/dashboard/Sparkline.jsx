const WIDTH = 240
const HEIGHT = 48
const PADDING = 4

export function Sparkline({ points }) {
  if (!points.length) {
    return <p className="text-xs text-gray-400 dark:text-gray-500">No data in this window.</p>
  }
  const max = Math.max(...points, 1)
  const stepX = points.length === 1
    ? 0
    : (WIDTH - PADDING * 2) / (points.length - 1)
  const coords = points.map((value, index) => {
    const x = PADDING + stepX * index
    const y = HEIGHT - PADDING - (value / max) * (HEIGHT - PADDING * 2)
    return [x, y]
  })
  const path = coords
    .map(([x, y], index) => (index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`))
    .join(' ')

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="none"
      className="w-full h-12"
      role="img"
      aria-label="Pass rate trend"
    >
      <path d={path} fill="none" stroke="currentColor" strokeWidth="1.5" className="text-primary-500" />
      {coords.map(([x, y], index) => (
        <circle key={index} cx={x} cy={y} r="1.5" className="fill-primary-500" />
      ))}
    </svg>
  )
}
