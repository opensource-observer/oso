type AnonUser = {
  role: "anonymous";
  host: string | null;
};
type UserDetails = {
  userId: string;
  keyName: string;
  host: string | null;
  email?: string;
  name: string;
};
type NormalUser = UserDetails & {
  role: "user";
};
type AdminUser = UserDetails & {
  role: "admin";
};

type AuthUser = NormalUser | AdminUser;
type User = AnonUser | AuthUser;

export type { AnonUser, NormalUser, AdminUser, AuthUser, User };
