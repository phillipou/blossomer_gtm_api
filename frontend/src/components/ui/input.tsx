import * as React from "react"

import { cn } from "../../lib/utils"

/**
 * Input component - a styled input primitive using shadcn/ui conventions.
 *
 * @example
 * <Input type="email" placeholder="Enter your email" />
 *
 * @remarks
 * To add a new style, extend the className or wrap with composition.
 *
 * @see https://ui.shadcn.com/docs/components/input
 */
const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
