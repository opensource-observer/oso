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
      { table1: Table.fromString("table1") },
      validMetadata,
    );

    expect(resolved).toEqual({
      table1: new Table("test-org", "test-dataset", "table1"),
    });
  });

  it("should resolve partially qualified table names (dataset.table) using metadata orgName", async () => {
    const resolved = await resolver.resolveTables(
      { "other_dataset.table1": Table.fromString("other_dataset.table1") },
      validMetadata,
    );

    expect(resolved).toEqual({
      "other_dataset.table1": new Table("test-org", "other_dataset", "table1"),
    });
  });

  it("should resolve partially qualified table names (dataset.table) using metadata orgName even if datasetName is missing in metadata", async () => {
    const resolved = await resolver.resolveTables(
      { "other_dataset.table1": Table.fromString("other_dataset.table1") },
      metadataWithoutDataset,
    );

    expect(resolved).toEqual({
      "other_dataset.table1": new Table("test-org", "other_dataset", "table1"),
    });
  });

  it("should leave fully qualified names unchanged", async () => {
    const resolved = await resolver.resolveTables(
      {
        "custom.catalog.table1": Table.fromString("custom.catalog.table1"),
      },
      validMetadata,
    );
    expect(resolved).toEqual({
      "custom.catalog.table1": new Table("custom", "catalog", "table1"),
    });
  });

  it("should throw error if datasetName is missing in metadata when resolving bare table", async () => {
    await expect(
      resolver.resolveTables(
        { table1: Table.fromString("table1") },
        metadataWithoutDataset,
      ),
    ).rejects.toThrow(
      'Cannot infer table mapping for "table1" without datasetName in metadata.',
    );
  });

  it("should return untouched metadata if metadata is invalid (missing required fields)", async () => {
    const invalidMetadata = {
      user: "test-user",
      // Missing timestamp, orgName, orgId
    };

    const resolved = await resolver.resolveTables(
      { table1: Table.fromString("table1") },
      invalidMetadata,
    );

    expect(resolved).toEqual({
      table1: Table.fromString("table1"),
    });
  });
});
