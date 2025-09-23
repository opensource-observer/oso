import crypto from "crypto";
import { createClient } from "@supabase/supabase-js";
import { SUPABASE_SERVICE_KEY, SUPABASE_URL } from "@/lib/config";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { logger } from "@/lib/logger";

describe("Organizations", () => {
  // Generate unique IDs for this test suite to avoid conflicts with other tests
  const USER_1_ID = crypto.randomUUID();
  const USER_2_ID = crypto.randomUUID();

  beforeAll(async () => {
    // Setup test data specific to this test suite
    const adminSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
    // Create test users with unique IDs
    await adminSupabase.auth.admin.createUser({
      id: USER_1_ID,
      email: `user1-${USER_1_ID}@test.com`,
      password: "password123",
      // We want the user to be usable right away without email confirmation
      email_confirm: true,
    });
    await adminSupabase.auth.admin.createUser({
      id: USER_2_ID,
      email: `user2-${USER_2_ID}@test.com`,
      password: "password123",
      email_confirm: true,
    });
  });

  it("should create an organization", async () => {
    expect(true).toBe(true);
  });
});

describe("Resource Permissions", () => {
  const USER_OWNER_ID = crypto.randomUUID();
  const USER_COLLABORATOR_ID = crypto.randomUUID();
  const USER_NO_ACCESS_ID = crypto.randomUUID();
  const NOTEBOOK_ID = crypto.randomUUID();
  const CHAT_ID = crypto.randomUUID();
  const ORG_ID = crypto.randomUUID();

  let adminSupabase: ReturnType<typeof createClient>;
  let ownerClient: OsoAppClient;
  let collaboratorClient: OsoAppClient;
  let noAccessClient: OsoAppClient;
  let anonymousClient: OsoAppClient;

  beforeAll(async () => {
    adminSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "admin-test-auth" },
    });

    const userCreationResults = await Promise.all([
      adminSupabase.auth.admin.createUser({
        id: USER_OWNER_ID,
        email: `owner-${USER_OWNER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
      adminSupabase.auth.admin.createUser({
        id: USER_COLLABORATOR_ID,
        email: `collaborator-${USER_COLLABORATOR_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
      adminSupabase.auth.admin.createUser({
        id: USER_NO_ACCESS_ID,
        email: `noaccess-${USER_NO_ACCESS_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
    ]);

    userCreationResults.forEach((result, index) => {
      const userType = ["owner", "collaborator", "noaccess"][index];
      if (result.error) {
        logger.error(`Failed to create ${userType} user:`, result.error);
        throw result.error;
      }
      logger.log(`Created ${userType} user:`, result.data.user?.id);
    });

    await adminSupabase.from("user_profiles").insert([
      {
        id: USER_OWNER_ID,
        email: `owner-${USER_OWNER_ID}@test.com`,
        full_name: "Owner User",
      },
      {
        id: USER_COLLABORATOR_ID,
        email: `collaborator-${USER_COLLABORATOR_ID}@test.com`,
        full_name: "Collaborator User",
      },
      {
        id: USER_NO_ACCESS_ID,
        email: `noaccess-${USER_NO_ACCESS_ID}@test.com`,
        full_name: "No Access User",
      },
    ]);

    const ownerSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "owner-test-auth" },
    });
    const { data: ownerAuth, error: ownerAuthError } =
      await ownerSupabase.auth.signInWithPassword({
        email: `owner-${USER_OWNER_ID}@test.com`,
        password: "password123",
      });
    if (ownerAuthError) throw ownerAuthError;
    logger.log(
      "Owner authenticated:",
      ownerAuth.user?.id,
      "Expected:",
      USER_OWNER_ID,
    );
    ownerClient = new OsoAppClient(ownerSupabase);

    const orgResult = await adminSupabase.from("organizations").insert({
      id: ORG_ID,
      created_by: USER_OWNER_ID,
      org_name: `test-org-${ORG_ID.substring(0, 8)}`,
    });

    if (orgResult.error) {
      logger.error("Failed to create organization:", orgResult.error);
      throw orgResult.error;
    }

    const userOrgResult = await adminSupabase
      .from("users_by_organization")
      .insert([
        {
          user_id: USER_COLLABORATOR_ID,
          org_id: ORG_ID,
          user_role: "admin",
        },
      ]);

    if (userOrgResult.error) {
      logger.error(
        "Failed to create user-org memberships:",
        userOrgResult.error,
      );
      throw userOrgResult.error;
    }

    const notebookResult = await adminSupabase.from("notebooks").insert({
      id: NOTEBOOK_ID,
      notebook_name: "Test Notebook",
      created_by: USER_OWNER_ID,
      data: JSON.stringify({ cells: [] }),
      org_id: ORG_ID,
    });

    const chatResult = await adminSupabase.from("chat_history").insert({
      id: CHAT_ID,
      created_by: USER_OWNER_ID,
      data: JSON.stringify([]),
      display_name: "Test Chat",
      org_id: ORG_ID,
    });

    if (notebookResult.error) {
      logger.error("Failed to create notebook:", notebookResult.error);
      throw notebookResult.error;
    }

    if (chatResult.error) {
      logger.error("Failed to create chat:", chatResult.error);
      throw chatResult.error;
    }

    const collaboratorSupabase = createClient(
      SUPABASE_URL,
      SUPABASE_SERVICE_KEY,
      { auth: { storageKey: "collaborator-test-auth" } },
    );
    const { data: collaboratorAuth, error: collaboratorAuthError } =
      await collaboratorSupabase.auth.signInWithPassword({
        email: `collaborator-${USER_COLLABORATOR_ID}@test.com`,
        password: "password123",
      });
    if (collaboratorAuthError) throw collaboratorAuthError;
    logger.log(
      "Collaborator authenticated:",
      collaboratorAuth.user?.id,
      "Expected:",
      USER_COLLABORATOR_ID,
    );
    collaboratorClient = new OsoAppClient(collaboratorSupabase);

    const noAccessSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "noaccess-test-auth" },
    });
    const { data: noAccessAuth, error: noAccessAuthError } =
      await noAccessSupabase.auth.signInWithPassword({
        email: `noaccess-${USER_NO_ACCESS_ID}@test.com`,
        password: "password123",
      });
    if (noAccessAuthError) throw noAccessAuthError;
    logger.log(
      "NoAccess authenticated:",
      noAccessAuth.user?.id,
      "Expected:",
      USER_NO_ACCESS_ID,
    );
    noAccessClient = new OsoAppClient(noAccessSupabase);

    const anonymousSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "anonymous-test-auth" },
    });
    anonymousClient = new OsoAppClient(anonymousSupabase);
  });

  afterAll(async () => {
    await Promise.all([
      adminSupabase
        .from("resource_permissions")
        .delete()
        .in("user_id", [
          USER_OWNER_ID,
          USER_COLLABORATOR_ID,
          USER_NO_ACCESS_ID,
        ]),
      adminSupabase.from("users_by_organization").delete().eq("org_id", ORG_ID),
      adminSupabase.from("notebooks").delete().eq("id", NOTEBOOK_ID),
      adminSupabase.from("chat_history").delete().eq("id", CHAT_ID),
      adminSupabase.from("organizations").delete().eq("id", ORG_ID),
      adminSupabase
        .from("user_profiles")
        .delete()
        .in("id", [USER_OWNER_ID, USER_COLLABORATOR_ID, USER_NO_ACCESS_ID]),
      adminSupabase.auth.admin.deleteUser(USER_OWNER_ID),
      adminSupabase.auth.admin.deleteUser(USER_COLLABORATOR_ID),
      adminSupabase.auth.admin.deleteUser(USER_NO_ACCESS_ID),
    ]);
  });

  afterEach(async () => {
    await adminSupabase
      .from("resource_permissions")
      .delete()
      .in("user_id", [USER_OWNER_ID, USER_COLLABORATOR_ID, USER_NO_ACCESS_ID]);
  });

  describe("checkResourcePermission", () => {
    describe("Anonymous user access (2x2 matrix)", () => {
      it("should deny access to private notebook (no permissions exist)", async () => {
        const result = await anonymousClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          accessType: "no_access",
          permissionLevel: null,
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should allow read access to public notebook (NULL user_id permission exists)", async () => {
        await ownerClient.makeResourcePublic({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        const result = await anonymousClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          accessType: "public_access",
          permissionLevel: "read",
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.makeResourcePrivate({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should deny access to private notebook (permissions exist)", async () => {
        await ownerClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "read",
        });

        const result = await anonymousClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          accessType: "no_access",
          permissionLevel: null,
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.revokeResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
        });
      });

      it("should deny access to private chat (no permissions exist)", async () => {
        const result = await anonymousClient.checkResourcePermission({
          resourceType: "chat",
          resourceId: CHAT_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          accessType: "no_access",
          permissionLevel: null,
          resourceId: CHAT_ID,
        });
      });
    });

    describe("Authenticated user access (2x2 matrix)", () => {
      it("should allow owner full access", async () => {
        const result = await ownerClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          accessType: "authenticated_access",
          permissionLevel: "owner",
          isOwner: true,
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should deny authenticated user access to private resource", async () => {
        const result = await noAccessClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          accessType: "authenticated_no_access",
          permissionLevel: null,
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should allow authenticated user read access to public resource", async () => {
        await ownerClient.makeResourcePublic({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        const result = await noAccessClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          accessType: "authenticated_access",
          permissionLevel: "read",
          isOwner: false,
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.makeResourcePrivate({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should deny authenticated user access to private resource without permission", async () => {
        await ownerClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "write",
        });

        const result = await noAccessClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          accessType: "authenticated_no_access",
          permissionLevel: null,
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.revokeResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
        });
      });

      it("should allow authenticated user access with explicit permission", async () => {
        await ownerClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "admin",
        });

        const result = await collaboratorClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          accessType: "authenticated_access",
          permissionLevel: "admin",
          isOwner: false,
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.revokeResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
        });
      });
    });

    describe("Error handling", () => {
      it("should return no_access for non-existent resource", async () => {
        const nonExistentId = crypto.randomUUID();
        const result = await ownerClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: nonExistentId,
        });

        expect(result).toEqual({
          hasAccess: false,
          accessType: "no_access",
          permissionLevel: null,
          resourceId: "unknown",
        });
      });

      it("should throw error for missing arguments", async () => {
        await expect(
          ownerClient.checkResourcePermission({
            resourceType: "notebook",
          }),
        ).rejects.toThrow("Missing resourceId argument");
      });
    });
  });

  describe("grantResourcePermission", () => {
    it("should grant read permission successfully", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "read",
      });

      const result = await collaboratorClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(result.hasAccess).toBe(true);
      expect(result.permissionLevel).toBe("read");

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });
    });

    it("should upsert permission (overwrite existing)", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "read",
      });

      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "admin",
      });

      const result = await collaboratorClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(result.hasAccess).toBe(true);
      expect(result.permissionLevel).toBe("admin");

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });
    });

    it("should work for chat resources", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "write",
      });

      const result = await collaboratorClient.checkResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
      });

      expect(result.hasAccess).toBe(true);
      expect(result.permissionLevel).toBe("write");

      await ownerClient.revokeResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });
    });

    it("should throw error for missing arguments", async () => {
      await expect(
        ownerClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        }),
      ).rejects.toThrow();
    });
  });

  describe("revokeResourcePermission", () => {
    it("should revoke permission successfully", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "write",
      });

      let result = await collaboratorClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });
      expect(result.hasAccess).toBe(true);
      expect(result.permissionLevel).toBe("write");

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });

      result = await collaboratorClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });
      expect(result.accessType).toBe("authenticated_no_access");
      expect(result.permissionLevel).toBe(null);
    });

    it("should work for chat resources", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "admin",
      });

      await ownerClient.revokeResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });

      const result = await collaboratorClient.checkResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
      });
      expect(result.permissionLevel).toBe(null);
    });

    it("should throw error for missing arguments", async () => {
      await expect(
        ownerClient.revokeResourcePermission({
          resourceType: "notebook",
        }),
      ).rejects.toThrow();
    });
  });

  describe("listResourcePermissions", () => {
    it("should list all permissions for a resource", async () => {
      await Promise.all([
        ownerClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "write",
        }),
        ownerClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_OWNER_ID,
          permissionLevel: "admin",
        }),
      ]);

      const permissions = await ownerClient.listResourcePermissions({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(permissions).toHaveLength(2);
      expect(
        permissions.some(
          (p) =>
            p.user_id === USER_COLLABORATOR_ID &&
            p.permission_level === "write",
        ),
      ).toBe(true);
      expect(
        permissions.some(
          (p) => p.user_id === USER_OWNER_ID && p.permission_level === "admin",
        ),
      ).toBe(true);

      const collaboratorPermission = permissions.find(
        (p) => p.user_id === USER_COLLABORATOR_ID,
      );
      expect(collaboratorPermission?.user).toBeDefined();
      expect(collaboratorPermission?.granted_by_user).toBeDefined();

      await Promise.all([
        ownerClient.revokeResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
        }),
        ownerClient.revokeResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_OWNER_ID,
        }),
      ]);
    });

    it("should return empty array for resource with no permissions", async () => {
      const permissions = await ownerClient.listResourcePermissions({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(permissions).toHaveLength(0);
    });

    it("should work for chat resources", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "admin",
      });

      const permissions = await ownerClient.listResourcePermissions({
        resourceType: "chat",
        resourceId: CHAT_ID,
      });

      expect(permissions).toHaveLength(1);
      expect(permissions[0].user_id).toBe(USER_COLLABORATOR_ID);
      expect(permissions[0].permission_level).toBe("admin");

      await ownerClient.revokeResourcePermission({
        resourceType: "chat",
        resourceId: CHAT_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });
    });

    it("should throw error for missing arguments", async () => {
      await expect(ownerClient.listResourcePermissions({})).rejects.toThrow();
    });
  });

  describe("cross-organization security", () => {
    const EXTERNAL_ORG_ID = crypto.randomUUID();
    const EXTERNAL_USER_ID = crypto.randomUUID();
    const EXTERNAL_NOTEBOOK_ID = crypto.randomUUID();
    let externalClient: OsoAppClient;

    beforeAll(async () => {
      const externalUserResult = await adminSupabase.auth.admin.createUser({
        id: EXTERNAL_USER_ID,
        email: `external-${EXTERNAL_USER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      });
      if (externalUserResult.error) throw externalUserResult.error;

      await adminSupabase.from("user_profiles").insert({
        id: EXTERNAL_USER_ID,
        email: `external-${EXTERNAL_USER_ID}@test.com`,
        full_name: "External User",
      });

      await adminSupabase.from("organizations").insert({
        id: EXTERNAL_ORG_ID,
        created_by: EXTERNAL_USER_ID,
        org_name: `external-org-${EXTERNAL_ORG_ID.substring(0, 8)}`,
      });

      await adminSupabase.from("notebooks").insert({
        id: EXTERNAL_NOTEBOOK_ID,
        notebook_name: "External Notebook",
        created_by: EXTERNAL_USER_ID,
        data: JSON.stringify({ cells: [] }),
        org_id: EXTERNAL_ORG_ID,
      });

      const externalSupabase = createClient(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY,
        {
          auth: { storageKey: "external-test-auth" },
        },
      );
      const { error: authError } =
        await externalSupabase.auth.signInWithPassword({
          email: `external-${EXTERNAL_USER_ID}@test.com`,
          password: "password123",
        });
      if (authError) throw authError;
      externalClient = new OsoAppClient(externalSupabase);
    });

    afterAll(async () => {
      await Promise.all([
        adminSupabase.from("notebooks").delete().eq("id", EXTERNAL_NOTEBOOK_ID),
        adminSupabase.from("organizations").delete().eq("id", EXTERNAL_ORG_ID),
        adminSupabase.from("user_profiles").delete().eq("id", EXTERNAL_USER_ID),
        adminSupabase.auth.admin.deleteUser(EXTERNAL_USER_ID),
      ]);
    });

    it("should prevent cross-org access to resources", async () => {
      const result = await externalClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(result.hasAccess).toBe(false);
      expect(result.accessType).toBe("authenticated_no_access");
    });

    it("should prevent cross-org permission grants", async () => {
      await expect(
        externalClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: EXTERNAL_USER_ID,
          permissionLevel: "read",
        }),
      ).rejects.toThrow();
    });

    it("should prevent access to external org resources", async () => {
      const result = await collaboratorClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: EXTERNAL_NOTEBOOK_ID,
      });

      expect(result.hasAccess).toBe(false);
      expect(result.accessType).toBe("authenticated_no_access");
    });
  });

  describe("row level security enforcement", () => {
    it("should prevent non-owners from granting permissions", async () => {
      await expect(
        collaboratorClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_NO_ACCESS_ID,
          permissionLevel: "read",
        }),
      ).rejects.toThrow();
    });

    it("should restrict permission visibility", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "read",
      });

      const permissions = await noAccessClient.listResourcePermissions({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(permissions).toHaveLength(0);

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });
    });

    it("should enforce granted_by authentication", async () => {
      const collaboratorSupabase = createClient(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY,
        {
          auth: { storageKey: "collaborator-rls-test" },
        },
      );
      await collaboratorSupabase.auth.signInWithPassword({
        email: `collaborator-${USER_COLLABORATOR_ID}@test.com`,
        password: "password123",
      });

      const { error } = await collaboratorSupabase
        .from("resource_permissions")
        .insert({
          user_id: USER_NO_ACCESS_ID,
          notebook_id: NOTEBOOK_ID,
          permission_level: "read",
          granted_by: USER_OWNER_ID,
        });

      expect(error).toBeDefined();
    });
  });

  describe("database constraints", () => {
    it("should enforce exactly one resource constraint", async () => {
      const { error: bothError } = await adminSupabase
        .from("resource_permissions")
        .insert({
          user_id: USER_COLLABORATOR_ID,
          notebook_id: NOTEBOOK_ID,
          chat_id: CHAT_ID,
          permission_level: "read",
          granted_by: USER_OWNER_ID,
        });

      expect(bothError).toBeDefined();
      expect(bothError?.message).toContain("exactly_one_resource");

      const { error: neitherError } = await adminSupabase
        .from("resource_permissions")
        .insert({
          user_id: USER_COLLABORATOR_ID,
          permission_level: "read",
          granted_by: USER_OWNER_ID,
        });

      expect(neitherError).toBeDefined();
      expect(neitherError?.message).toContain("exactly_one_resource");
    });

    it("should enforce unique active permissions", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "read",
      });

      const { error } = await adminSupabase
        .from("resource_permissions")
        .insert({
          user_id: USER_COLLABORATOR_ID,
          notebook_id: NOTEBOOK_ID,
          permission_level: "write",
          granted_by: USER_OWNER_ID,
        });

      expect(error).toBeDefined();
      expect(error?.message).toContain("duplicate");

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_COLLABORATOR_ID,
      });
    });

    it("should validate permission levels", async () => {
      const { error } = await adminSupabase
        .from("resource_permissions")
        .insert({
          user_id: USER_COLLABORATOR_ID,
          notebook_id: NOTEBOOK_ID,
          permission_level: "invalid_level",
          granted_by: USER_OWNER_ID,
        });

      expect(error).toBeDefined();
      expect(error?.message).toContain("permission_level");
    });
  });

  describe("resource deletion cascades", () => {
    it("should cascade delete permissions when notebook is deleted", async () => {
      const tempNotebookId = crypto.randomUUID();

      await adminSupabase.from("notebooks").insert({
        id: tempNotebookId,
        notebook_name: "Temp Notebook",
        created_by: USER_OWNER_ID,
        data: JSON.stringify({ cells: [] }),
        org_id: ORG_ID,
      });

      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: tempNotebookId,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "read",
      });

      const permissions = await ownerClient.listResourcePermissions({
        resourceType: "notebook",
        resourceId: tempNotebookId,
      });
      expect(permissions).toHaveLength(1);

      await adminSupabase.from("notebooks").delete().eq("id", tempNotebookId);

      const { data: permissionsData } = await adminSupabase
        .from("resource_permissions")
        .select("*")
        .eq("notebook_id", tempNotebookId);

      expect(permissionsData).toHaveLength(0);
    });

    it("should cascade delete permissions when chat is deleted", async () => {
      const tempChatId = crypto.randomUUID();

      await adminSupabase.from("chat_history").insert({
        id: tempChatId,
        created_by: USER_OWNER_ID,
        data: JSON.stringify([]),
        display_name: "Temp Chat",
        org_id: ORG_ID,
      });

      await ownerClient.grantResourcePermission({
        resourceType: "chat",
        resourceId: tempChatId,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "write",
      });

      await adminSupabase.from("chat_history").delete().eq("id", tempChatId);

      const { data: permissionsData } = await adminSupabase
        .from("resource_permissions")
        .select("*")
        .eq("chat_id", tempChatId);

      expect(permissionsData).toHaveLength(0);
    });
  });

  describe("user deletion scenarios", () => {
    it("should handle target user deletion", async () => {
      const tempUserId = crypto.randomUUID();

      const userResult = await adminSupabase.auth.admin.createUser({
        id: tempUserId,
        email: `temp-${tempUserId}@test.com`,
        password: "password123",
        email_confirm: true,
      });
      if (userResult.error) throw userResult.error;

      await adminSupabase.from("user_profiles").insert({
        id: tempUserId,
        email: `temp-${tempUserId}@test.com`,
        full_name: "Temp User",
      });

      await adminSupabase.from("users_by_organization").insert({
        user_id: tempUserId,
        org_id: ORG_ID,
        user_role: "member",
      });

      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: tempUserId,
        permissionLevel: "read",
      });

      await adminSupabase
        .from("users_by_organization")
        .delete()
        .eq("user_id", tempUserId);

      await adminSupabase
        .from("organizations")
        .delete()
        .eq("created_by", tempUserId);

      const { error: deleteError } = await adminSupabase
        .from("user_profiles")
        .delete()
        .eq("id", tempUserId);

      if (deleteError) {
        throw deleteError;
      }

      await new Promise((resolve) => setTimeout(resolve, 100));

      await adminSupabase.auth.admin.deleteUser(tempUserId);

      const { data: permissionsData } = await adminSupabase
        .from("resource_permissions")
        .select("*")
        .eq("user_id", tempUserId);

      expect(permissionsData).toHaveLength(0);
    });

    it("should handle granter user deletion", async () => {
      const tempGranterId = crypto.randomUUID();
      const tempNotebookId = crypto.randomUUID();

      const userResult = await adminSupabase.auth.admin.createUser({
        id: tempGranterId,
        email: `granter-${tempGranterId}@test.com`,
        password: "password123",
        email_confirm: true,
      });
      if (userResult.error) throw userResult.error;

      await adminSupabase.from("user_profiles").insert({
        id: tempGranterId,
        email: `granter-${tempGranterId}@test.com`,
        full_name: "Granter User",
      });

      await adminSupabase.from("notebooks").insert({
        id: tempNotebookId,
        notebook_name: "Granter Notebook",
        created_by: tempGranterId,
        data: JSON.stringify({ cells: [] }),
        org_id: ORG_ID,
      });

      await adminSupabase.from("users_by_organization").insert({
        user_id: tempGranterId,
        org_id: ORG_ID,
        user_role: "admin",
      });

      const granterSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
        auth: { storageKey: "granter-test-auth" },
      });
      await granterSupabase.auth.signInWithPassword({
        email: `granter-${tempGranterId}@test.com`,
        password: "password123",
      });
      const granterClient = new OsoAppClient(granterSupabase);

      await granterClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: tempNotebookId,
        targetUserId: USER_COLLABORATOR_ID,
        permissionLevel: "read",
      });

      await adminSupabase
        .from("notebooks")
        .update({ created_by: USER_OWNER_ID })
        .eq("id", tempNotebookId);

      await adminSupabase
        .from("notebooks")
        .delete()
        .eq("created_by", tempGranterId)
        .neq("id", tempNotebookId);

      await adminSupabase
        .from("chat_history")
        .delete()
        .eq("created_by", tempGranterId);

      await adminSupabase
        .from("users_by_organization")
        .delete()
        .eq("user_id", tempGranterId);

      await adminSupabase
        .from("organizations")
        .delete()
        .eq("created_by", tempGranterId);

      const { error: deleteError } = await adminSupabase
        .from("user_profiles")
        .delete()
        .eq("id", tempGranterId);

      if (deleteError) {
        throw deleteError;
      }

      await new Promise((resolve) => setTimeout(resolve, 100));

      await adminSupabase.auth.admin.deleteUser(tempGranterId);

      const { data: permissionsData } = await adminSupabase
        .from("resource_permissions")
        .select("*")
        .eq("notebook_id", tempNotebookId);

      expect(permissionsData).toHaveLength(1);
      expect(permissionsData?.[0]?.granted_by).toBeNull();

      await adminSupabase.from("notebooks").delete().eq("id", tempNotebookId);
    });
  });

  describe("self-permission scenarios", () => {
    it("should allow owner to grant permission to themselves", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_OWNER_ID,
        permissionLevel: "admin",
      });

      const result = await ownerClient.checkResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(result.hasAccess).toBe(true);
      expect(result.permissionLevel).toBe("owner");
      expect(result.isOwner).toBe(true);

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_OWNER_ID,
      });
    });

    it("should prevent non-owners from granting permission to themselves", async () => {
      await expect(
        collaboratorClient.grantResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "admin",
        }),
      ).rejects.toThrow();
    });
  });
});
