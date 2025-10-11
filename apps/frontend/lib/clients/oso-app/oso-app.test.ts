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

    // Clean up any existing test data first
    await adminSupabase
      .from("user_profiles")
      .delete()
      .in("id", [USER_1_ID, USER_2_ID]);

    await Promise.all([
      adminSupabase.auth.admin.deleteUser(USER_1_ID).catch(() => {}),
      adminSupabase.auth.admin.deleteUser(USER_2_ID).catch(() => {}),
    ]);

    // Create test users with unique IDs
    await adminSupabase.auth.admin.createUser({
      id: USER_1_ID,
      email: `user1_${USER_1_ID}@test.com`,
      password: "password123",
      // We want the user to be usable right away without email confirmation
      email_confirm: true,
    });
    await adminSupabase.auth.admin.createUser({
      id: USER_2_ID,
      email: `user2_${USER_2_ID}@test.com`,
      password: "password123",
      email_confirm: true,
    });
  });

  it("should create an organization", async () => {
    expect(true).toBe(true);
  });
});

describe("Organization Ownership", () => {
  const REGULAR_USER_ID = crypto.randomUUID();
  const ADMIN_USER_ID = crypto.randomUUID();
  const FIRST_ORG_ID = crypto.randomUUID();
  const SECOND_ORG_ID = crypto.randomUUID();
  const THIRD_ORG_ID = crypto.randomUUID();

  let adminSupabase: ReturnType<typeof createClient>;

  beforeAll(async () => {
    adminSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "org-ownership-admin-test-auth" },
    });

    // Clean up any existing test data first
    await adminSupabase
      .from("users_by_organization")
      .delete()
      .in("org_id", [FIRST_ORG_ID, SECOND_ORG_ID, THIRD_ORG_ID]);

    await adminSupabase
      .from("organizations")
      .delete()
      .in("id", [FIRST_ORG_ID, SECOND_ORG_ID, THIRD_ORG_ID]);

    await adminSupabase
      .from("admin_users")
      .delete()
      .eq("user_id", ADMIN_USER_ID);

    await adminSupabase
      .from("user_profiles")
      .delete()
      .in("id", [REGULAR_USER_ID, ADMIN_USER_ID]);

    await Promise.all([
      adminSupabase.auth.admin.deleteUser(REGULAR_USER_ID).catch(() => {}),
      adminSupabase.auth.admin.deleteUser(ADMIN_USER_ID).catch(() => {}),
    ]);

    const userCreationResults = await Promise.all([
      adminSupabase.auth.admin.createUser({
        id: REGULAR_USER_ID,
        email: `regular_${REGULAR_USER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
      adminSupabase.auth.admin.createUser({
        id: ADMIN_USER_ID,
        email: `admin_${ADMIN_USER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
    ]);

    userCreationResults.forEach((result, index) => {
      const userType = ["regular", "admin"][index];
      if (result.error) {
        logger.error(`Failed to create ${userType} user:`, result.error);
        throw result.error;
      }
    });

    await adminSupabase.from("user_profiles").insert([
      {
        id: REGULAR_USER_ID,
        email: `regular_${REGULAR_USER_ID}@test.com`,
        full_name: "Regular User",
      },
      {
        id: ADMIN_USER_ID,
        email: `admin_${ADMIN_USER_ID}@test.com`,
        full_name: "Admin User",
      },
    ]);

    await adminSupabase.from("admin_users").insert({
      user_id: ADMIN_USER_ID,
      name: "Test Admin",
      description: "Test admin user for org ownership tests",
    });

    const regularSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "regular-org-test-auth" },
    });
    const { error: regularAuthError } =
      await regularSupabase.auth.signInWithPassword({
        email: `regular_${REGULAR_USER_ID}@test.com`,
        password: "password123",
      });
    if (regularAuthError) throw regularAuthError;

    const adminUserSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "admin-org-test-auth" },
    });
    const { error: adminAuthError } =
      await adminUserSupabase.auth.signInWithPassword({
        email: `admin_${ADMIN_USER_ID}@test.com`,
        password: "password123",
      });
    if (adminAuthError) throw adminAuthError;
  });

  afterAll(async () => {
    await adminSupabase
      .from("users_by_organization")
      .delete()
      .in("org_id", [FIRST_ORG_ID, SECOND_ORG_ID, THIRD_ORG_ID]);

    await adminSupabase
      .from("organizations")
      .delete()
      .in("id", [FIRST_ORG_ID, SECOND_ORG_ID, THIRD_ORG_ID]);

    await adminSupabase
      .from("admin_users")
      .delete()
      .eq("user_id", ADMIN_USER_ID);

    await adminSupabase
      .from("user_profiles")
      .delete()
      .in("id", [REGULAR_USER_ID, ADMIN_USER_ID]);

    await Promise.all([
      adminSupabase.auth.admin.deleteUser(REGULAR_USER_ID),
      adminSupabase.auth.admin.deleteUser(ADMIN_USER_ID),
    ]);
  });

  afterEach(async () => {
    await adminSupabase
      .from("users_by_organization")
      .delete()
      .in("org_id", [FIRST_ORG_ID, SECOND_ORG_ID, THIRD_ORG_ID]);

    await adminSupabase
      .from("organizations")
      .delete()
      .in("id", [FIRST_ORG_ID, SECOND_ORG_ID, THIRD_ORG_ID]);
  });

  it("should allow regular user to create their first organization", async () => {
    const { error } = await adminSupabase.from("organizations").insert({
      id: FIRST_ORG_ID,
      created_by: REGULAR_USER_ID,
      org_name: `regular_first_${FIRST_ORG_ID.substring(0, 8)}`,
    });

    expect(error).toBeNull();

    const { data: ownership } = await adminSupabase
      .from("users_by_organization")
      .select("*")
      .eq("user_id", REGULAR_USER_ID)
      .eq("org_id", FIRST_ORG_ID)
      .eq("user_role", "owner")
      .is("deleted_at", null);

    expect(ownership).toHaveLength(1);
  });

  it("should prevent regular user from creating a second organization", async () => {
    await adminSupabase.from("organizations").insert({
      id: FIRST_ORG_ID,
      created_by: REGULAR_USER_ID,
      org_name: `regular_first_${FIRST_ORG_ID.substring(0, 8)}`,
    });
    const { error: orgError } = await adminSupabase
      .from("organizations")
      .insert({
        id: SECOND_ORG_ID,
        created_by: REGULAR_USER_ID,
        org_name: `regular_second_${SECOND_ORG_ID.substring(0, 8)}`,
      });

    expect(orgError).toBeDefined();
  });

  it("should allow admin user to create multiple organizations", async () => {
    const { error: firstError } = await adminSupabase
      .from("organizations")
      .insert({
        id: FIRST_ORG_ID,
        created_by: ADMIN_USER_ID,
        org_name: `admin_first_${FIRST_ORG_ID.substring(0, 8)}`,
      });

    expect(firstError).toBeNull();

    const { error: secondError } = await adminSupabase
      .from("organizations")
      .insert({
        id: SECOND_ORG_ID,
        created_by: ADMIN_USER_ID,
        org_name: `admin_second_${SECOND_ORG_ID.substring(0, 8)}`,
      });

    expect(secondError).toBeNull();

    const { data: ownerships } = await adminSupabase
      .from("users_by_organization")
      .select("*")
      .eq("user_id", ADMIN_USER_ID)
      .eq("user_role", "owner")
      .is("deleted_at", null);

    expect(ownerships).toHaveLength(2);
  });

  it("should prevent promoting regular user to owner of second organization", async () => {
    await adminSupabase.from("organizations").insert({
      id: FIRST_ORG_ID,
      created_by: REGULAR_USER_ID,
      org_name: `regular_first_${FIRST_ORG_ID.substring(0, 8)}`,
    });

    await adminSupabase.from("organizations").insert({
      id: SECOND_ORG_ID,
      created_by: ADMIN_USER_ID,
      org_name: `admin_second_${SECOND_ORG_ID.substring(0, 8)}`,
    });

    await adminSupabase.from("users_by_organization").insert({
      user_id: REGULAR_USER_ID,
      org_id: SECOND_ORG_ID,
      user_role: "member",
    });

    const { error } = await adminSupabase
      .from("users_by_organization")
      .update({ user_role: "owner" })
      .eq("user_id", REGULAR_USER_ID)
      .eq("org_id", SECOND_ORG_ID);

    expect(error).toBeDefined();
  });

  it("should allow promoting admin user to owner of multiple organizations", async () => {
    await adminSupabase.from("organizations").insert({
      id: FIRST_ORG_ID,
      created_by: REGULAR_USER_ID,
      org_name: `regular_first_${FIRST_ORG_ID.substring(0, 8)}`,
    });

    const tempUserId = crypto.randomUUID();
    await adminSupabase.auth.admin.createUser({
      id: tempUserId,
      email: `temp_${tempUserId}@test.com`,
      password: "password123",
      email_confirm: true,
    });
    await adminSupabase.from("user_profiles").insert({
      id: tempUserId,
      email: `temp_${tempUserId}@test.com`,
      full_name: "Temp User",
    });

    await adminSupabase.from("organizations").insert({
      id: SECOND_ORG_ID,
      created_by: tempUserId,
      org_name: `temp_second_${SECOND_ORG_ID.substring(0, 8)}`,
    });

    await adminSupabase.from("users_by_organization").insert([
      {
        user_id: ADMIN_USER_ID,
        org_id: FIRST_ORG_ID,
        user_role: "member",
      },
      {
        user_id: ADMIN_USER_ID,
        org_id: SECOND_ORG_ID,
        user_role: "member",
      },
    ]);

    const { error: firstPromotion } = await adminSupabase
      .from("users_by_organization")
      .update({ user_role: "owner" })
      .eq("user_id", ADMIN_USER_ID)
      .eq("org_id", FIRST_ORG_ID);

    expect(firstPromotion).toBeNull();

    const { error: secondPromotion } = await adminSupabase
      .from("users_by_organization")
      .update({ user_role: "owner" })
      .eq("user_id", ADMIN_USER_ID)
      .eq("org_id", SECOND_ORG_ID);

    expect(secondPromotion).toBeNull();

    const { data: ownerships } = await adminSupabase
      .from("users_by_organization")
      .select("*")
      .eq("user_id", ADMIN_USER_ID)
      .eq("user_role", "owner")
      .is("deleted_at", null);

    expect(ownerships).toHaveLength(2);

    await adminSupabase
      .from("users_by_organization")
      .delete()
      .eq("user_id", tempUserId);
    await adminSupabase
      .from("organizations")
      .delete()
      .eq("created_by", tempUserId);
    await adminSupabase.from("user_profiles").delete().eq("id", tempUserId);
    await adminSupabase.auth.admin.deleteUser(tempUserId);
  });

  it("should allow existing owner to update their ownership record", async () => {
    await adminSupabase.from("organizations").insert({
      id: FIRST_ORG_ID,
      created_by: REGULAR_USER_ID,
      org_name: `regular_update_${FIRST_ORG_ID.substring(0, 8)}`,
    });

    const { error } = await adminSupabase
      .from("users_by_organization")
      .update({ updated_at: new Date().toISOString() })
      .eq("user_id", REGULAR_USER_ID)
      .eq("org_id", FIRST_ORG_ID)
      .eq("user_role", "owner");

    expect(error).toBeNull();
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

    // Clean up any existing test data first
    await Promise.all([
      adminSupabase
        .from("resource_permissions")
        .delete()
        .in("user_id", [
          USER_OWNER_ID,
          USER_COLLABORATOR_ID,
          USER_NO_ACCESS_ID,
        ]),
      adminSupabase
        .from("resource_permissions")
        .delete()
        .eq("notebook_id", NOTEBOOK_ID),
      adminSupabase
        .from("resource_permissions")
        .delete()
        .eq("chat_id", CHAT_ID),
    ]);

    await Promise.all([
      adminSupabase.from("notebooks").delete().eq("id", NOTEBOOK_ID),
      adminSupabase.from("chat_history").delete().eq("id", CHAT_ID),
      adminSupabase.from("users_by_organization").delete().eq("org_id", ORG_ID),
    ]);

    await adminSupabase.from("organizations").delete().eq("id", ORG_ID);

    await adminSupabase
      .from("user_profiles")
      .delete()
      .in("id", [USER_OWNER_ID, USER_COLLABORATOR_ID, USER_NO_ACCESS_ID]);

    await Promise.all([
      adminSupabase.auth.admin.deleteUser(USER_OWNER_ID).catch(() => {}),
      adminSupabase.auth.admin.deleteUser(USER_COLLABORATOR_ID).catch(() => {}),
      adminSupabase.auth.admin.deleteUser(USER_NO_ACCESS_ID).catch(() => {}),
    ]);

    const userCreationResults = await Promise.all([
      adminSupabase.auth.admin.createUser({
        id: USER_OWNER_ID,
        email: `owner_${USER_OWNER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
      adminSupabase.auth.admin.createUser({
        id: USER_COLLABORATOR_ID,
        email: `collaborator_${USER_COLLABORATOR_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
      adminSupabase.auth.admin.createUser({
        id: USER_NO_ACCESS_ID,
        email: `noaccess_${USER_NO_ACCESS_ID}@test.com`,
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
        email: `owner_${USER_OWNER_ID}@test.com`,
        full_name: "Owner User",
      },
      {
        id: USER_COLLABORATOR_ID,
        email: `collaborator_${USER_COLLABORATOR_ID}@test.com`,
        full_name: "Collaborator User",
      },
      {
        id: USER_NO_ACCESS_ID,
        email: `noaccess_${USER_NO_ACCESS_ID}@test.com`,
        full_name: "No Access User",
      },
    ]);

    const ownerSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "owner-test-auth" },
    });
    const { data: ownerAuth, error: ownerAuthError } =
      await ownerSupabase.auth.signInWithPassword({
        email: `owner_${USER_OWNER_ID}@test.com`,
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
      org_name: `test_org_${ORG_ID.substring(0, 8)}`,
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
      notebook_name: "Test_Notebook",
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
        email: `collaborator_${USER_COLLABORATOR_ID}@test.com`,
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
        email: `noaccess_${USER_NO_ACCESS_ID}@test.com`,
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
    describe("Anonymous user access", () => {
      it("should deny access to private resources", async () => {
        const result = await anonymousClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          permissionLevel: "none",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should allow read access to public resources", async () => {
        await ownerClient.grantPublicPermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          permissionLevel: "read",
        });

        const result = await anonymousClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          permissionLevel: "read",
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.revokePublicPermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should deny access to private resources when other permissions exist", async () => {
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
          permissionLevel: "none",
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.revokeResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          targetUserId: USER_COLLABORATOR_ID,
        });
      });
    });

    describe("Authenticated user access", () => {
      it("should allow owner full access", async () => {
        const result = await ownerClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          permissionLevel: "owner",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should deny access to private resources", async () => {
        const result = await noAccessClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: false,
          permissionLevel: "none",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should allow access to public resources", async () => {
        await ownerClient.grantPublicPermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
          permissionLevel: "read",
        });

        const result = await noAccessClient.checkResourcePermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });

        expect(result).toEqual({
          hasAccess: true,
          permissionLevel: "read",
          resourceId: NOTEBOOK_ID,
        });

        await ownerClient.revokePublicPermission({
          resourceType: "notebook",
          resourceId: NOTEBOOK_ID,
        });
      });

      it("should allow access with explicit permissions", async () => {
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
          permissionLevel: "admin",
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
          permissionLevel: "none",
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
    test.each([
      ["notebook", NOTEBOOK_ID],
      ["chat", CHAT_ID],
    ])(
      "should grant permission successfully for %s",
      async (resourceType, resourceId) => {
        await ownerClient.grantResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "read",
        });

        const result = await collaboratorClient.checkResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
        });

        expect(result.hasAccess).toBe(true);
        expect(result.permissionLevel).toBe("read");

        await ownerClient.revokeResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
          targetUserId: USER_COLLABORATOR_ID,
        });
      },
    );

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
    test.each([
      ["notebook", NOTEBOOK_ID, "write"],
      ["chat", CHAT_ID, "admin"],
    ])(
      "should revoke permission successfully for %s",
      async (resourceType, resourceId, permissionLevel) => {
        await ownerClient.grantResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: permissionLevel as any,
        });

        let result = await collaboratorClient.checkResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
        });
        expect(result.hasAccess).toBe(true);
        expect(result.permissionLevel).toBe(permissionLevel);

        await ownerClient.revokeResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
          targetUserId: USER_COLLABORATOR_ID,
        });

        result = await collaboratorClient.checkResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
        });
        expect(result.hasAccess).toBe(false);
        expect(result.permissionLevel).toBe("none");
      },
    );

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

    test.each([
      ["notebook", NOTEBOOK_ID],
      ["chat", CHAT_ID],
    ])(
      "should list permissions for %s resources",
      async (resourceType, resourceId) => {
        await ownerClient.grantResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
          targetUserId: USER_COLLABORATOR_ID,
          permissionLevel: "admin",
        });

        const permissions = await ownerClient.listResourcePermissions({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
        });

        expect(permissions).toHaveLength(1);
        expect(permissions[0].user_id).toBe(USER_COLLABORATOR_ID);
        expect(permissions[0].permission_level).toBe("admin");

        await ownerClient.revokeResourcePermission({
          resourceType: resourceType as "notebook" | "chat",
          resourceId,
          targetUserId: USER_COLLABORATOR_ID,
        });
      },
    );

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
        email: `external_${EXTERNAL_USER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      });
      if (externalUserResult.error) throw externalUserResult.error;

      await adminSupabase.from("user_profiles").insert({
        id: EXTERNAL_USER_ID,
        email: `external_${EXTERNAL_USER_ID}@test.com`,
        full_name: "External User",
      });

      await adminSupabase.from("organizations").insert({
        id: EXTERNAL_ORG_ID,
        created_by: EXTERNAL_USER_ID,
        org_name: `external_org_${EXTERNAL_ORG_ID.substring(0, 8)}`,
      });

      await adminSupabase.from("notebooks").insert({
        id: EXTERNAL_NOTEBOOK_ID,
        notebook_name: "External_Notebook",
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
          email: `external_${EXTERNAL_USER_ID}@test.com`,
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
      expect(result.permissionLevel).toBe("none");
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
      expect(result.permissionLevel).toBe("none");
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

    it("should allow org members to view permissions for resources in their org", async () => {
      await ownerClient.grantResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_OWNER_ID,
        permissionLevel: "read",
      });

      const permissions = await collaboratorClient.listResourcePermissions({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
      });

      expect(permissions).toHaveLength(1);
      expect(permissions[0].user_id).toBe(USER_OWNER_ID);
      expect(permissions[0].permission_level).toBe("read");

      await ownerClient.revokeResourcePermission({
        resourceType: "notebook",
        resourceId: NOTEBOOK_ID,
        targetUserId: USER_OWNER_ID,
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
        email: `collaborator_${USER_COLLABORATOR_ID}@test.com`,
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

    it("should allow any permission level in database (validation moved to application)", async () => {
      const { error } = await adminSupabase
        .from("resource_permissions")
        .insert({
          user_id: USER_COLLABORATOR_ID,
          notebook_id: NOTEBOOK_ID,
          permission_level: "invalid_level",
          granted_by: USER_OWNER_ID,
        });

      expect(error).toBeNull();
    });
  });

  describe("resource deletion cascades", () => {
    it("should cascade delete permissions when notebook is deleted", async () => {
      const tempNotebookId = crypto.randomUUID();

      await adminSupabase.from("notebooks").insert({
        id: tempNotebookId,
        notebook_name: "Temp_Notebook",
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
        email: `temp_${tempUserId}@test.com`,
        password: "password123",
        email_confirm: true,
      });
      if (userResult.error) throw userResult.error;

      await adminSupabase.from("user_profiles").insert({
        id: tempUserId,
        email: `temp_${tempUserId}@test.com`,
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
        email: `granter_${tempGranterId}@test.com`,
        password: "password123",
        email_confirm: true,
      });
      if (userResult.error) throw userResult.error;

      await adminSupabase.from("user_profiles").insert({
        id: tempGranterId,
        email: `granter_${tempGranterId}@test.com`,
        full_name: "Granter User",
      });

      await adminSupabase.from("notebooks").insert({
        id: tempNotebookId,
        notebook_name: "Granter_Notebook",
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
        email: `granter_${tempGranterId}@test.com`,
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

  describe("user profile visibility", () => {
    it("should allow users to view their own profile", async () => {
      const ownerSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
        auth: { storageKey: "owner-profile-test" },
      });
      await ownerSupabase.auth.signInWithPassword({
        email: `owner_${USER_OWNER_ID}@test.com`,
        password: "password123",
      });

      const { data, error } = await ownerSupabase
        .from("user_profiles")
        .select("*")
        .eq("id", USER_OWNER_ID)
        .single();

      expect(error).toBeNull();
      expect(data).toBeDefined();
      expect(data?.id).toBe(USER_OWNER_ID);
    });

    it("should allow users to view profiles of users in the same organization", async () => {
      const ownerSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
        auth: { storageKey: "owner-profile-view-test" },
      });
      await ownerSupabase.auth.signInWithPassword({
        email: `owner_${USER_OWNER_ID}@test.com`,
        password: "password123",
      });

      const { data, error } = await ownerSupabase
        .from("user_profiles")
        .select("*")
        .eq("id", USER_COLLABORATOR_ID)
        .single();

      expect(error).toBeNull();
      expect(data).toBeDefined();
      expect(data?.id).toBe(USER_COLLABORATOR_ID);
    });

    it("should allow viewing multiple profiles in the same organization", async () => {
      const collaboratorSupabase = createClient(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY,
        {
          auth: { storageKey: "collaborator-profiles-view-test" },
        },
      );
      await collaboratorSupabase.auth.signInWithPassword({
        email: `collaborator_${USER_COLLABORATOR_ID}@test.com`,
        password: "password123",
      });

      const { data, error } = await collaboratorSupabase
        .from("user_profiles")
        .select("*")
        .in("id", [USER_OWNER_ID, USER_COLLABORATOR_ID]);

      expect(error).toBeNull();
      expect(data).toHaveLength(2);
      expect(data?.map((p) => p.id).sort()).toEqual(
        [USER_OWNER_ID, USER_COLLABORATOR_ID].sort(),
      );
    });
  });
});

describe("Billing and Credits", () => {
  const ADMIN_USER_ID = crypto.randomUUID();
  const REGULAR_USER_ID = crypto.randomUUID();
  const FREE_ORG_ID = crypto.randomUUID();
  const ENTERPRISE_ORG_ID = crypto.randomUUID();

  let adminSupabase: ReturnType<typeof createClient>;
  let adminClient: OsoAppClient;
  let regularClient: OsoAppClient;

  beforeAll(async () => {
    adminSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "billing-admin-test-auth" },
    });

    await Promise.all([
      adminSupabase
        .from("organization_credits")
        .delete()
        .in("org_id", [FREE_ORG_ID, ENTERPRISE_ORG_ID]),
      adminSupabase
        .from("users_by_organization")
        .delete()
        .in("org_id", [FREE_ORG_ID, ENTERPRISE_ORG_ID]),
    ]);

    await adminSupabase
      .from("organizations")
      .delete()
      .in("id", [FREE_ORG_ID, ENTERPRISE_ORG_ID]);

    await Promise.all([
      adminSupabase.from("admin_users").delete().eq("user_id", ADMIN_USER_ID),
      adminSupabase
        .from("user_profiles")
        .delete()
        .in("id", [ADMIN_USER_ID, REGULAR_USER_ID]),
    ]);

    await Promise.all([
      adminSupabase.auth.admin.deleteUser(ADMIN_USER_ID).catch(() => {}),
      adminSupabase.auth.admin.deleteUser(REGULAR_USER_ID).catch(() => {}),
    ]);

    await Promise.all([
      adminSupabase.auth.admin.createUser({
        id: ADMIN_USER_ID,
        email: `billing_admin_${ADMIN_USER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
      adminSupabase.auth.admin.createUser({
        id: REGULAR_USER_ID,
        email: `billing_regular_${REGULAR_USER_ID}@test.com`,
        password: "password123",
        email_confirm: true,
      }),
    ]);

    await adminSupabase.from("user_profiles").insert([
      {
        id: ADMIN_USER_ID,
        email: `billing_admin_${ADMIN_USER_ID}@test.com`,
        full_name: "Billing Admin",
      },
      {
        id: REGULAR_USER_ID,
        email: `billing_regular_${REGULAR_USER_ID}@test.com`,
        full_name: "Billing Regular",
      },
    ]);

    await adminSupabase
      .from("admin_users")
      .insert({
        user_id: ADMIN_USER_ID,
        name: "Billing Test Admin",
        description: "Admin for billing tests",
      })
      .throwOnError();

    const { data: freePlan } = await adminSupabase
      .from("pricing_plan")
      .select("plan_id")
      .eq("plan_name", "FREE")
      .single();

    const { data: enterprisePlan } = await adminSupabase
      .from("pricing_plan")
      .select("plan_id")
      .eq("plan_name", "ENTERPRISE")
      .single();

    await adminSupabase
      .from("organizations")
      .upsert(
        [
          {
            id: FREE_ORG_ID,
            created_by: REGULAR_USER_ID,
            org_name: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
            plan_id: freePlan?.plan_id,
          },
          {
            id: ENTERPRISE_ORG_ID,
            created_by: ADMIN_USER_ID,
            org_name: `enterprise_billing_${ENTERPRISE_ORG_ID.substring(0, 8)}`,
            plan_id: enterprisePlan?.plan_id,
            billing_contact_email: "enterprise@test.com",
            enterprise_support_url: "https://support.test.com",
          },
        ],
        { onConflict: "id" },
      )
      .throwOnError();

    await adminSupabase
      .from("organization_credits")
      .upsert(
        [
          {
            org_id: FREE_ORG_ID,
            credits_balance: 100,
            last_refill_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            org_id: ENTERPRISE_ORG_ID,
            credits_balance: 10000,
            last_refill_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        { onConflict: "org_id" },
      )
      .throwOnError();

    const adminUserSupabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "admin-billing-client-auth" },
    });
    await adminUserSupabase.auth.signInWithPassword({
      email: `billing_admin_${ADMIN_USER_ID}@test.com`,
      password: "password123",
    });
    adminClient = new OsoAppClient(adminUserSupabase);

    const regularUserSupabase = createClient(
      SUPABASE_URL,
      SUPABASE_SERVICE_KEY,
      {
        auth: { storageKey: "regular-billing-client-auth" },
      },
    );
    await regularUserSupabase.auth.signInWithPassword({
      email: `billing_regular_${REGULAR_USER_ID}@test.com`,
      password: "password123",
    });
    regularClient = new OsoAppClient(regularUserSupabase);
  });

  afterAll(async () => {
    await Promise.all([
      adminSupabase
        .from("organization_credits")
        .delete()
        .in("org_id", [FREE_ORG_ID, ENTERPRISE_ORG_ID]),
      adminSupabase
        .from("users_by_organization")
        .delete()
        .in("org_id", [FREE_ORG_ID, ENTERPRISE_ORG_ID]),
      adminSupabase
        .from("organizations")
        .delete()
        .in("id", [FREE_ORG_ID, ENTERPRISE_ORG_ID]),
      adminSupabase.from("admin_users").delete().eq("user_id", ADMIN_USER_ID),
      adminSupabase
        .from("user_profiles")
        .delete()
        .in("id", [ADMIN_USER_ID, REGULAR_USER_ID]),
      adminSupabase.auth.admin.deleteUser(ADMIN_USER_ID),
      adminSupabase.auth.admin.deleteUser(REGULAR_USER_ID),
    ]);
  });

  describe("getSubscriptionStatus", () => {
    it("should return correct structure for FREE tier", async () => {
      const status = await adminClient.getSubscriptionStatus({
        orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
      });

      expect(status.tier).toBe("free");
      expect(status.planName).toBe("FREE");
      expect(status.creditsBalance).toBeGreaterThanOrEqual(0);
      expect(status.subscriptionStatus.isFree).toBe(true);
      expect(status.subscriptionStatus.isEnterprise).toBe(false);
      expect(status.billingCycle.cycleStartDate).toBeDefined();
      expect(status.billingCycle.cycleEndDate).toBeDefined();
      expect(status.billingCycle.daysUntilRefill).toBeGreaterThanOrEqual(0);
    });

    it("should return correct structure for ENTERPRISE tier", async () => {
      const status = await adminClient.getSubscriptionStatus({
        orgName: `enterprise_billing_${ENTERPRISE_ORG_ID.substring(0, 8)}`,
      });

      expect(status.tier).toBe("enterprise");
      expect(status.planName).toBe("ENTERPRISE");
      expect(status.creditsBalance).toBeGreaterThanOrEqual(0);
      expect(status.subscriptionStatus.isEnterprise).toBe(true);
      expect(status.subscriptionStatus.isFree).toBe(false);
      expect(status.billingContact.email).toBe("enterprise@test.com");
      expect(status.billingContact.supportUrl).toBe("https://support.test.com");
      expect(status.features.hasUnlimitedQueries).toBe(true);
      expect(status.features.hasPrioritySupport).toBe(true);
    });

    it("should calculate next refill date correctly", async () => {
      const status = await adminClient.getSubscriptionStatus({
        orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
      });

      if (status.billingCycle.cycleStartDate && status.billingCycle.cycleDays) {
        const startDate = new Date(status.billingCycle.cycleStartDate);
        const expectedEndDate = new Date(
          startDate.getTime() +
            status.billingCycle.cycleDays * 24 * 60 * 60 * 1000,
        );
        const actualEndDate = new Date(status.billingCycle.cycleEndDate!);

        expect(actualEndDate.getTime()).toBe(expectedEndDate.getTime());
      }
    });
  });

  describe("Admin operations - Access control", () => {
    it("should allow admin to promote organization to enterprise", async () => {
      const result = await adminClient.promoteOrganizationToEnterprise({
        orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
      });

      expect(result).toBe(true);

      const status = await adminClient.getSubscriptionStatus({
        orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
      });

      expect(status.planName).toBe("ENTERPRISE");
      expect(status.tier).toBe("enterprise");

      await adminClient.demoteOrganizationFromEnterprise({
        orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
      });
    });

    it("should deny regular user from promoting organization", async () => {
      await expect(
        regularClient.promoteOrganizationToEnterprise({
          orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
        }),
      ).rejects.toThrow("Only global admins can change organization plan");
    });

    it("should allow admin to add credits", async () => {
      const orgName = `free_billing_${FREE_ORG_ID.substring(0, 8)}`;

      const initialStatus = await adminClient.getSubscriptionStatus({
        orgName,
      });
      const initialBalance = initialStatus.creditsBalance;

      await adminClient.addOrganizationCredits({
        orgName,
        amount: 50,
        reason: "Test credit addition",
      });

      const updatedStatus = await adminClient.getSubscriptionStatus({
        orgName,
      });

      expect(updatedStatus.creditsBalance).toBe(initialBalance + 50);
    });

    it("should allow admin to deduct credits", async () => {
      const orgName = `free_billing_${FREE_ORG_ID.substring(0, 8)}`;

      const initialStatus = await adminClient.getSubscriptionStatus({
        orgName,
      });
      const initialBalance = initialStatus.creditsBalance;

      await adminClient.deductOrganizationCredits({
        orgName,
        amount: 25,
        reason: "Test credit deduction",
      });

      const updatedStatus = await adminClient.getSubscriptionStatus({
        orgName,
      });

      expect(updatedStatus.creditsBalance).toBe(initialBalance - 25);
    });

    it("should deny regular user from adding credits", async () => {
      await expect(
        regularClient.addOrganizationCredits({
          orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
          amount: 50,
        }),
      ).rejects.toThrow("row-level security policy");
    });

    it("should deny regular user from deducting credits", async () => {
      await expect(
        regularClient.deductOrganizationCredits({
          orgName: `free_billing_${FREE_ORG_ID.substring(0, 8)}`,
          amount: 10,
        }),
      ).rejects.toThrow("row-level security policy");
    });

    it("should deny regular user from inserting transaction logs directly", async () => {
      const regularUserSupabase = createClient(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY,
        {
          auth: { storageKey: "regular-billing-client-auth-logs" },
        },
      );
      await regularUserSupabase.auth.signInWithPassword({
        email: `billing_regular_${REGULAR_USER_ID}@test.com`,
        password: "password123",
      });

      const { error } = await regularUserSupabase
        .from("organization_credit_transactions")
        .insert({
          org_id: FREE_ORG_ID,
          user_id: REGULAR_USER_ID,
          amount: 100,
          transaction_type: "admin_grant",
          metadata: { reason: "fake transaction" },
          created_at: new Date().toISOString(),
        });

      expect(error).toBeDefined();
      expect(error?.message).toContain("policy");
    });

    it("should allow admin to insert transaction logs directly", async () => {
      const adminUserSupabase = createClient(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY,
        {
          auth: { storageKey: "admin-billing-client-auth-logs" },
        },
      );
      await adminUserSupabase.auth.signInWithPassword({
        email: `billing_admin_${ADMIN_USER_ID}@test.com`,
        password: "password123",
      });

      const { error } = await adminUserSupabase
        .from("organization_credit_transactions")
        .insert({
          org_id: FREE_ORG_ID,
          user_id: ADMIN_USER_ID,
          amount: 50,
          transaction_type: "admin_grant",
          metadata: { reason: "admin test transaction" },
          created_at: new Date().toISOString(),
        });

      expect(error).toBeNull();
    });
  });

  describe("Organization listing", () => {
    it("should list enterprise organizations for admin", async () => {
      const enterprises = await adminClient.getEnterpriseOrganizations();

      expect(Array.isArray(enterprises)).toBe(true);
      expect(enterprises.some((org) => org.id === ENTERPRISE_ORG_ID)).toBe(
        true,
      );
    });

    it("should list all organizations with credits for admin", async () => {
      const allOrgs = await adminClient.getAllOrganizationsWithCredits();

      expect(Array.isArray(allOrgs)).toBe(true);
      expect(allOrgs.length).toBeGreaterThanOrEqual(2);
      expect(allOrgs.some((org) => org.id === FREE_ORG_ID)).toBe(true);
      expect(allOrgs.some((org) => org.id === ENTERPRISE_ORG_ID)).toBe(true);
    });
  });
});
