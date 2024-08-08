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

type Registration = (PLASMIC: NextJsPlasmicComponentLoader) => void;

export function registerComponent<P>(
  component: ComponentType<P>,
  meta: CodeComponentMeta<P>,
): Registration {
  return (PLASMIC: NextJsPlasmicComponentLoader) => {
    PLASMIC.registerComponent(component, meta);
  };
}

type RegisterFuncArgs<F extends (...args: any[]) => any> = Parameters<
  typeof NextJsPlasmicComponentLoader.prototype.registerFunction<F>
>;

export function registerFunction<F extends (...args: any) => any>(
  fn: F,
  meta: RegisterFuncArgs<F>[1],
): Registration {
  return (PLASMIC: NextJsPlasmicComponentLoader) => {
    PLASMIC.registerFunction(fn, meta);
  };
}

export function groupRegistrations(...args: Registration[]): Registration {
  return (PLASMIC: NextJsPlasmicComponentLoader) => {
    args.forEach((reg) => {
      reg(PLASMIC);
    });
  };
}
