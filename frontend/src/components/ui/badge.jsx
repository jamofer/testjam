import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900",
        secondary: "border-transparent bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200",
        destructive: "border-transparent bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300",
        success: "border-transparent bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300",
        warning: "border-transparent bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300",
        outline: "text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-700",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

export function Badge({ className, variant, ...props }) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
