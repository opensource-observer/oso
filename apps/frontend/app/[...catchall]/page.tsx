import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { notFound } from "next/navigation";
import { PLASMIC } from "@/plasmic-init";
import { PlasmicClientRootProvider } from "@/plasmic-init-client";
import type { Metadata, Viewport } from "next";
import { generateNotebookMetadata } from "@/lib/utils/og-metadata";
import { getPageComponentAndProps } from "@/lib/plasmic/component-route";

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

  // Here we can determine which component to render for server side routing.
  const { component, props: pageProps } =
    await getPageComponentAndProps(pageMeta);

  return (
    <PlasmicClientRootProvider
      prefetchedData={prefetchedData}
      pageParams={pageMeta.params}
      pageQuery={searchParams}
    >
      <PlasmicComponent component={component} componentProps={pageProps} />
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
