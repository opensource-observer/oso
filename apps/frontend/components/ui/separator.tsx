"use client";

import * as React from "react";
import * as SeparatorPrimitive from "@radix-ui/react-separator";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root>
>(
  (
    { className, orientation = "horizontal", decorative = true, ...props },
    ref,
  ) => (
    <SeparatorPrimitive.Root
      ref={ref}
      decorative={decorative}
      orientation={orientation}
      className={cn(
        "shrink-0 bg-border",
        orientation === "horizontal" ? "h-px w-full" : "h-full w-px",
        className,
      )}
      {...props}
    />
  ),
);
Separator.displayName = SeparatorPrimitive.Root.displayName;

type SeparatorProps = React.ComponentPropsWithoutRef<
  typeof SeparatorPrimitive.Root
>;

export const SeparatorMeta: CodeComponentMeta<SeparatorProps> = {
  name: "Separator",
  description: "shadcn/ui Separator component for visual dividers",
  props: {
    orientation: {
      type: "choice",
      options: ["horizontal", "vertical"],
      defaultValue: "horizontal",
    },
    decorative: {
      type: "boolean",
      defaultValue: true,
      description: "Whether the separator is purely decorative",
    },
  },
};

export { Separator };
