"use client";

import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";
import { toggleVariants } from "@/components/ui/toggle";

const ToggleGroupContext = React.createContext<
  VariantProps<typeof toggleVariants>
>({
  size: "default",
  variant: "default",
});

const ToggleGroup = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root> &
    VariantProps<typeof toggleVariants>
>(({ className, variant, size, children, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    className={cn("flex items-center justify-center gap-1", className)}
    {...props}
  >
    <ToggleGroupContext.Provider value={{ variant, size }}>
      {children}
    </ToggleGroupContext.Provider>
  </ToggleGroupPrimitive.Root>
));

ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

const ToggleGroupItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item> &
    VariantProps<typeof toggleVariants>
>(({ className, children, variant, size, ...props }, ref) => {
  const context = React.useContext(ToggleGroupContext);

  return (
    <ToggleGroupPrimitive.Item
      ref={ref}
      className={cn(
        toggleVariants({
          variant: context.variant || variant,
          size: context.size || size,
        }),
        className,
      )}
      {...props}
    >
      {children}
    </ToggleGroupPrimitive.Item>
  );
});

ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;

type ToggleGroupProps = React.ComponentPropsWithoutRef<
  typeof ToggleGroupPrimitive.Root
> &
  VariantProps<typeof toggleVariants>;

export const ToggleGroupMeta: CodeComponentMeta<ToggleGroupProps> = {
  name: "ToggleGroup",
  description: "shadcn/ui ToggleGroup component",
  props: {
    children: "slot",
    type: {
      type: "choice",
      options: ["single", "multiple"],
      defaultValue: "single",
    },
    variant: {
      type: "choice",
      options: ["default", "outline"],
      defaultValueHint: "default",
    },
    size: {
      type: "choice",
      options: ["default", "sm", "lg"],
      defaultValueHint: "default",
    },
    defaultValue: {
      type: "object",
      helpText: "For 'multiple' type, provide an array of values",
    },
    onValueChange: {
      type: "eventHandler",
      argTypes: [{ name: "value", type: "object" }],
    },
    disabled: "boolean",
  },
  states: {
    value: {
      type: "readonly",
      variableType: "object",
      onChangeProp: "onValueChange",
      onChangeArgsToValue: (value) => value,
    },
  },
};

type ToggleGroupItemProps = React.ComponentPropsWithoutRef<
  typeof ToggleGroupPrimitive.Item
> &
  VariantProps<typeof toggleVariants>;

export const ToggleGroupItemMeta: CodeComponentMeta<ToggleGroupItemProps> = {
  name: "ToggleGroupItem",
  description: "shadcn/ui ToggleGroupItem component",
  props: {
    children: "slot",
    value: {
      type: "string",
      required: true,
    },
    disabled: "boolean",
  },
};

export { ToggleGroup, ToggleGroupItem };
