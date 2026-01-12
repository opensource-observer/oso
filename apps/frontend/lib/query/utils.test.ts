import { queryContainsUDMsReferenceWithDefaults } from "@/lib/query/utils";

describe("queryContainsUDMsReference", () => {
  it("should return false for queries with no table references", async () => {
    const query = "SELECT 1 + 1 AS sum";
    const result = await queryContainsUDMsReferenceWithDefaults({
      query,
      metadata: {
        orgName: "test-org",
        datasetName: "test-dataset",
      },
    });
    expect(result).toBe(false);
  });

  it("should return true for queries referencing UDMs", async () => {
    const queriesToTest: string[] = [
      "SELECT * FROM some_org.some_dataset.user_model",
      "SELECT col1, col2 FROM user_model WHERE col3 > 100",
      "SELECT col1, col2 FROM some_dataset.user_model",
    ];

    for (const query of queriesToTest) {
      const result = await queryContainsUDMsReferenceWithDefaults({
        query,
        metadata: {
          orgName: "test-org",
          datasetName: "test-dataset",
        },
      });
      expect(result).toBe(true);
    }
  });

  it("should return false for queries not referencing UDMs", async () => {
    const queriesToTest: string[] = [
      "SELECT * FROM iceberg.some_dataset.some_table",
      "SELECT col1, col2 FROM some_org__private.some_dataset.some_table",
    ];

    for (const query of queriesToTest) {
      const result = await queryContainsUDMsReferenceWithDefaults({
        query,
        metadata: {
          orgName: "test-org",
        },
      });
      expect(result).toBe(false);
    }
  });

  it("should throw an error when metadata is insufficient to resolve tables in the udm context", async () => {
    const query = "SELECT * FROM user_model";
    await expect(
      queryContainsUDMsReferenceWithDefaults({
        query,
        metadata: {
          orgName: "test-org",
          sourceType: "udm",
        },
      }),
    ).rejects.toThrow(
      'Cannot infer table mapping for "user_model" without datasetName in metadata.',
    );
  });
});
