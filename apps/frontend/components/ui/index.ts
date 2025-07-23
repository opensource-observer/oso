import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import { Skeleton, SkeletonMeta } from "@/components/ui/skeleton";

export function registerAllUi(PLASMIC: NextJsPlasmicComponentLoader) {
  // shadcn/ui
  PLASMIC.registerComponent(Skeleton, SkeletonMeta);
}
