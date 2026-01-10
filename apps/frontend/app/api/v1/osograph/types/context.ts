import type { SystemCredentials } from "@/lib/types/system";
import type { User } from "@/lib/types/user";

export type AuthenticatedUser = Extract<User, { role: "user" }>;

export type GraphQLContext = {
  req: Request;
  user: User;
  systemCredentials?: SystemCredentials;
};
