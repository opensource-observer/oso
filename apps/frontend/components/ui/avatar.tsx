"use client";

import * as React from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";

type AvatarProps = React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Root>;

const Avatar = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Root>,
  AvatarProps
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full",
      className,
    )}
    {...props}
  />
));
Avatar.displayName = AvatarPrimitive.Root.displayName;

const AvatarMeta: CodeComponentMeta<AvatarProps> = {
  name: "Avatar",
  description: "shadcn/ui Avatar component",
  props: {
    children: "slot",
  },
};

type AvatarImageProps = React.ComponentPropsWithoutRef<
  typeof AvatarPrimitive.Image
>;

const AvatarImage = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Image>,
  AvatarImageProps
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Image
    ref={ref}
    className={cn("aspect-square h-full w-full", className)}
    {...props}
  />
));
AvatarImage.displayName = AvatarPrimitive.Image.displayName;

const AvatarImageMeta: CodeComponentMeta<AvatarImageProps> = {
  name: "AvatarImage",
  description: "shadcn/ui AvatarImage component",
  props: {
    src: "string",
    alt: "string",
  },
};

type AvatarFallbackProps = React.ComponentPropsWithoutRef<
  typeof AvatarPrimitive.Fallback
>;

const AvatarFallback = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Fallback>,
  AvatarFallbackProps
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Fallback
    ref={ref}
    className={cn(
      "flex h-full w-full items-center justify-center rounded-full bg-muted",
      className,
    )}
    {...props}
  />
));
AvatarFallback.displayName = AvatarPrimitive.Fallback.displayName;

const AvatarFallbackMeta: CodeComponentMeta<AvatarFallbackProps> = {
  name: "AvatarFallback",
  description: "shadcn/ui AvatarFallback component",
  props: {
    children: "slot",
  },
};

export {
  Avatar,
  AvatarImage,
  AvatarFallback,
  // Meta
  AvatarMeta,
  AvatarImageMeta,
  AvatarFallbackMeta,
};
