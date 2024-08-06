/**
 * This hopefully will clean up our plasmic registration a bit. The registration
 * options should live with the component definition as opposed to in the
 * monolithic plasmic file. This keeps things together.
 */
import {
  NextJsPlasmicComponentLoader,
  CodeComponentMeta,
} from "@plasmicapp/loader-nextjs";
import { ComponentType } from "react";

export function plasmicRegistration<P>(
  component: ComponentType<P>,
  meta: CodeComponentMeta<P>,
) {
  return (PLASMIC: NextJsPlasmicComponentLoader) => {
    PLASMIC.registerComponent(component, meta);
  };
}
