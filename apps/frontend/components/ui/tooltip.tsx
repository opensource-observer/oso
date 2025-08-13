"use client";

import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const TooltipProvider = TooltipPrimitive.Provider;

const TooltipRoot = TooltipPrimitive.Root;

const TooltipTrigger = TooltipPrimitive.Trigger;

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Portal>
    <TooltipPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 overflow-hidden rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-tooltip-content-transform-origin)",
        className,
      )}
      {...props}
    />
  </TooltipPrimitive.Portal>
));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;

type ToolTipSide = "top" | "right" | "bottom" | "left";
type ToolTipProps = {
  className?: string; // Plasmic CSS class
  trigger?: React.ReactElement; // Show this
  content?: React.ReactElement; // Show this
  side?: ToolTipSide; // Position of the tooltip
};

const ToolTipMeta: CodeComponentMeta<ToolTipProps> = {
  name: "ToolTip",
  description: "shadcn/ui tooltip component",
  props: {
    trigger: "slot",
    content: "slot",
    side: {
      type: "choice",
      options: ["top", "right", "bottom", "left"],
    },
  },
};

function ToolTip(props: ToolTipProps) {
  const { className, trigger, content, side } = props;
  return (
    <TooltipRoot>
      <TooltipTrigger asChild>
        <div className={className}>{trigger}</div>
      </TooltipTrigger>
      <TooltipContent side={side}>{content}</TooltipContent>
    </TooltipRoot>
  );
}

export {
  TooltipRoot,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
  ToolTip,
  ToolTipMeta,
};
