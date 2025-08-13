"use client";

import { PlasmicRootProvider } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "@/plasmic-init";
import { registerAllDataProvider } from "@/components/dataprovider";
import { registerAllUi } from "@/components/ui";
import { registerAllWidgets } from "@/components/widgets";
import { registerAllFunctions } from "@/lib/index";

/**
 * Plasmic component registration
 *
 * For more details see:
 * https://docs.plasmic.app/learn/code-components-ref/
 */

registerAllDataProvider(PLASMIC);
registerAllUi(PLASMIC);
registerAllWidgets(PLASMIC);
registerAllFunctions(PLASMIC);

/**
 * PlasmicClientRootProvider is a Client Component that passes in the loader for you.
 *
 * Why? Props passed from Server to Client Components must be serializable.
 * https://beta.nextjs.org/docs/rendering/server-and-client-components#passing-props-from-server-to-client-components-serialization
 * However, PlasmicRootProvider requires a loader, but the loader is NOT serializable.
 */
export function PlasmicClientRootProvider(
  props: Omit<React.ComponentProps<typeof PlasmicRootProvider>, "loader">,
) {
  return (
    <PlasmicRootProvider loader={PLASMIC} {...props}></PlasmicRootProvider>
  );
}
