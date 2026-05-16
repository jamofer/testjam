import { forwardRef } from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary-600 text-white hover:bg-primary-700",
        destructive: "bg-red-700 text-white hover:bg-red-800",
        outline: "border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-800",
        ghost: "text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800",
        link: "text-primary-600 dark:text-primary-400 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-10 px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)

export const Button = forwardRef(function Button(
  { className, variant, size, asChild = false, loading = false, disabled, children, ...props },
  ref,
) {
  if (asChild) {
    return (
      <Slot ref={ref} className={cn(buttonVariants({ variant, size, className }))} disabled={disabled} {...props}>
        {children}
      </Slot>
    )
  }
  return (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 size={14} className="animate-spin" />}
      {children}
    </button>
  )
})
