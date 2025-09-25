import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { notFound } from "next/navigation";
import { PLASMIC } from "@/plasmic-init";
import { PlasmicClientRootProvider } from "@/plasmic-init-client";
import type { Metadata, ResolvingMetadata } from "next";
import { generateNotebookMetadata } from "@/lib/utils/og-metadata";

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
  return (
    <PlasmicClientRootProvider
      prefetchedData={prefetchedData}
      pageParams={pageMeta.params}
      pageQuery={searchParams}
    >
      <PlasmicComponent component={pageMeta.displayName} />
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

export async function generateMetadata(
  { params }: MetadataProps,
  parent: ResolvingMetadata,
): Promise<Metadata> {
  const { catchall } = await params;

  const plasmicComponentData = await fetchPlasmicComponentData(catchall);
  if (!plasmicComponentData) {
    notFound();
  }

  const { prefetchedData } = plasmicComponentData;
  if (prefetchedData.entryCompMetas.length === 0) {
    notFound();
  }

  const [{ pageMetadata }] = prefetchedData.entryCompMetas;

  if (catchall?.length === 2) {
    const [orgName, notebookName] = catchall;
    const notebookMetadata = await generateNotebookMetadata(
      orgName,
      notebookName,
      parent,
    );
    if (notebookMetadata) return notebookMetadata;
  }

  return {
    title: pageMetadata?.title,
    description: pageMetadata?.description,
    openGraph: {
      title: pageMetadata?.title ?? undefined,
      description: pageMetadata?.description ?? undefined,
      images: pageMetadata?.openGraphImageUrl
        ? [
            {
              url: pageMetadata?.openGraphImageUrl,
            },
          ]
        : [],
    },
  } satisfies Metadata;
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
