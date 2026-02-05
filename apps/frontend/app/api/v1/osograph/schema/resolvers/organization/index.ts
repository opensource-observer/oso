import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/notebook/mutations";
import { datasetMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/dataset/mutations";
import { dataModelMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/data-model/mutations";
import { staticModelMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/static-model/mutations";
import { dataIngestionMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/data-ingestion/mutations";
import { dataConnectionMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/data-connection/mutations";
import { organizationOrganizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/organization/index";
import { invitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/invitation/index";

/**
 * Organization-scoped resolvers.
 * These resolvers use getOrgScopedClient for operations that don't have
 * a specific resource ID yet (e.g., creating new resources).
 */
export const organizationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...organizationOrganizationResolvers.Query,
    ...invitationResolvers.Query,
  },
  Mutation: {
    ...notebookMutations,
    ...datasetMutations,
    ...dataModelMutations,
    ...staticModelMutations,
    ...dataIngestionMutations,
    ...dataConnectionMutations,
    ...organizationOrganizationResolvers.Mutation,
    ...invitationResolvers.Mutation,
  },
  Organization: organizationOrganizationResolvers.Organization,
  OrganizationMember: organizationOrganizationResolvers.OrganizationMember,
};
