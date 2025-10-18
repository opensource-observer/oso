import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground [&>svg~*]:pl-7",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
));
Alert.displayName = "Alert";

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
));
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
));
AlertDescription.displayName = "AlertDescription";

type AlertProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof alertVariants>;
type AlertTitleProps = React.HTMLAttributes<HTMLHeadingElement>;
type AlertDescriptionProps = React.HTMLAttributes<HTMLParagraphElement>;

export const AlertMeta: CodeComponentMeta<AlertProps> = {
  name: "Alert",
  description: "shadcn/ui Alert component for displaying callouts",
  props: {
    children: "slot",
    variant: {
      type: "choice",
      options: ["default", "destructive"],
      defaultValue: "default",
    },
  },
};

export const AlertTitleMeta: CodeComponentMeta<AlertTitleProps> = {
  name: "AlertTitle",
  description: "Title for alert component",
  props: {
    children: "slot",
  },
};

export const AlertDescriptionMeta: CodeComponentMeta<AlertDescriptionProps> = {
  name: "AlertDescription",
  description: "Description content for alert component",
  props: {
    children: "slot",
  },
};

export { Alert, AlertTitle, AlertDescription };
