import { logger } from "@/lib/logger";
import { getPublishedNotebookByNames } from "@/lib/notebook/utils-server";
import { createServerClient } from "@/lib/supabase/server";
import { ComponentMeta } from "@plasmicapp/loader-nextjs";

/**
 * Mapping of components that have no-authenticated versions.
 * This is useful for server side routing where we want to
 * serve different components based on authentication status,
 * improving SEO for non authenticated pages.
 */
const noAuthComponents: Record<string, string> = {
  "Organization/NotebookPage": "NoAuthNotebookPage",
};

async function getComponentProps(
  pageMeta: ComponentMeta & { params?: Record<string, string> },
): Promise<Record<string, any>> {
  // params will have the route params, e.g /[orgName]/[notebookName] will have
  // { orgName: string, notebookName: string }
  const { params } = pageMeta;
  if (pageMeta.displayName === "Organization/NotebookPage") {
    const { orgName, notebookName } = params || {};
    if (!orgName || !notebookName) {
      return {};
    }
    const publishedNotebook = await getPublishedNotebookByNames(
      orgName,
      notebookName,
    );
    return {
      publishedHtml: publishedNotebook?.html,
    };
  }
  return {};
}

export async function getPageComponentAndProps(
  pageMeta: ComponentMeta & { params?: Record<string, string> },
) {
  const auth = await (await createServerClient()).auth.getSession();
  let props = {};
  try {
    props = await getComponentProps(pageMeta);
  } catch (error) {
    logger.error("Error fetching page props:", error);
  }

  const isAuthenticated = auth.data?.session != null;

  const component = isAuthenticated
    ? pageMeta.displayName
    : noAuthComponents[pageMeta.displayName] || pageMeta.displayName;

  return {
    props,
    component: component,
  };
}
