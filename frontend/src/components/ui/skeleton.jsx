import { cn } from "../../lib/utils"

export function Skeleton({ className, ...props }) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading"
      className={cn("animate-pulse rounded-md bg-gray-200/70", className)}
      {...props}
    />
  )
}

export function SkeletonText({ lines = 3, className }) {
  return (
    <div className={cn("space-y-2", className)} role="status" aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-3 animate-pulse rounded bg-gray-200/70",
            i === lines - 1 ? "w-2/3" : "w-full"
          )}
        />
      ))}
    </div>
  )
}

export function SkeletonList({ count = 3, itemClassName, className }) {
  return (
    <div className={cn("space-y-2", className)} role="status" aria-busy="true" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn("h-16 animate-pulse rounded-xl border border-gray-100 bg-gray-50", itemClassName)}
        />
      ))}
    </div>
  )
}
