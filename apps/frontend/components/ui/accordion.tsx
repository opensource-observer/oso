"use client";

import * as React from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const Accordion = AccordionPrimitive.Root;

const AccordionItem = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item>
>(({ className, ...props }, ref) => (
  <AccordionPrimitive.Item
    ref={ref}
    className={cn("border-b", className)}
    {...props}
  />
));
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      ref={ref}
      className={cn(
        "flex flex-1 items-center justify-between py-4 text-sm font-medium transition-all hover:underline text-left [&[data-state=open]>svg]:rotate-180",
        className,
      )}
      {...props}
    >
      {children}
      <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200" />
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
));
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Content
    ref={ref}
    className="overflow-hidden text-sm data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
    {...props}
  >
    <div className={cn("pb-4 pt-0", className)}>{children}</div>
  </AccordionPrimitive.Content>
));
AccordionContent.displayName = AccordionPrimitive.Content.displayName;

type AccordionProps = React.ComponentProps<typeof Accordion>;
export const AccordionMeta: CodeComponentMeta<AccordionProps> = {
  name: "Accordion",
  description: "shadcn/ui Accordion component for collapsible sections",
  props: {
    children: "slot",
    type: {
      type: "choice",
      options: ["single", "multiple"],
      defaultValueHint: "single",
      helpText: "Whether the accordion should be single or multiple",
    },
    collapsible: {
      type: "boolean",
      defaultValueHint: false,
      helpText: "Whether the accordion should be collapsible",
    },
    defaultValue: "string",
    value: "string",
    onValueChange: {
      type: "eventHandler",
      argTypes: [{ name: "value", type: "string" }],
    },
    disabled: {
      type: "boolean",
      defaultValueHint: false,
      helpText: "Whether the accordion should be disabled",
    },
    orientation: {
      type: "choice",
      options: ["horizontal", "vertical"],
      defaultValueHint: "vertical",
      helpText: "The orientation of the accordion",
    },
    dir: {
      type: "choice",
      options: ["ltr", "rtl"],
      defaultValueHint: "ltr",
      helpText: "The direction that the accordion should read",
    },
  },
};

type AccordionItemProps = React.ComponentPropsWithoutRef<
  typeof AccordionPrimitive.Item
>;
export const AccordionItemMeta: CodeComponentMeta<AccordionItemProps> = {
  name: "AccordionItem",
  description: "Individual item in an Accordion",
  props: {
    children: "slot",
    value: {
      type: "string",
      description: "Unique value for this accordion item",
    },
    disabled: "boolean",
  },
};

type AccordionTriggerProps = React.ComponentPropsWithoutRef<
  typeof AccordionPrimitive.Trigger
>;
export const AccordionTriggerMeta: CodeComponentMeta<AccordionTriggerProps> = {
  name: "AccordionTrigger",
  description: "Trigger button for an accordion item",
  props: {
    children: "slot",
  },
};

type AccordionContentProps = React.ComponentPropsWithoutRef<
  typeof AccordionPrimitive.Content
>;
export const AccordionContentMeta: CodeComponentMeta<AccordionContentProps> = {
  name: "AccordionContent",
  description: "Content area for an accordion item",
  props: {
    children: "slot",
  },
};

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
