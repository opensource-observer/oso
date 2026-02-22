import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/notebook/index";
import { datasetResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/dataset/index";
import { dataModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/data-model/index";
import { staticModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/static-model/index";
import { dataConnectionResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/data-connection/index";
import { runResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/run/index";
import { organizationOrganizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/organization/index";
import { invitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/invitation/index";
import { stepResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/step/index";
import { materializationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/materialization/index";

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
    ...notebookResolvers.Mutation,
    ...datasetResolvers.Mutation,
    ...dataModelResolvers.Mutation,
    ...staticModelResolvers.Mutation,
    ...dataConnectionResolvers.Mutation,
    ...runResolvers.Mutation,
    ...organizationOrganizationResolvers.Mutation,
    ...invitationResolvers.Mutation,
  },
  Organization: organizationOrganizationResolvers.Organization,
  OrganizationMember: organizationOrganizationResolvers.OrganizationMember,
  Invitation: invitationResolvers.Invitation,
  Run: runResolvers.Run,
  Step: stepResolvers.Step,
  Materialization: materializationResolvers.Materialization,
};
