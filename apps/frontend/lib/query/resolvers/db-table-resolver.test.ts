import { createClient } from "@supabase/supabase-js";
import { SUPABASE_SERVICE_KEY, SUPABASE_URL } from "@/lib/config";
import type { Database } from "@/lib/types/supabase";
import * as crypto from "crypto";
import { DBTableResolver } from "@/lib/query/resolvers/db-table-resolver";
import { Table } from "@/lib/types/table";

let testSupabaseClient: ReturnType<typeof createClient<Database>>;

jest.mock("../../supabase/server", () => ({
  createServerClient: jest.fn(() => testSupabaseClient),
  createAdminClient: jest.fn(() => testSupabaseClient),
}));

describe("DBTableResolver", () => {
  /**
   * Ideally we'd have more control over the fixture state of this by using some
   * kind of data layer abstraction. However, for now we just create a more
   * complex fixture here directly in the test database.
   */

  let adminSupabase: ReturnType<typeof createClient<Database>>;
  const TEST_USER_ID = crypto.randomUUID();
  const RANDOM_SUFFIX = crypto.randomBytes(4).toString("hex");
  const TEST_ORG_NAMES_AND_IDS: Record<string, { name: string; id: string }> = {
    org_a: { name: `org_a_${RANDOM_SUFFIX}`, id: crypto.randomUUID() },
    org_b: { name: `org_b_${RANDOM_SUFFIX}`, id: crypto.randomUUID() },
    org_c: { name: `org_c_${RANDOM_SUFFIX}`, id: crypto.randomUUID() },
    org_d: { name: `org_d_${RANDOM_SUFFIX}`, id: crypto.randomUUID() },
    org_e: { name: `org_e_${RANDOM_SUFFIX}`, id: crypto.randomUUID() },
  };
  const TEST_ORG_ID_TO_REF: Record<string, string> = Object.fromEntries(
    Object.keys(TEST_ORG_NAMES_AND_IDS).map((ref) => [
      TEST_ORG_NAMES_AND_IDS[ref].id,
      ref,
    ]),
  );
  const orgDatasets: Record<string, string[]> = {};

  beforeAll(async () => {
    adminSupabase = createClient<Database>(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "credits-test-auth" },
    });
    testSupabaseClient = adminSupabase;

    await adminSupabase.auth.admin.createUser({
      id: TEST_USER_ID,
      email: `credits_test_${TEST_USER_ID}@test.com`,
      password: "password123",
      email_confirm: true,
    });

    const orgs = await adminSupabase
      .from("organizations")
      .insert(
        Object.values(TEST_ORG_NAMES_AND_IDS).map((orgNameAndId) => ({
          id: orgNameAndId.id,
          org_name: orgNameAndId.name,
          created_by: TEST_USER_ID,
        })),
      )
      .select()
      .throwOnError();

    // Create an "user", "connector", and "ingestion" dataset for every org
    const datasets = await adminSupabase
      .from("datasets")
      .insert(
        orgs.data.flatMap((org) => {
          const datasetIds: string[] = [
            crypto.randomUUID(),
            crypto.randomUUID(),
            crypto.randomUUID(),
          ];
          const orgRef = TEST_ORG_ID_TO_REF[org.id];
          orgDatasets[orgRef] = datasetIds;

          return [
            {
              id: datasetIds[0],
              org_id: org.id,
              name: "user",
              display_name: `User Dataset for ${org.org_name}`,
              created_by: TEST_USER_ID,
              dataset_type: "USER_MODEL" as const,
            },
            {
              id: datasetIds[1],
              org_id: org.id,
              name: "connection",
              display_name: `Connection Dataset for ${org.org_name}`,
              created_by: TEST_USER_ID,
              dataset_type: "DATA_CONNECTION" as const,
            },
            {
              id: datasetIds[2],
              org_id: org.id,
              name: "ingestion",
              display_name: `Ingestion Dataset for ${org.org_name}`,
              created_by: TEST_USER_ID,
              dataset_type: "DATA_INGESTION" as const,
            },
          ];
        }),
      )
      .select()
      .throwOnError();

    // Create model "alpha", "bravo", and "charlie" models for every dataset that is a "USER_MODEL"
    const models = await adminSupabase
      .from("model")
      .insert(
        datasets.data.flatMap((dataset) => {
          if (dataset.dataset_type !== "USER_MODEL") {
            return [];
          }
          return [
            {
              dataset_id: dataset.id,
              org_id: dataset.org_id,
              name: "alpha",
            },
            {
              dataset_id: dataset.id,
              org_id: dataset.org_id,
              name: "bravo",
            },
            {
              dataset_id: dataset.id,
              org_id: dataset.org_id,
              name: "charlie",
            },
          ];
        }),
      )
      .select()
      .throwOnError();

    // Create model revision for every model
    const modelRevisions = await adminSupabase
      .from("model_revision")
      .insert(
        models.data.map((model) => ({
          org_id: model.org_id,
          model_id: model.id,
          name: model.name,
          revision_number: 1,
          hash: crypto.randomUUID(),
          language: "sql",
          code: "SELECT 1;",
          cron: "@daily",
          schema: [],
          kind: "FULL" as const,
        })),
      )
      .select()
      .throwOnError();

    // Create a model release for every model revision
    const modelReleases = await adminSupabase
      .from("model_release")
      .insert(
        modelRevisions.data.map((revision) => ({
          org_id: revision.org_id,
          model_id: revision.model_id,
          model_revision_id: revision.id,
        })),
      )
      .select()
      .throwOnError();

    // Create a mapping for model to model_revision
    const modelIdToReleaseMap: Record<string, string> = {};
    modelReleases.data.forEach((release) => {
      modelIdToReleaseMap[release.model_id] = release.id;
    });

    // Create two runs for every model, both completed but with different created_at timestamps
    const modelRuns = await adminSupabase
      .from("run")
      .insert(
        models.data.flatMap((model) => [
          {
            org_id: model.org_id,
            dataset_id: model.dataset_id,
            status: "completed" as const,
            started_at: "2025-01-01T00:00:00Z",
            completed_at: "2025-01-01T00:00:00Z",
          },
          {
            org_id: model.org_id,
            dataset_id: model.dataset_id,
            status: "completed" as const,
            started_at: "2025-01-02T00:00:00Z",
            completed_at: "2025-01-02T00:00:00Z",
          },
        ]),
      )
      .select()
      .throwOnError();

    // Create materializations for every model and associated runs
    await adminSupabase
      .from("materialization")
      .insert(
        models.data.flatMap((model, index) => {
          const firstRun = modelRuns.data[index * 2];
          const secondRun = modelRuns.data[index * 2 + 1];

          return [
            {
              org_id: model.org_id,
              dataset_id: model.dataset_id,
              run_id: firstRun.id,
              table_id: `data_model_${model.id}`,
              warehouse_fqn: `org_${model.org_id}.dataset_${model.dataset_id}.model_${model.id}`,
              schema: [],
            },
            {
              org_id: model.org_id,
              dataset_id: model.dataset_id,
              run_id: secondRun.id,
              table_id: model.id,
              warehouse_fqn: `org_${model.org_id}.dataset_${model.dataset_id}.model_${model.id}`,
              schema: [],
            },
          ];
        }),
      )
      .throwOnError();
  });

  describe("resolveTables", () => {
    it("resolves a table correctly", async () => {
      const resolver = new DBTableResolver(testSupabaseClient, []);

      const resolvedTables = await resolver.resolveTables(
        {
          "some.random.table": Table.fromString(
            `org_a_${RANDOM_SUFFIX}.user.alpha`,
          ),
        },
        {},
      );

      const resolvedTable = resolvedTables["some.random.table"];

      // Check that this resolves to a table in the format we expect
      expect(
        resolvedTable
          .toFQN()
          .startsWith(`org_${TEST_ORG_NAMES_AND_IDS.org_a.id}`),
      ).toBe(true);

      // Check that the dataset is one of the available datasets for org_a
      const datasetIdsForOrgA = orgDatasets["org_a"];
      const datasetIdInResolvedTable = resolvedTable.dataset.split("_")[1];
      expect(datasetIdsForOrgA).toContain(datasetIdInResolvedTable);

      // Check that the table_id is in the expected format
      const tableIdInResolvedTable = resolvedTable.table;
      expect(tableIdInResolvedTable.startsWith("model_")).toBe(true);
    });

    it("resolves multiple tables without duplication", async () => {
      const resolver = new DBTableResolver(testSupabaseClient, []);

      const resolvedTables = await resolver.resolveTables(
        {
          table_00: Table.fromString(`org_a_${RANDOM_SUFFIX}.user.alpha`),
          table_01: Table.fromString(`org_b_${RANDOM_SUFFIX}.user.alpha`),
          table_02: Table.fromString(`org_c_${RANDOM_SUFFIX}.user.alpha`),
          table_03: Table.fromString(`org_d_${RANDOM_SUFFIX}.user.alpha`),
          table_04: Table.fromString(`org_e_${RANDOM_SUFFIX}.user.alpha`),
          table_05: Table.fromString(`org_a_${RANDOM_SUFFIX}.user.bravo`),
          table_06: Table.fromString(`org_b_${RANDOM_SUFFIX}.user.bravo`),
          table_07: Table.fromString(`org_c_${RANDOM_SUFFIX}.user.bravo`),
          table_08: Table.fromString(`org_d_${RANDOM_SUFFIX}.user.bravo`),
          table_09: Table.fromString(`org_e_${RANDOM_SUFFIX}.user.bravo`),
          table_10: Table.fromString(`org_a_${RANDOM_SUFFIX}.user.charlie`),
          table_11: Table.fromString(`org_b_${RANDOM_SUFFIX}.user.charlie`),
          table_12: Table.fromString(`org_c_${RANDOM_SUFFIX}.user.charlie`),
          table_13: Table.fromString(`org_d_${RANDOM_SUFFIX}.user.charlie`),
          table_14: Table.fromString(`org_e_${RANDOM_SUFFIX}.user.charlie`),
        },
        {},
      );

      // Ensure all tables are resolved and all unique (this is a sanity check
      // that our test logic isn't creating duplicate references)
      const seenTableFQNs: Set<string> = new Set();
      for (const [_, table] of Object.entries(resolvedTables)) {
        expect(table).toBeDefined();
        const fqn = table.toFQN();
        expect(seenTableFQNs.has(fqn)).toBe(false);
        seenTableFQNs.add(fqn);
      }
    });

    it("doesn't throw an error for unresolvable tables", async () => {
      const resolver = new DBTableResolver(testSupabaseClient, []);

      const resolvedTables = await resolver.resolveTables(
        {
          valid_table: Table.fromString(`org_a_${RANDOM_SUFFIX}.user.alpha`),
          invalid_table: Table.fromString(`nonexistent.org.nothing`),
        },
        {},
      );
      expect(resolvedTables["valid_table"]).toBeDefined();
      expect(resolvedTables["invalid_table"]).toBeUndefined();
    });
  });
});
