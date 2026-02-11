import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { viewerResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/viewer/index";
import { invitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/invitation/index";
import { userUserResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/user/index";
import { dataConnectionResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/data-connection/index";
import { datasetResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/dataset/index";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/notebook/index";
import { organizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/organization/index";
import { dataModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/data-model/index";
import { staticModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/static-model/index";
import { runsResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/runs/index";

/**
 * User-scoped resolvers (viewer query).
 * Uses getAuthenticatedClient for authenticated user operations.
 */
export const userResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...viewerResolvers.Query,
    ...runsResolvers.Query,
    ...invitationResolvers.Query,
    ...dataConnectionResolvers.Query,
    ...datasetResolvers.Query,
    ...notebookResolvers.Query,
    ...organizationResolvers.Query,
    ...dataModelResolvers.Query,
    ...staticModelResolvers.Query,
  },
  Mutation: {
    ...invitationResolvers.Mutation,
  },
  Viewer: viewerResolvers.Viewer,
  User: userUserResolvers.User,
};
