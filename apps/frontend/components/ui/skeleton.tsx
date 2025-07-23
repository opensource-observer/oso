import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { cn } from "@/lib/utils";

const SkeletonMeta: CodeComponentMeta<React.HTMLAttributes<HTMLDivElement>> = {
  name: "Skeleton",
  description: "Skeleton loading widget",
  props: {},
};

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-primary/10", className)}
      {...props}
    />
  );
}

export { Skeleton, SkeletonMeta };
