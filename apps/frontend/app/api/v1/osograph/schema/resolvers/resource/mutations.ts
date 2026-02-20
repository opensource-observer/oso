import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  GrantResourcePermissionSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  getOrgResourceClient,
  RESOURCE_CONFIG,
} from "@/app/api/v1/osograph/utils/access-control";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { MutationGrantResourcePermissionArgs } from "@/lib/graphql/generated/graphql";
import { logger } from "@/lib/logger";

/**
 * Generic resource permission mutations
 */
export const resourceMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    grantResourcePermission: async (
      _: unknown,
      args: MutationGrantResourcePermissionArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(GrantResourcePermissionSchema, args.input);

      // Require admin permission to grant/revoke resource permissions
      const { client } = await getOrgResourceClient(
        context,
        input.resourceType,
        input.id,
        "admin",
      );

      // Get the current user ID for granted_by field
      const user = requireAuthentication(context.user);
      const userId = user.userId;

      const resourceConfig = RESOURCE_CONFIG[input.resourceType];

      switch (input.permissionLevel) {
        case "none": {
          // Revoke permission
          let query = client
            .from("resource_permissions")
            .update({ revoked_at: new Date().toISOString() })
            .is("revoked_at", null)
            .eq(resourceConfig.permissionColumn, input.id);

          // Add target filters
          if (input.targetUserId !== undefined) {
            query = query.eq("user_id", input.targetUserId);
          } else {
            query = query.is("user_id", null);
          }
          if (input.targetOrgId !== undefined) {
            query = query.eq("org_id", input.targetOrgId);
          } else {
            query = query.is("org_id", null);
          }

          logger.info("Revoking resource permission for", {
            input,
          });

          const { error: revokeError } = await query;

          if (revokeError) {
            logger.error("Failed to revoke resource permission:", revokeError);
            throw ServerErrors.database(
              `Failed to revoke resource permission: ${revokeError.message}`,
            );
          }

          return {
            success: true,
            message: "Permission revoked successfully",
          };
        }

        case "read":
        case "write":
        case "admin": {
          // Grant permission
          const insertData = {
            [resourceConfig.permissionColumn]: input.id,
            user_id: input.targetUserId || null,
            org_id: input.targetOrgId || null,
            permission_level: input.permissionLevel,
            granted_by: userId,
          };

          logger.info("Granting resource permission with insert data", {
            insertData,
          });

          const { error: insertError } = await client
            .from("resource_permissions")
            .insert(insertData);

          if (insertError) {
            if (insertError.code === "23505") {
              logger.warn("Permission already exists, skipping insert:", {
                insertData,
              });
              return {
                success: true,
                message: "Permission already exists",
              };
            }
            logger.error("Failed to grant resource permission:", insertError);
            throw ServerErrors.database(
              `Failed to grant resource permission: ${insertError.message}`,
            );
          }

          let message = "Permission granted successfully";
          if (!input.targetUserId && !input.targetOrgId) {
            message = `Resource is now public with ${input.permissionLevel} access`;
          } else if (input.targetOrgId) {
            message = `Permission granted to organization`;
          } else if (input.targetUserId) {
            message = `Permission granted to user`;
          }

          return {
            success: true,
            message,
          };
        }

        default:
          throw ServerErrors.internal(
            `Permission level ${input.permissionLevel} not implemented`,
          );
      }
    },
  };
