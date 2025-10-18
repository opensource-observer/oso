"use client";

import * as React from "react";
import { type DialogProps } from "@radix-ui/react-dialog";
import { Command as CommandPrimitive } from "cmdk";
import { Search } from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";
import { Dialog, DialogContent } from "@/components/ui/dialog";

const Command = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive>
>(({ className, ...props }, ref) => (
  <CommandPrimitive
    ref={ref}
    className={cn(
      "flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground",
      className,
    )}
    {...props}
  />
));
Command.displayName = CommandPrimitive.displayName;

const CommandDialog = ({ children, ...props }: DialogProps) => {
  return (
    <Dialog {...props}>
      <DialogContent className="overflow-hidden p-0">
        <Command className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-group]]:px-2 [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5">
          {children}
        </Command>
      </DialogContent>
    </Dialog>
  );
};

const CommandInput = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Input>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Input>
>(({ className, ...props }, ref) => (
  <div className="flex items-center border-b px-3" cmdk-input-wrapper="">
    <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
    <CommandPrimitive.Input
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  </div>
));

CommandInput.displayName = CommandPrimitive.Input.displayName;

const CommandList = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.List>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.List
    ref={ref}
    className={cn("max-h-[300px] overflow-y-auto overflow-x-hidden", className)}
    {...props}
  />
));

CommandList.displayName = CommandPrimitive.List.displayName;

const CommandEmpty = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Empty>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Empty>
>((props, ref) => (
  <CommandPrimitive.Empty
    ref={ref}
    className="py-6 text-center text-sm"
    {...props}
  />
));

CommandEmpty.displayName = CommandPrimitive.Empty.displayName;

const CommandGroup = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Group>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Group>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Group
    ref={ref}
    className={cn(
      "overflow-hidden p-1 text-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground",
      className,
    )}
    {...props}
  />
));

CommandGroup.displayName = CommandPrimitive.Group.displayName;

const CommandSeparator = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 h-px bg-border", className)}
    {...props}
  />
));
CommandSeparator.displayName = CommandPrimitive.Separator.displayName;

const CommandItem = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default gap-2 select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled=true]:pointer-events-none data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground data-[disabled=true]:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
      className,
    )}
    {...props}
  />
));

CommandItem.displayName = CommandPrimitive.Item.displayName;

const CommandShortcut = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) => {
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
CommandShortcut.displayName = "CommandShortcut";

type CommandProps = React.ComponentPropsWithoutRef<typeof CommandPrimitive>;
type CommandDialogProps = DialogProps;
type CommandInputProps = React.ComponentPropsWithoutRef<
  typeof CommandPrimitive.Input
>;
type CommandListProps = React.ComponentPropsWithoutRef<
  typeof CommandPrimitive.List
>;
type CommandEmptyProps = React.ComponentPropsWithoutRef<
  typeof CommandPrimitive.Empty
>;
type CommandGroupProps = React.ComponentPropsWithoutRef<
  typeof CommandPrimitive.Group
>;
type CommandItemProps = React.ComponentPropsWithoutRef<
  typeof CommandPrimitive.Item
>;
type CommandShortcutProps = React.HTMLAttributes<HTMLSpanElement>;
type CommandSeparatorProps = React.ComponentPropsWithoutRef<
  typeof CommandPrimitive.Separator
>;

export const CommandMeta: CodeComponentMeta<CommandProps> = {
  name: "Command",
  description: "Command menu container for search and navigation",
  props: {
    children: "slot",
  },
};

export const CommandDialogMeta: CodeComponentMeta<CommandDialogProps> = {
  name: "CommandDialog",
  description: "Command menu displayed in a dialog",
  props: {
    children: "slot",
    open: "boolean",
    onOpenChange: {
      type: "eventHandler",
      argTypes: [{ name: "open", type: "boolean" }],
    },
  },
};

export const CommandInputMeta: CodeComponentMeta<CommandInputProps> = {
  name: "CommandInput",
  description: "Search input for command menu",
  props: {
    placeholder: {
      type: "string",
      defaultValue: "Search...",
    },
    value: "string",
    onValueChange: {
      type: "eventHandler",
      argTypes: [{ name: "value", type: "string" }],
    },
  },
};

export const CommandListMeta: CodeComponentMeta<CommandListProps> = {
  name: "CommandList",
  description: "Container for command items with scrolling",
  props: {
    children: "slot",
  },
};

export const CommandEmptyMeta: CodeComponentMeta<CommandEmptyProps> = {
  name: "CommandEmpty",
  description: "Message shown when no results are found",
  props: {
    children: {
      type: "slot",
      defaultValue: "No results found.",
    },
  },
};

export const CommandGroupMeta: CodeComponentMeta<CommandGroupProps> = {
  name: "CommandGroup",
  description: "Group of related command items",
  props: {
    children: "slot",
    heading: "string",
  },
};

export const CommandItemMeta: CodeComponentMeta<CommandItemProps> = {
  name: "CommandItem",
  description: "Individual selectable item in command menu",
  props: {
    children: "slot",
    value: "string",
    onSelect: {
      type: "eventHandler",
      argTypes: [{ name: "value", type: "string" }],
    },
    disabled: "boolean",
  },
};

export const CommandShortcutMeta: CodeComponentMeta<CommandShortcutProps> = {
  name: "CommandShortcut",
  description: "Keyboard shortcut indicator for command items",
  props: {
    children: "slot",
  },
};

export const CommandSeparatorMeta: CodeComponentMeta<CommandSeparatorProps> = {
  name: "CommandSeparator",
  description: "Visual separator between command groups",
  props: {},
};

export {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
};
