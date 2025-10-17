"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const Popover = PopoverPrimitive.Root;

const PopoverTrigger = PopoverPrimitive.Trigger;

const PopoverAnchor = PopoverPrimitive.Anchor;

const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "center", sideOffset = 4, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      className={cn(
        "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-[--radix-popover-content-transform-origin]",
        className,
      )}
      {...props}
    />
  </PopoverPrimitive.Portal>
));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;

type PopoverProps = React.ComponentProps<typeof PopoverPrimitive.Root>;
type PopoverTriggerProps = React.ComponentProps<
  typeof PopoverPrimitive.Trigger
>;
type PopoverContentProps = React.ComponentPropsWithoutRef<
  typeof PopoverPrimitive.Content
>;
type PopoverAnchorProps = React.ComponentProps<typeof PopoverPrimitive.Anchor>;

export const PopoverMeta: CodeComponentMeta<PopoverProps> = {
  name: "Popover",
  description: "Root popover container component",
  props: {
    children: "slot",
    open: "boolean",
    onOpenChange: {
      type: "eventHandler",
      argTypes: [{ name: "open", type: "boolean" }],
    },
    defaultOpen: "boolean",
  },
};

export const PopoverTriggerMeta: CodeComponentMeta<PopoverTriggerProps> = {
  name: "PopoverTrigger",
  description: "Button that triggers the popover",
  props: {
    children: "slot",
    asChild: {
      type: "boolean",
      description: "Merge props with child element instead of wrapping",
    },
  },
};

export const PopoverContentMeta: CodeComponentMeta<PopoverContentProps> = {
  name: "PopoverContent",
  description: "Container for popover content",
  props: {
    children: "slot",
    align: {
      type: "choice",
      options: ["start", "center", "end"],
      defaultValue: "center",
    },
    side: {
      type: "choice",
      options: ["top", "right", "bottom", "left"],
    },
    sideOffset: {
      type: "number",
      defaultValue: 4,
    },
  },
};

export const PopoverAnchorMeta: CodeComponentMeta<PopoverAnchorProps> = {
  name: "PopoverAnchor",
  description: "Anchor element for popover positioning",
  props: {
    children: "slot",
    asChild: {
      type: "boolean",
      description: "Merge props with child element instead of wrapping",
    },
  },
};

export { Popover, PopoverTrigger, PopoverContent, PopoverAnchor };
