import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/** Stable empty default: `data ?? EMPTY_LIST` keeps memo dependencies unchanged. */
export const EMPTY_LIST = Object.freeze([])
