import { Table } from "@/lib/types/table";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";

describe("LegacyInferredTableResolver", () => {
  let resolver: LegacyInferredTableResolver;

  beforeEach(() => {
    resolver = new LegacyInferredTableResolver();
  });

  it("should resolve bare table names to iceberg.oso", async () => {
    const resolved = await resolver.resolveTables(
      { table1: Table.fromString("table1") },
      {},
    );

    expect(resolved).toEqual({
      table1: new Table("iceberg", "oso", "table1"),
    });
  });

  it("should resolve oso dataset to iceberg catalog", async () => {
    const resolved = await resolver.resolveTables(
      { "oso.table1": Table.fromString("oso.table1") },
      {},
    );
    expect(resolved).toEqual({
      "oso.table1": new Table("iceberg", "oso", "table1"),
    });
  });

  it("should leave fully qualified names unchanged", async () => {
    const resolved = await resolver.resolveTables(
      { "custom.catalog.table1": Table.fromString("custom.catalog.table1") },
      {},
    );
    expect(resolved).toEqual({
      "custom.catalog.table1": new Table("custom", "catalog", "table1"),
    });
  });

  it("should leave datasets other than oso unchanged", async () => {
    const resolved = await resolver.resolveTables(
      { "other.table1": Table.fromString("other.table1") },
      {},
    );
    expect(resolved).toEqual({
      "other.table1": new Table("", "other", "table1"),
    });
  });
});
