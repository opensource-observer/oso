import { ComponentMeta, PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { notFound } from "next/navigation";
import { PLASMIC } from "@/plasmic-init";
import { PlasmicClientRootProvider } from "@/plasmic-init-client";
import type { Metadata, Viewport } from "next";
import { generateNotebookMetadata } from "@/lib/utils/og-metadata";
import { logger } from "@/lib/logger";
import { getPublishedNotebookByNames } from "@/lib/notebook/utils-server";

// Use revalidate if you want incremental static regeneration
// export const dynamic = "force-static";
export const revalidate = false; // 3600 = 1 hour

export default async function PlasmicLoaderPage({
  params,
  searchParams,
}: {
  params?: { catchall: string[] | undefined };
  searchParams?: Record<string, string | string[]>;
}) {
  const plasmicComponentData = await fetchPlasmicComponentData(
    params?.catchall,
  );
  if (!plasmicComponentData) {
    notFound();
  }

  const { prefetchedData } = plasmicComponentData;
  if (prefetchedData.entryCompMetas.length === 0) {
    notFound();
  }

  const pageMeta = prefetchedData.entryCompMetas[0];

  let pageProps = {};
  try {
    pageProps = await getPageProps(pageMeta);
  } catch (error) {
    logger.error("Error fetching page props:", error);
  }

  return (
    <PlasmicClientRootProvider
      prefetchedData={prefetchedData}
      pageParams={pageMeta.params}
      pageQuery={searchParams}
    >
      <PlasmicComponent
        component={pageMeta.displayName}
        componentProps={pageProps}
      />
    </PlasmicClientRootProvider>
  );
}

async function fetchPlasmicComponentData(catchall: string[] | undefined) {
  const plasmicPath = "/" + (catchall ? catchall.join("/") : "");
  const prefetchedData = await PLASMIC.maybeFetchComponentData(plasmicPath);
  if (!prefetchedData) {
    notFound();
  }

  return { prefetchedData };
}

type MetadataProps = {
  params: Promise<{ catchall?: string[] }>;
};

export async function generateMetadata({
  params,
}: MetadataProps): Promise<Metadata> {
  const { catchall } = await params;

  if (catchall?.length === 2) {
    const [orgName, notebookName] = catchall;
    const notebookMetadata = await generateNotebookMetadata(
      orgName,
      notebookName,
    );
    if (notebookMetadata) return notebookMetadata;
  }

  return {};
}

export async function generateViewport(
  props: MetadataProps,
): Promise<Viewport> {
  const { catchall } = await props.params;

  if (catchall?.length === 2) {
    return {
      themeColor: "#ffffff",
    };
  }

  return {};
}

export async function generateStaticParams() {
  const pageModules = await PLASMIC.fetchPages();
  return pageModules.map((mod) => {
    const catchall =
      mod.path === "/" ? undefined : mod.path.substring(1).split("/");
    return {
      catchall,
    };
  });
}

async function getPageProps(
  pageMeta: ComponentMeta & { params?: Record<string, string> },
): Promise<Record<string, any>> {
  const { params } = pageMeta;
  if (pageMeta.name === "OrganizationNotebookPage") {
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
