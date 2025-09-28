"use client";

import * as React from "react";
import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const Select = SelectPrimitive.Root;

const SelectMeta: CodeComponentMeta<React.ComponentProps<typeof Select>> = {
  name: "Select",
  description: "shadcn/ui Select component",
  props: {
    children: "slot",
    defaultValue: "string",
    value: "string",
    onValueChange: {
      type: "eventHandler",
      argTypes: [{ name: "value", type: "string" }],
    },
    defaultOpen: "boolean",
    open: "boolean",
    onOpenChange: {
      type: "eventHandler",
      argTypes: [{ name: "open", type: "boolean" }],
    },
    name: "string",
    disabled: "boolean",
    required: "boolean",
  },
  states: {
    value: {
      type: "writable",
      valueProp: "value",
      variableType: "text",
      onChangeProp: "onValueChange",
    },
    open: {
      type: "writable",
      valueProp: "open",
      variableType: "boolean",
      onChangeProp: "onOpenChange",
    },
  },
};

const SelectGroup = SelectPrimitive.Group;

const SelectGroupMeta: CodeComponentMeta<
  React.ComponentProps<typeof SelectGroup>
> = {
  name: "SelectGroup",
  description: "shadcn/ui SelectGroup component",
  props: {
    children: "slot",
  },
};

const SelectValue = SelectPrimitive.Value;

const SelectValueMeta: CodeComponentMeta<
  React.ComponentProps<typeof SelectValue>
> = {
  name: "SelectValue",
  description: "shadcn/ui SelectValue component",
  props: {
    placeholder: "string",
  },
};

type SelectTriggerProps = React.ComponentPropsWithoutRef<
  typeof SelectPrimitive.Trigger
>;

const SelectTriggerMeta: CodeComponentMeta<SelectTriggerProps> = {
  name: "SelectTrigger",
  description: "shadcn/ui SelectTrigger component",
  props: {
    children: "slot",
  },
};

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  SelectTriggerProps
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex h-9 w-full items-center justify-between whitespace-nowrap rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs ring-offset-background data-placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1",
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
));
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName;

const SelectScrollUpButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn(
      "flex cursor-default items-center justify-center py-1",
      className,
    )}
    {...props}
  >
    <ChevronUp className="h-4 w-4" />
  </SelectPrimitive.ScrollUpButton>
));
SelectScrollUpButton.displayName = SelectPrimitive.ScrollUpButton.displayName;

const SelectScrollDownButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn(
      "flex cursor-default items-center justify-center py-1",
      className,
    )}
    {...props}
  >
    <ChevronDown className="h-4 w-4" />
  </SelectPrimitive.ScrollDownButton>
));
SelectScrollDownButton.displayName =
  SelectPrimitive.ScrollDownButton.displayName;

type SelectContentProps = React.ComponentPropsWithoutRef<
  typeof SelectPrimitive.Content
> & {
  usePortal?: boolean;
};

const SelectContentMeta: CodeComponentMeta<SelectContentProps> = {
  name: "SelectContent",
  description: "shadcn/ui SelectContent component",
  props: {
    children: "slot",
    side: {
      type: "choice",
      options: ["top", "right", "bottom", "left"],
    },
    sideOffset: "number",
    align: {
      type: "choice",
      options: ["start", "center", "end"],
    },
    alignOffset: "number",
    sticky: {
      type: "choice",
      options: ["partial", "always"],
    },
  },
};

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  SelectContentProps
>(
  (
    { className, children, position = "popper", usePortal = true, ...props },
    ref,
  ) => {
    const Wrapper = usePortal ? SelectPrimitive.Portal : React.Fragment;
    return (
      <Wrapper>
        <SelectPrimitive.Content
          ref={ref}
          className={cn(
            "relative z-50 max-h-(--radix-select-content-available-height) min-w-32 overflow-y-auto overflow-x-hidden rounded-md border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-select-content-transform-origin)",
            position === "popper" &&
              "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
            className,
          )}
          position={position}
          {...props}
        >
          <SelectScrollUpButton />
          <SelectPrimitive.Viewport
            className={cn(
              "p-1",
              position === "popper" &&
                "h-(--radix-select-trigger-height) w-full min-w-(--radix-select-trigger-width)",
            )}
          >
            {children}
          </SelectPrimitive.Viewport>
          <SelectScrollDownButton />
        </SelectPrimitive.Content>
      </Wrapper>
    );
  },
);
SelectContent.displayName = SelectPrimitive.Content.displayName;

type SelectLabelProps = React.ComponentPropsWithoutRef<
  typeof SelectPrimitive.Label
>;

const SelectLabelMeta: CodeComponentMeta<SelectLabelProps> = {
  name: "SelectLabel",
  description: "shadcn/ui SelectLabel component",
  props: {
    children: "slot",
  },
};

const SelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  SelectLabelProps
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn("px-2 py-1.5 text-sm font-semibold", className)}
    {...props}
  />
));
SelectLabel.displayName = SelectPrimitive.Label.displayName;

type SelectItemProps = React.ComponentPropsWithoutRef<
  typeof SelectPrimitive.Item
>;

const SelectItemMeta: CodeComponentMeta<SelectItemProps> = {
  name: "SelectItem",
  description: "shadcn/ui SelectItem component",
  props: {
    children: "slot",
    value: {
      type: "string",
      required: true,
    },
    disabled: "boolean",
  },
};

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  SelectItemProps
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-2 pr-8 text-sm outline-hidden focus:bg-accent focus:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50",
      className,
    )}
    {...props}
  >
    <span className="absolute right-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
SelectItem.displayName = SelectPrimitive.Item.displayName;

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-muted", className)}
    {...props}
  />
));
SelectSeparator.displayName = SelectPrimitive.Separator.displayName;

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
  // Meta
  SelectMeta,
  SelectGroupMeta,
  SelectValueMeta,
  SelectTriggerMeta,
  SelectContentMeta,
  SelectLabelMeta,
  SelectItemMeta,
};
