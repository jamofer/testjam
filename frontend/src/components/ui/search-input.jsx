import { forwardRef } from "react"
import { Search, X } from "lucide-react"
import { cn } from "../../lib/utils"

export const SearchInput = forwardRef(function SearchInput(
  { value, onChange, placeholder = "Search…", className, autoFocus, ...props },
  ref,
) {
  return (
    <div className={cn("relative", className)}>
      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none" />
      <input
        ref={ref}
        type="search"
        autoFocus={autoFocus}
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full h-9 pl-9 pr-9 text-sm border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-300"
        {...props}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 p-1"
          aria-label="Clear search"
        >
          <X size={13} />
        </button>
      )}
    </div>
  )
})
