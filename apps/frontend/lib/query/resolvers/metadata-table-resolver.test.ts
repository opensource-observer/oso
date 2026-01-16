import { Table } from "@/lib/types/table";
import { MetadataInferredTableResolver } from "@/lib/query/resolvers/metadata-table-resolver";

describe("MetadataInferredTableResolver", () => {
  let resolver: MetadataInferredTableResolver;
  const validMetadata = {
    user: "test-user",
    timestamp: "2023-01-01T00:00:00Z",
    orgName: "test-org",
    orgId: "test-org-id",
    datasetName: "test-dataset",
  };

  const metadataWithoutDataset = {
    user: "test-user",
    timestamp: "2023-01-01T00:00:00Z",
    orgName: "test-org",
    orgId: "test-org-id",
  };

  beforeEach(() => {
    resolver = new MetadataInferredTableResolver();
  });

  it("should resolve bare table names using metadata orgName and datasetName", async () => {
    const resolved = await resolver.resolveTables(
      {
        tables: {
          table1: Table.fromString("table1"),
        },
        errors: [],
      },
      validMetadata,
    );

    expect(resolved).toEqual({
      map: {
        table1: new Table("test-org", "test-dataset", "table1"),
      },
      errors: [],
    });
  });

  it("should resolve partially qualified table names (dataset.table) using metadata orgName", async () => {
    const resolved = await resolver.resolveTables(
      {
        tables: {
          "other_dataset.table1": Table.fromString("other_dataset.table1"),
        },
        errors: [],
      },
      validMetadata,
    );

    expect(resolved).toEqual({
      map: {
        "other_dataset.table1": new Table(
          "test-org",
          "other_dataset",
          "table1",
        ),
      },
      errors: [],
    });
  });

  it("should resolve partially qualified table names (dataset.table) using metadata orgName even if datasetName is missing in metadata", async () => {
    const resolved = await resolver.resolveTables(
      {
        tables: {
          "other_dataset.table1": Table.fromString("other_dataset.table1"),
        },
        errors: [],
      },
      metadataWithoutDataset,
    );

    expect(resolved).toEqual({
      map: {
        "other_dataset.table1": new Table(
          "test-org",
          "other_dataset",
          "table1",
        ),
      },
      errors: [],
    });
  });

  it("should leave fully qualified names unchanged", async () => {
    const resolved = await resolver.resolveTables(
      {
        tables: {
          "custom.catalog.table1": Table.fromString("custom.catalog.table1"),
        },
        errors: [],
      },
      validMetadata,
    );
    expect(resolved).toEqual({
      map: {
        "custom.catalog.table1": new Table("custom", "catalog", "table1"),
      },
      errors: [],
    });
  });

  it("should throw error if datasetName is missing in metadata when resolving bare table", async () => {
    await expect(
      resolver.resolveTables(
        { tables: { table1: Table.fromString("table1") }, errors: [] },
        metadataWithoutDataset,
      ),
    ).rejects.toThrow(
      'Cannot infer table mapping for "table1" without datasetName in metadata.',
    );
  });

  it("should throw error if metadata is invalid (missing required fields)", async () => {
    const invalidMetadata = {
      user: "test-user",
      // Missing timestamp, orgName, orgId
    };

    await expect(
      resolver.resolveTables(
        { tables: { table1: Table.fromString("table1") }, errors: [] },
        invalidMetadata,
      ),
    ).rejects.toThrow();
  });
});
