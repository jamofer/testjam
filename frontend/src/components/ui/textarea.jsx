import { cn } from "../../lib/utils"

export function Textarea({ className, ...props }) {
  return (
    <textarea
      className={cn(
        "flex min-h-20 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 dark:placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-400 dark:focus-visible:ring-gray-500 disabled:opacity-50 resize-y",
        className
      )}
      {...props}
    />
  )
}
