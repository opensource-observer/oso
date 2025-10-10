import * as React from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border bg-card text-card-foreground shadow",
      className,
    )}
    {...props}
  />
));
Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

const CardMeta: CodeComponentMeta<React.HTMLAttributes<HTMLDivElement>> = {
  name: "Card",
  description: "A card container component",
  props: {
    children: "slot",
  },
};

const CardHeaderMeta: CodeComponentMeta<React.HTMLAttributes<HTMLDivElement>> =
  {
    name: "CardHeader",
    description: "Card header section",
    props: {
      children: "slot",
    },
  };

const CardTitleMeta: CodeComponentMeta<React.HTMLAttributes<HTMLDivElement>> = {
  name: "CardTitle",
  description: "Card title text",
  props: {
    children: "slot",
  },
};

const CardDescriptionMeta: CodeComponentMeta<
  React.HTMLAttributes<HTMLDivElement>
> = {
  name: "CardDescription",
  description: "Card description text",
  props: {
    children: "slot",
  },
};

const CardContentMeta: CodeComponentMeta<React.HTMLAttributes<HTMLDivElement>> =
  {
    name: "CardContent",
    description: "Card main content section",
    props: {
      children: "slot",
    },
  };

const CardFooterMeta: CodeComponentMeta<React.HTMLAttributes<HTMLDivElement>> =
  {
    name: "CardFooter",
    description: "Card footer section",
    props: {
      children: "slot",
    },
  };

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardMeta,
  CardHeaderMeta,
  CardFooterMeta,
  CardTitleMeta,
  CardDescriptionMeta,
  CardContentMeta,
};
