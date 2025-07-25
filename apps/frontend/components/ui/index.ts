import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import { Skeleton, SkeletonMeta } from "@/components/ui/skeleton";
import { ToolTip, ToolTipMeta } from "@/components/ui/tooltip";

export function registerAllUi(PLASMIC: NextJsPlasmicComponentLoader) {
  // shadcn/ui
  PLASMIC.registerComponent(Skeleton, SkeletonMeta);
  PLASMIC.registerComponent(ToolTip, ToolTipMeta);
}
