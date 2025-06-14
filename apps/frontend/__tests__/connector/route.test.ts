import { POST, DELETE } from "@/app/api/v1/connector/route";
import { NextRequest } from "next/server";
import { getTrinoAdminClient } from "@/lib/clients/trino";
import { createAdminClient } from "@/lib/supabase/admin";
import { Session, SupabaseClient } from "@supabase/supabase-js";
import { Database } from "@/lib/types/supabase"; // Assuming Database types are here
import { randomUUID } from "crypto";

// Mock dependencies
jest.mock("server-only", () => {});
jest.mock("../../lib/clients/trino");

const mockTrinoClient = {
  queryAll: jest.fn(),
};

const mockGetTrinoAdminClient = getTrinoAdminClient as jest.Mock;

const supabaseAdminClient: SupabaseClient<Database> = createAdminClient();

describe("API /api/v1/connector", () => {
  let testUser: any;
  let testOrg: any;
  let session: Session | null = null;

  beforeAll(async () => {
    const userEmail = `test_user_${Date.now()}@example.com`;
    const orgName = `test_org_${randomUUID().split("-")[0]}`;

    const { data: userData, error: userError } =
      await supabaseAdminClient.auth.admin.createUser({
        email: userEmail,
        password: "password",
        email_confirm: true,
      });
    if (userError)
      throw new Error(`User creation failed: ${userError.message}`);
    testUser = userData.user;

    const { data: orgData, error: orgError } = await supabaseAdminClient
      .from("organizations")
      .insert({ org_name: orgName, created_by: testUser.id })
      .select()
      .single();
    if (orgError) {
      await supabaseAdminClient.auth.admin.deleteUser(testUser.id);
      throw new Error(`Org creation failed: ${orgError.message}`);
    }
    testOrg = orgData;

    const { error: userOrgError } = await supabaseAdminClient
      .from("users_by_organization")
      .insert({ user_id: testUser.id, org_id: testOrg.id, user_role: "admin" });
    if (userOrgError) {
      await supabaseAdminClient
        .from("organizations")
        .delete()
        .eq("id", testOrg.id);
      await supabaseAdminClient.auth.admin.deleteUser(testUser.id);
      throw new Error(`User-Org link failed: ${userOrgError.message}`);
    }

    const { data, error } = await supabaseAdminClient.auth.signInWithPassword({
      email: userEmail,
      password: "password",
    });
    if (error) {
      throw new Error(`Session creation failed: ${error.message}`);
    }

    session = data.session;
  });

  afterAll(async () => {
    if (testOrg && testOrg.id) {
      await supabaseAdminClient
        .from("users_by_organization")
        .delete()
        .eq("org_id", testOrg.id);
      await supabaseAdminClient
        .from("organizations")
        .delete()
        .eq("id", testOrg.id);
    }
    if (testUser && testUser.id) {
      await supabaseAdminClient.auth.admin.deleteUser(testUser.id);
    }
  });

  beforeEach(async () => {
    jest.clearAllMocks();
    mockGetTrinoAdminClient.mockReturnValue(mockTrinoClient);
    await supabaseAdminClient.from("dynamic_connectors").delete();
  });

  describe("POST", () => {
    it("should create a dynamic connector successfully", async () => {
      mockTrinoClient.queryAll.mockResolvedValueOnce({ error: null });

      const connectorName = `${testOrg.org_name}_postgres`;
      const requestBody = {
        data: {
          org_id: testOrg.id,
          connector_name: connectorName,
          connector_type: "postgresql",
          config: { host: "localhost" },
          created_by: testUser.id,
        },
        credentials: {},
      };
      const req = new NextRequest("http://localhost/api/v1/connector", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
        },
        body: JSON.stringify(requestBody),
      });

      const response = await POST(req);
      const json = await response.json();

      expect(response.status).toBe(200);
      expect(json.connector_name).toBe(connectorName);
      expect(json.org_id).toBe(testOrg.id);
      expect(json.connector_type).toBe("postgresql");
      expect(mockTrinoClient.queryAll).toHaveBeenCalledWith(
        expect.stringContaining(
          `CREATE CATALOG ${connectorName} USING postgresql WITH`,
        ),
      );

      if (json.id) {
        await supabaseAdminClient
          .from("dynamic_connectors")
          .delete()
          .eq("id", json.id);
      }
    });

    it("should return 401 if authentication fails", async () => {
      const req = new NextRequest("http://localhost/api/v1/connector", {
        method: "POST",
        body: JSON.stringify({}),
      });
      const response = await POST(req);
      expect(response.status).toBe(401);
      const json = await response.json();
      expect(json.error).toContain("Authorization error");
    });

    it("should return 400 for invalid connector type", async () => {
      const requestBody = {
        data: {
          org_id: testOrg.id,
          connector_name: `${testOrg.org_name}_invalid`,
          connector_type: "invalid_type",
          created_by: testUser.id,
        },
        credentials: { token: "abc" },
      };
      const req = new NextRequest("http://localhost/api/v1/connector", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
        },
        body: JSON.stringify(requestBody),
      });
      const response = await POST(req);
      expect(response.status).toBe(400);
      const json = await response.json();
      expect(json.error).toContain("Invalid connector type: invalid_type");
    });

    it("should return 400 for invalid connector name", async () => {
      const requestBody = {
        data: {
          org_id: testOrg.id,
          connector_name: "wrongprefix_postgres",
          connector_type: "postgresql",
          created_by: testUser.id,
        },
        credentials: { token: "abc" },
      };
      const req = new NextRequest("http://localhost/api/v1/connector", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
        },
        body: JSON.stringify(requestBody),
      });
      const response = await POST(req);
      expect(response.status).toBe(400);
      const json = await response.json();
      expect(json.error).toContain(
        "Invalid connector name: wrongprefix_postgres",
      );
    });

    it("should return 500 if fetching organization fails", async () => {
      const invalidOrgId = "00000000-0000-0000-0000-000000000000";
      const requestBody = {
        data: {
          org_id: invalidOrgId,
          connector_name: "testorg_pg",
          connector_type: "postgresql",
          created_by: testUser.id,
        },
        credentials: { token: "abc" },
      };
      const req = new NextRequest("http://localhost/api/v1/connector", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
        },
        body: JSON.stringify(requestBody),
      });
      const response = await POST(req);
      expect(response.status).toBe(500);
      const json = await response.json();
      expect(json.error).toContain("Error fetching organization");
    });

    it("should attempt to cleanup Supabase if Trino catalog creation fails", async () => {
      mockTrinoClient.queryAll.mockResolvedValueOnce({
        error: new Error("Trino error"),
      });

      const connectorName = `${testOrg.org_name}_postgres_cleanup`;
      const requestBody = {
        data: {
          org_id: testOrg.id,
          connector_name: connectorName,
          connector_type: "postgresql",
          created_by: testUser.id,
        },
        credentials: { password: "secure" },
      };
      const req = new NextRequest("http://localhost/api/v1/connector", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
        },
        body: JSON.stringify(requestBody),
      });

      const response = await POST(req);
      expect(response.status).toBe(500);
      const json = await response.json();
      expect(json.error).toContain(
        "Error creating catalog: Error: Trino error",
      );

      const { data: cleanedConnector, error: fetchError } =
        await supabaseAdminClient
          .from("dynamic_connectors")
          .select("id")
          .eq("connector_name", connectorName)
          .eq("org_id", testOrg.id)
          .maybeSingle();

      expect(fetchError).toBeNull();
      expect(cleanedConnector).toBeNull();
    });
  });

  describe("DELETE", () => {
    let connectorToDelete: any;

    beforeEach(async () => {
      const connectorName = `${testOrg.org_name}_todelete_${randomUUID().split("-")[0]}`;
      const { data, error } = await supabaseAdminClient
        .from("dynamic_connectors")
        .insert({
          connector_name: connectorName,
          org_id: testOrg.id,
          connector_type: "postgresql",
          created_by: testUser.id,
          config: { host: "delete-test" }, // Ensure config is not null if required by schema
          is_public: false,
        })
        .select("*")
        .single();
      if (error) {
        throw new Error(
          `Failed to create connector for DELETE test: ${error.message}`,
        );
      }
      connectorToDelete = data;
    });

    afterEach(async () => {
      if (connectorToDelete && connectorToDelete.id) {
        await supabaseAdminClient
          .from("dynamic_connectors")
          .delete()
          .eq("id", connectorToDelete.id);
      }
    });

    it("should delete a dynamic connector successfully", async () => {
      mockTrinoClient.queryAll.mockResolvedValueOnce({ error: null });

      const req = new NextRequest(
        `http://localhost/api/v1/connector?id=${connectorToDelete.id}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
          },
        },
      );

      const response = await DELETE(req);
      const json = await response.json();

      expect(response.status).toBe(200);
      expect(json.id).toBe(connectorToDelete.id);
      expect(json.connector_name).toBe(connectorToDelete.connector_name);
      expect(mockTrinoClient.queryAll).toHaveBeenCalledWith(
        `DROP CATALOG ${connectorToDelete.connector_name}`,
      );

      const { data: found } = await supabaseAdminClient
        .from("dynamic_connectors")
        .select()
        .eq("id", connectorToDelete.id)
        .maybeSingle();
      expect(found?.deleted_at).not.toBeNull();
    });

    it("should return 401 if authentication fails for DELETE", async () => {
      const req = new NextRequest(
        "http://localhost/api/v1/connector?id=connector-id",
        {
          method: "DELETE",
        },
      );
      const response = await DELETE(req);
      expect(response.status).toBe(401);
      const json = await response.json();
      expect(json.error).toContain("Authorization error");
    });

    it("should return 400 if id parameter is missing for DELETE", async () => {
      const req = new NextRequest("http://localhost/api/v1/connector", {
        // No id query param
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
        },
      });
      const response = await DELETE(req);
      expect(response.status).toBe(400);
      const json = await response.json();
      expect(json.error).toBe("Missing id parameter");
    });

    it("should return 404 if connector to delete is not found", async () => {
      const nonExistentConnectorId = "00000000-0000-0000-0000-000000000000";
      const req = new NextRequest(
        `http://localhost/api/v1/connector?id=${nonExistentConnectorId}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
          },
        },
      );
      const response = await DELETE(req);
      expect(response.status).toBe(406);
      const json = await response.json();
      expect(json.error).toContain("Error deleting connector");
    });

    it("should attempt to revert Supabase deletion if Trino catalog drop fails", async () => {
      const originalConnectorData = { ...connectorToDelete }; // Clone for revert check

      mockTrinoClient.queryAll.mockResolvedValueOnce({
        error: new Error("Trino drop error"),
      });

      const req = new NextRequest(
        `http://localhost/api/v1/connector?id=${connectorToDelete.id}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            "X-Supabase-Auth": `${session?.access_token}:${session?.refresh_token}`,
          },
        },
      );

      const response = await DELETE(req);
      expect(response.status).toBe(500);
      const json = await response.json();
      expect(json.error).toContain(
        "Error dropping catalog: Error: Trino drop error",
      );

      const { data: revertedConnector, error: fetchError } =
        await supabaseAdminClient
          .from("dynamic_connectors")
          .select()
          .eq("id", originalConnectorData.id)
          .single();

      expect(fetchError).toBeNull();
      if (!revertedConnector) throw new Error("Reverted connector not found");

      expect(revertedConnector.deleted_at).toBeNull();
    });
  });
});
