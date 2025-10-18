import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { ChevronRight, MoreHorizontal } from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const Breadcrumb = React.forwardRef<
  HTMLElement,
  React.ComponentPropsWithoutRef<"nav"> & {
    separator?: React.ReactNode;
  }
>(({ ...props }, ref) => <nav ref={ref} aria-label="breadcrumb" {...props} />);
Breadcrumb.displayName = "Breadcrumb";

const BreadcrumbList = React.forwardRef<
  HTMLOListElement,
  React.ComponentPropsWithoutRef<"ol">
>(({ className, ...props }, ref) => (
  <ol
    ref={ref}
    className={cn(
      "flex flex-wrap items-center gap-1.5 break-words text-sm text-muted-foreground sm:gap-2.5",
      className,
    )}
    {...props}
  />
));
BreadcrumbList.displayName = "BreadcrumbList";

const BreadcrumbItem = React.forwardRef<
  HTMLLIElement,
  React.ComponentPropsWithoutRef<"li">
>(({ className, ...props }, ref) => (
  <li
    ref={ref}
    className={cn("inline-flex items-center gap-1.5", className)}
    {...props}
  />
));
BreadcrumbItem.displayName = "BreadcrumbItem";

const BreadcrumbLink = React.forwardRef<
  HTMLAnchorElement,
  React.ComponentPropsWithoutRef<"a"> & {
    asChild?: boolean;
  }
>(({ asChild, className, ...props }, ref) => {
  const Comp = asChild ? Slot : "a";

  return (
    <Comp
      ref={ref}
      className={cn("transition-colors hover:text-foreground", className)}
      {...props}
    />
  );
});
BreadcrumbLink.displayName = "BreadcrumbLink";

const BreadcrumbPage = React.forwardRef<
  HTMLSpanElement,
  React.ComponentPropsWithoutRef<"span">
>(({ className, ...props }, ref) => (
  <span
    ref={ref}
    role="link"
    aria-disabled="true"
    aria-current="page"
    className={cn("font-normal text-foreground", className)}
    {...props}
  />
));
BreadcrumbPage.displayName = "BreadcrumbPage";

const BreadcrumbSeparator = ({
  children,
  className,
  ...props
}: React.ComponentProps<"li">) => (
  <li
    role="presentation"
    aria-hidden="true"
    className={cn("[&>svg]:w-3.5 [&>svg]:h-3.5", className)}
    {...props}
  >
    {children ?? <ChevronRight />}
  </li>
);
BreadcrumbSeparator.displayName = "BreadcrumbSeparator";

const BreadcrumbEllipsis = ({
  className,
  ...props
}: React.ComponentProps<"span">) => (
  <span
    role="presentation"
    aria-hidden="true"
    className={cn("flex h-9 w-9 items-center justify-center", className)}
    {...props}
  >
    <MoreHorizontal className="h-4 w-4" />
    <span className="sr-only">More</span>
  </span>
);
BreadcrumbEllipsis.displayName = "BreadcrumbElipssis";

type BreadcrumbProps = React.ComponentPropsWithoutRef<"nav"> & {
  separator?: React.ReactNode;
};
type BreadcrumbListProps = React.ComponentPropsWithoutRef<"ol">;
type BreadcrumbItemProps = React.ComponentPropsWithoutRef<"li">;
type BreadcrumbLinkProps = React.ComponentPropsWithoutRef<"a"> & {
  asChild?: boolean;
};
type BreadcrumbPageProps = React.ComponentPropsWithoutRef<"span">;
type BreadcrumbSeparatorProps = React.ComponentProps<"li">;
type BreadcrumbEllipsisProps = React.ComponentProps<"span">;

export const BreadcrumbMeta: CodeComponentMeta<BreadcrumbProps> = {
  name: "Breadcrumb",
  description: "Root breadcrumb navigation component",
  props: {
    children: "slot",
  },
};

export const BreadcrumbListMeta: CodeComponentMeta<BreadcrumbListProps> = {
  name: "BreadcrumbList",
  description: "Container for breadcrumb items",
  props: {
    children: "slot",
  },
};

export const BreadcrumbItemMeta: CodeComponentMeta<BreadcrumbItemProps> = {
  name: "BreadcrumbItem",
  description: "Individual breadcrumb item",
  props: {
    children: "slot",
  },
};

export const BreadcrumbLinkMeta: CodeComponentMeta<BreadcrumbLinkProps> = {
  name: "BreadcrumbLink",
  description: "Clickable breadcrumb link",
  props: {
    children: "slot",
    href: "string",
    asChild: {
      type: "boolean",
      description: "Merge props with child element instead of wrapping",
    },
  },
};

export const BreadcrumbPageMeta: CodeComponentMeta<BreadcrumbPageProps> = {
  name: "BreadcrumbPage",
  description: "Current page indicator in breadcrumb",
  props: {
    children: "slot",
  },
};

export const BreadcrumbSeparatorMeta: CodeComponentMeta<BreadcrumbSeparatorProps> =
  {
    name: "BreadcrumbSeparator",
    description: "Visual separator between breadcrumb items",
    props: {
      children: "slot",
    },
  };

export const BreadcrumbEllipsisMeta: CodeComponentMeta<BreadcrumbEllipsisProps> =
  {
    name: "BreadcrumbEllipsis",
    description: "Ellipsis indicator for collapsed breadcrumb items",
    props: {},
  };

export {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
  BreadcrumbEllipsis,
};
