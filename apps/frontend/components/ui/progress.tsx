"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  indicatorClassName?: string;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value, indicatorClassName, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      "relative h-2 w-full overflow-hidden rounded-full bg-primary/20",
      className,
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className={cn(
        "h-full w-full flex-1 bg-primary transition-all",
        indicatorClassName,
      )}
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

export const ProgressMeta: CodeComponentMeta<ProgressProps> = {
  name: "Progress",
  description: "shadcn/ui Progress component for displaying progress bars",
  props: {
    value: {
      type: "number",
      helpText: "Progress value (0-100)",
      defaultValueHint: 0,
    },
    max: {
      type: "number",
      helpText: "Maximum value",
      defaultValueHint: 100,
    },
    indicatorClassName: {
      type: "class",
      helpText: "Styles for the progress indicator bar",
    },
  },
};

export { Progress };
