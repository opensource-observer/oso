"use client";

import * as React from "react";
import * as ContextMenuPrimitive from "@radix-ui/react-context-menu";
import { Check, ChevronRight, Circle } from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { cn } from "@/lib/utils";

const ContextMenu = ContextMenuPrimitive.Root;

export const ContextMenuMeta: CodeComponentMeta<
  React.ComponentProps<typeof ContextMenu>
> = {
  name: "ContextMenu",
  description: "shadcn/ui ContextMenu component",
  props: {
    children: "slot",
  },
};

const ContextMenuTrigger = ContextMenuPrimitive.Trigger;

export const ContextMenuTriggerMeta: CodeComponentMeta<
  React.ComponentProps<typeof ContextMenuTrigger>
> = {
  name: "ContextMenuTrigger",
  description: "shadcn/ui ContextMenuTrigger component",
  props: {
    children: "slot",
  },
};

const ContextMenuGroup = ContextMenuPrimitive.Group;

export const ContextMenuGroupMeta: CodeComponentMeta<
  React.ComponentProps<typeof ContextMenuGroup>
> = {
  name: "ContextMenuGroup",
  description: "shadcn/ui ContextMenuGroup component",
  props: {
    children: "slot",
  },
};

const ContextMenuPortal = ContextMenuPrimitive.Portal;

const ContextMenuSub = ContextMenuPrimitive.Sub;

export const ContextMenuSubMeta: CodeComponentMeta<
  React.ComponentProps<typeof ContextMenuSub>
> = {
  name: "ContextMenuSub",
  description: "shadcn/ui ContextMenuSub component",
  props: {
    children: "slot",
  },
};

const ContextMenuRadioGroup = ContextMenuPrimitive.RadioGroup;

export const ContextMenuRadioGroupMeta: CodeComponentMeta<
  React.ComponentProps<typeof ContextMenuRadioGroup>
> = {
  name: "ContextMenuRadioGroup",
  description: "shadcn/ui ContextMenuRadioGroup component",
  props: {
    children: "slot",
    value: "string",
  },
};

type ContextMenuSubTriggerProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.SubTrigger
> & {
  inset?: boolean;
};

export const ContextMenuSubTriggerMeta: CodeComponentMeta<ContextMenuSubTriggerProps> =
  {
    name: "ContextMenuSubTrigger",
    description: "shadcn/ui ContextMenuSubTrigger component",
    props: {
      children: "slot",
      inset: "boolean",
    },
  };

const ContextMenuSubTrigger = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.SubTrigger>,
  ContextMenuSubTriggerProps
>(({ className, inset, children, ...props }, ref) => (
  <ContextMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[state=open]:bg-accent data-[state=open]:text-accent-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="ml-auto h-4 w-4" />
  </ContextMenuPrimitive.SubTrigger>
));
ContextMenuSubTrigger.displayName = ContextMenuPrimitive.SubTrigger.displayName;

type ContextMenuSubContentProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.SubContent
>;

export const ContextMenuSubContentMeta: CodeComponentMeta<ContextMenuSubContentProps> =
  {
    name: "ContextMenuSubContent",
    description: "shadcn/ui ContextMenuSubContent component",
    props: {
      children: "slot",
    },
  };

const ContextMenuSubContent = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.SubContent>,
  ContextMenuSubContentProps
>(({ className, ...props }, ref) => (
  <ContextMenuPrimitive.SubContent
    ref={ref}
    className={cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-[--radix-context-menu-content-transform-origin]",
      className,
    )}
    {...props}
  />
));
ContextMenuSubContent.displayName = ContextMenuPrimitive.SubContent.displayName;

type ContextMenuContentProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.Content
>;

export const ContextMenuContentMeta: CodeComponentMeta<ContextMenuContentProps> =
  {
    name: "ContextMenuContent",
    description: "shadcn/ui ContextMenuContent component",
    props: {
      children: "slot",
    },
  };

const ContextMenuContent = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Content>,
  ContextMenuContentProps
>(({ className, ...props }, ref) => (
  <ContextMenuPrimitive.Portal>
    <ContextMenuPrimitive.Content
      ref={ref}
      className={cn(
        "z-50 max-h-[--radix-context-menu-content-available-height] min-w-[8rem] overflow-y-auto overflow-x-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-[--radix-context-menu-content-transform-origin]",
        className,
      )}
      {...props}
    />
  </ContextMenuPrimitive.Portal>
));
ContextMenuContent.displayName = ContextMenuPrimitive.Content.displayName;

type ContextMenuItemProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.Item
> & {
  inset?: boolean;
};

export const ContextMenuItemMeta: CodeComponentMeta<ContextMenuItemProps> = {
  name: "ContextMenuItem",
  description: "shadcn/ui ContextMenuItem component",
  props: {
    children: "slot",
    inset: "boolean",
  },
};

const ContextMenuItem = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Item>,
  ContextMenuItemProps
>(({ className, inset, ...props }, ref) => (
  <ContextMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
ContextMenuItem.displayName = ContextMenuPrimitive.Item.displayName;

type ContextMenuCheckboxItemProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.CheckboxItem
>;

export const ContextMenuCheckboxItemMeta: CodeComponentMeta<ContextMenuCheckboxItemProps> =
  {
    name: "ContextMenuCheckboxItem",
    description: "shadcn/ui ContextMenuCheckboxItem component",
    props: {
      children: "slot",
      checked: "boolean",
    },
  };

const ContextMenuCheckboxItem = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.CheckboxItem>,
  ContextMenuCheckboxItemProps
>(({ className, children, checked, ...props }, ref) => (
  <ContextMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <ContextMenuPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </ContextMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </ContextMenuPrimitive.CheckboxItem>
));
ContextMenuCheckboxItem.displayName =
  ContextMenuPrimitive.CheckboxItem.displayName;

type ContextMenuRadioItemProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.RadioItem
>;

export const ContextMenuRadioItemMeta: CodeComponentMeta<ContextMenuRadioItemProps> =
  {
    name: "ContextMenuRadioItem",
    description: "shadcn/ui ContextMenuRadioItem component",
    props: {
      children: "slot",
      value: "string",
    },
  };

const ContextMenuRadioItem = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.RadioItem>,
  ContextMenuRadioItemProps
>(({ className, children, ...props }, ref) => (
  <ContextMenuPrimitive.RadioItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <ContextMenuPrimitive.ItemIndicator>
        <Circle className="h-4 w-4 fill-current" />
      </ContextMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </ContextMenuPrimitive.RadioItem>
));
ContextMenuRadioItem.displayName = ContextMenuPrimitive.RadioItem.displayName;

type ContextMenuLabelProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.Label
> & {
  inset?: boolean;
};

export const ContextMenuLabelMeta: CodeComponentMeta<ContextMenuLabelProps> = {
  name: "ContextMenuLabel",
  description: "shadcn/ui ContextMenuLabel component",
  props: {
    children: "slot",
    inset: "boolean",
  },
};

const ContextMenuLabel = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Label>,
  ContextMenuLabelProps
>(({ className, inset, ...props }, ref) => (
  <ContextMenuPrimitive.Label
    ref={ref}
    className={cn(
      "px-2 py-1.5 text-sm font-semibold text-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
ContextMenuLabel.displayName = ContextMenuPrimitive.Label.displayName;

type ContextMenuSeparatorProps = React.ComponentPropsWithoutRef<
  typeof ContextMenuPrimitive.Separator
>;

export const ContextMenuSeparatorMeta: CodeComponentMeta<ContextMenuSeparatorProps> =
  {
    name: "ContextMenuSeparator",
    description: "shadcn/ui ContextMenuSeparator component",
    props: {},
  };

const ContextMenuSeparator = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Separator>,
  ContextMenuSeparatorProps
>(({ className, ...props }, ref) => (
  <ContextMenuPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-border", className)}
    {...props}
  />
));
ContextMenuSeparator.displayName = ContextMenuPrimitive.Separator.displayName;

type ContextMenuShortcutProps = React.HTMLAttributes<HTMLSpanElement>;

export const ContextMenuShortcutMeta: CodeComponentMeta<ContextMenuShortcutProps> =
  {
    name: "ContextMenuShortcut",
    description: "shadcn/ui ContextMenuShortcut component",
    props: {
      children: "slot",
    },
  };

const ContextMenuShortcut = ({
  className,
  ...props
}: ContextMenuShortcutProps) => {
  return (
    <span
      className={cn(
        "ml-auto text-xs tracking-widest text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
};
ContextMenuShortcut.displayName = "ContextMenuShortcut";

export {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuCheckboxItem,
  ContextMenuRadioItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuGroup,
  ContextMenuPortal,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuRadioGroup,
};
