"use client";

import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import React from "react";

const Collapsible = CollapsiblePrimitive.Root;

type CollapsibleProps = React.ComponentProps<typeof Collapsible>;
const CollapsibleMeta: CodeComponentMeta<CollapsibleProps> = {
  name: "Collapsible",
  description: "shadcn/ui Collapsible component",
  variants: {
    open: {
      cssSelector: '[data-state="open"]',
      displayName: "Open",
    },
    hover: {
      cssSelector: ":hover",
      displayName: "Hover",
    },
  },
  props: {
    children: "slot",
    open: {
      type: "boolean",
      editOnly: true,
    },
    defaultOpen: "boolean",
    onOpenChange: {
      type: "eventHandler",
      argTypes: [{ name: "event", type: "object" }],
    },
    disabled: "boolean",
  },
};

const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger;

type CollapsibleTriggerProps = React.ComponentProps<typeof CollapsibleTrigger>;
const CollapsibleTriggerMeta: CodeComponentMeta<CollapsibleTriggerProps> = {
  name: "CollapsibleTrigger",
  description: "shadcn/ui CollapsibleTrigger component",
  props: {
    children: "slot",
    asChild: "boolean",
    className: {
      type: "class",
      selectors: [
        {
          selector: ":hover",
          label: "Hovered",
        },
      ],
    },
  },
};

const CollapsibleContent = CollapsiblePrimitive.CollapsibleContent;

type CollapsibleContentProps = React.ComponentProps<typeof CollapsibleContent>;
const CollapsibleContentMeta: CodeComponentMeta<CollapsibleContentProps> = {
  name: "CollapsibleContent",
  description: "shadcn/ui CollapsibleContent component",
  props: {
    children: "slot",
    asChild: "boolean",
  },
};

export {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
  CollapsibleMeta,
  CollapsibleTriggerMeta,
  CollapsibleContentMeta,
};
