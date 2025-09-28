"use client";

import * as React from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Check, ChevronRight, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

type DropdownMenuProps = React.ComponentProps<
  typeof DropdownMenuPrimitive.Root
> & {
  testOpen?: boolean;
};

function DropdownMenu(props: DropdownMenuProps) {
  // testOpen is an edit-time only prop to force the menu open in Plasmic Studio
  const { testOpen, ...rest } = props;
  // if open is explicitly set, respect that, otherwise use testOpen
  const open = props.open || testOpen;

  return <DropdownMenuPrimitive.Root {...rest} open={open} />;
}

const DropdownMenuMeta: CodeComponentMeta<DropdownMenuProps> = {
  name: "DropdownMenu",
  description: "shadcn/ui DropdownMenu component",
  props: {
    children: "slot",
    testOpen: {
      type: "boolean",
      advanced: true,
      editOnly: true,
    },
  },
};

const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;

type DropdownMenuTriggerProps = React.ComponentProps<
  typeof DropdownMenuTrigger
>;

const DropdownMenuTriggerMeta: CodeComponentMeta<DropdownMenuTriggerProps> = {
  name: "DropdownMenuTrigger",
  description: "shadcn/ui DropdownMenuTrigger component",
  props: {
    children: "slot",
    asChild: "boolean",
  },
};

const DropdownMenuGroup = DropdownMenuPrimitive.Group;

type DropdownMenuGroupProps = React.ComponentProps<typeof DropdownMenuGroup>;

const DropdownMenuGroupMeta: CodeComponentMeta<DropdownMenuGroupProps> = {
  name: "DropdownMenuGroup",
  description: "shadcn/ui DropdownMenuGroup component",
  props: {
    children: "slot",
  },
};

const DropdownMenuPortal = DropdownMenuPrimitive.Portal;

type DropdownMenuPortalProps = React.ComponentProps<typeof DropdownMenuPortal>;

const DropdownMenuPortalMeta: CodeComponentMeta<DropdownMenuPortalProps> = {
  name: "DropdownMenuPortal",
  description: "shadcn/ui DropdownMenuPortal component",
  props: {
    children: "slot",
  },
};

const DropdownMenuSub = DropdownMenuPrimitive.Sub;

type DropdownMenuSubProps = React.ComponentProps<typeof DropdownMenuSub>;

const DropdownMenuSubMeta: CodeComponentMeta<DropdownMenuSubProps> = {
  name: "DropdownMenuSub",
  description: "shadcn/ui DropdownMenuSub component",
  props: {
    children: "slot",
  },
};

const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup;

type DropdownMenuRadioGroupProps = React.ComponentProps<
  typeof DropdownMenuRadioGroup
>;

const DropdownMenuRadioGroupMeta: CodeComponentMeta<DropdownMenuRadioGroupProps> =
  {
    name: "DropdownMenuRadioGroup",
    description: "shadcn/ui DropdownMenuRadioGroup component",
    props: {
      children: "slot",
    },
  };

type DropdownMenuSubTriggerProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.SubTrigger
> & {
  inset?: boolean;
};

const DropdownMenuSubTriggerMeta: CodeComponentMeta<DropdownMenuSubTriggerProps> =
  {
    name: "DropdownMenuSubTrigger",
    description: "shadcn/ui DropdownMenuSubTrigger component",
    props: {
      children: "slot",
      inset: "boolean",
    },
  };

const DropdownMenuSubTrigger = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.SubTrigger>,
  DropdownMenuSubTriggerProps
>(({ className, inset, children, ...props }, ref) => (
  <DropdownMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent data-[state=open]:bg-accent [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
      inset && "pl-8",
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="ml-auto" />
  </DropdownMenuPrimitive.SubTrigger>
));
DropdownMenuSubTrigger.displayName =
  DropdownMenuPrimitive.SubTrigger.displayName;

type DropdownMenuSubContentProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.SubContent
>;

const DropdownMenuSubContentMeta: CodeComponentMeta<DropdownMenuSubContentProps> =
  {
    name: "DropdownMenuSubContent",
    description: "shadcn/ui DropdownMenuSubContent component",
    props: {
      children: "slot",
    },
  };

const DropdownMenuSubContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.SubContent>,
  DropdownMenuSubContentProps
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.SubContent
    ref={ref}
    className={cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-[--radix-dropdown-menu-content-transform-origin]",
      className,
    )}
    {...props}
  />
));
DropdownMenuSubContent.displayName =
  DropdownMenuPrimitive.SubContent.displayName;

type DropdownMenuContentProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.Content
>;

const DropdownMenuContentMeta: CodeComponentMeta<DropdownMenuContentProps> = {
  name: "DropdownMenuContent",
  description: "shadcn/ui DropdownMenuContent component",
  props: {
    children: "slot",
    align: {
      type: "choice",
      options: ["start", "center", "end"],
    },
    side: {
      type: "choice",
      options: ["top", "right", "bottom", "left"],
    },
    sideOffset: "number",
  },
};

const DropdownMenuContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  DropdownMenuContentProps
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 max-h-[var(--radix-dropdown-menu-content-available-height)] min-w-[8rem] overflow-y-auto overflow-x-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-[--radix-dropdown-menu-content-transform-origin]",
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
));
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;

type DropdownMenuItemProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.Item
> & {
  inset?: boolean;
};

const DropdownMenuItemMeta: CodeComponentMeta<DropdownMenuItemProps> = {
  name: "DropdownMenuItem",
  description: "shadcn/ui DropdownMenuItem component",
  props: {
    children: "slot",
    inset: "boolean",
  },
};

const DropdownMenuItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  DropdownMenuItemProps
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&>svg]:size-4 [&>svg]:shrink-0",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;

type DropdownMenuCheckboxItemProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.CheckboxItem
>;

const DropdownMenuCheckboxItemMeta: CodeComponentMeta<DropdownMenuCheckboxItemProps> =
  {
    name: "DropdownMenuCheckboxItem",
    description: "shadcn/ui DropdownMenuCheckboxItem component",
    props: {
      children: "slot",
    },
  };

const DropdownMenuCheckboxItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.CheckboxItem>,
  DropdownMenuCheckboxItemProps
>(({ className, children, checked, ...props }, ref) => (
  <DropdownMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.CheckboxItem>
));
DropdownMenuCheckboxItem.displayName =
  DropdownMenuPrimitive.CheckboxItem.displayName;

type DropdownMenuRadioItemProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.RadioItem
>;

const DropdownMenuRadioItemMeta: CodeComponentMeta<DropdownMenuRadioItemProps> =
  {
    name: "DropdownMenuRadioItem",
    description: "shadcn/ui DropdownMenuRadioItem component",
    props: {
      children: "slot",
    },
  };

const DropdownMenuRadioItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.RadioItem>,
  DropdownMenuRadioItemProps
>(({ className, children, ...props }, ref) => (
  <DropdownMenuPrimitive.RadioItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Circle className="h-2 w-2 fill-current" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.RadioItem>
));
DropdownMenuRadioItem.displayName = DropdownMenuPrimitive.RadioItem.displayName;

type DropdownMenuLabelProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.Label
> & {
  inset?: boolean;
};

const DropdownMenuLabelMeta: CodeComponentMeta<DropdownMenuLabelProps> = {
  name: "DropdownMenuLabel",
  description: "shadcn/ui DropdownMenuLabel component",
  props: {
    children: "slot",
    inset: "boolean",
  },
};

const DropdownMenuLabel = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Label>,
  DropdownMenuLabelProps
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn(
      "px-2 py-1.5 text-sm font-semibold",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName;

type DropdownMenuSeparatorProps = React.ComponentPropsWithoutRef<
  typeof DropdownMenuPrimitive.Separator
>;

const DropdownMenuSeparatorMeta: CodeComponentMeta<DropdownMenuSeparatorProps> =
  {
    name: "DropdownMenuSeparator",
    description: "shadcn/ui DropdownMenuSeparator component",
    props: {},
  };

const DropdownMenuSeparator = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Separator>,
  DropdownMenuSeparatorProps
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-muted", className)}
    {...props}
  />
));
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName;

const DropdownMenuShortcut = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      className={cn("ml-auto text-xs tracking-widest opacity-60", className)}
      {...props}
    />
  );
};
DropdownMenuShortcut.displayName = "DropdownMenuShortcut";

type DropdownMenuShortcutProps = React.HTMLAttributes<HTMLSpanElement>;

const DropdownMenuShortcutMeta: CodeComponentMeta<DropdownMenuShortcutProps> = {
  name: "DropdownMenuShortcut",
  description: "shadcn/ui DropdownMenuShortcut component",
  props: {
    children: "slot",
  },
};

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
  // Meta
  DropdownMenuMeta,
  DropdownMenuTriggerMeta,
  DropdownMenuContentMeta,
  DropdownMenuItemMeta,
  DropdownMenuGroupMeta,
  DropdownMenuPortalMeta,
  DropdownMenuSubMeta,
  DropdownMenuRadioGroupMeta,
  DropdownMenuSubTriggerMeta,
  DropdownMenuSubContentMeta,
  DropdownMenuCheckboxItemMeta,
  DropdownMenuRadioItemMeta,
  DropdownMenuLabelMeta,
  DropdownMenuSeparatorMeta,
  DropdownMenuShortcutMeta,
};
