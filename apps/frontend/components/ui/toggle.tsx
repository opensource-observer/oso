"use client";

import * as React from "react";
import * as TogglePrimitive from "@radix-ui/react-toggle";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const toggleVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors hover:bg-muted hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-transparent",
        outline:
          "border border-input bg-transparent shadow-sm hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-9 px-2 min-w-9",
        sm: "h-8 px-1.5 min-w-8",
        lg: "h-10 px-2.5 min-w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

const Toggle = React.forwardRef<
  React.ElementRef<typeof TogglePrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root> &
    VariantProps<typeof toggleVariants>
>(({ className, variant, size, ...props }, ref) => (
  <TogglePrimitive.Root
    ref={ref}
    className={cn(toggleVariants({ variant, size, className }))}
    {...props}
  />
));

Toggle.displayName = TogglePrimitive.Root.displayName;

type ToggleProps = React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root> &
  VariantProps<typeof toggleVariants>;

export const ToggleMeta: CodeComponentMeta<ToggleProps> = {
  name: "Toggle",
  description: "shadcn/ui Toggle component",
  props: {
    children: "slot",
    defaultPressed: "boolean",
    onPressedChange: {
      type: "eventHandler",
      argTypes: [{ name: "pressed", type: "boolean" }],
    },
    disabled: "boolean",
    variant: {
      type: "choice",
      options: ["default", "outline"],
      defaultValue: "default",
    },
    size: {
      type: "choice",
      options: ["default", "sm", "lg"],
      defaultValue: "default",
    },
  },
  states: {
    pressed: {
      type: "readonly",
      variableType: "boolean",
      onChangeProp: "onPressedChange",
      onChangeArgsToValue: (pressed) => pressed,
    },
  },
};

export { Toggle, toggleVariants };
