import type { SystemCredentials } from "@/lib/types/system";
import type { User } from "@/lib/types/user";

export type AuthenticatedUser = Extract<User, { role: "user" }>;

export type AuthCache = {
  /** Maps "userId:orgId" to the user's role in that organization */
  orgMemberships: Map<string, string>;
  /** Maps "userId:resourceType:resourceId" to the user's permission level on that resource */
  resourcePermissions: Map<string, string>;
  /** Maps userId to the user's organization IDs */
  orgIds: Map<string, string[]>;
};

export type GraphQLContext = {
  req: Request;
  user: User;
  systemCredentials?: SystemCredentials;
  authCache: AuthCache;
};
