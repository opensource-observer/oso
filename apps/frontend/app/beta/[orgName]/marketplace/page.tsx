import { query } from "@/lib/clients/apollo-app";
import { MarketplaceContent } from "@/app/beta/[orgName]/marketplace/_components/marketplace-content";
import { RESOLVE_ORGANIZATION } from "@/app/beta/[orgName]/marketplace/_graphql/queries";
import { notFound } from "next/navigation";

export default async function MarketplacePage({
  params,
}: {
  params: { orgName: string };
}) {
  // Resolve organization on the server
  const { data: orgData } = await query({
    query: RESOLVE_ORGANIZATION,
    variables: {
      where: { org_name: { eq: params.orgName } },
    },
    errorPolicy: "all",
  });

  const orgId = orgData?.organizations?.edges?.[0]?.node?.id;

  if (!orgId) {
    notFound();
  }

  return <MarketplaceContent orgId={orgId} />;
}
