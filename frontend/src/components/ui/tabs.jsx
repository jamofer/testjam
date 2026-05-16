import * as TabsPrimitive from "@radix-ui/react-tabs"
import { cn } from "../../lib/utils"

export const Tabs = TabsPrimitive.Root

export function TabsList({ className, ...props }) {
  return (
    <TabsPrimitive.List
      className={cn("inline-flex h-9 items-center rounded-lg bg-gray-100 dark:bg-gray-800 p-1 text-gray-500 dark:text-gray-400", className)}
      {...props}
    />
  )
}

export function TabsTrigger({ className, ...props }) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "inline-flex items-center justify-center rounded-md px-3 py-1 text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-900 data-[state=active]:text-gray-900 dark:data-[state=active]:text-gray-100 data-[state=active]:shadow",
        className
      )}
      {...props}
    />
  )
}

export function TabsContent({ className, ...props }) {
  return <TabsPrimitive.Content className={cn("mt-4 focus-visible:outline-none", className)} {...props} />
}
