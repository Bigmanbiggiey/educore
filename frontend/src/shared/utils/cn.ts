import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge conditional Tailwind classes without the last-writer-wins bugs of
 * plain string concatenation (e.g. `p-4 ${className}` silently keeps a
 * conflicting `p-2` a consumer passed in `className`, since `p-2`/`p-4`
 * are the same specificity to the browser and only ordering decides).
 * Every `shared/components` primitive should compose classes through this
 * rather than template-string concatenation.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
