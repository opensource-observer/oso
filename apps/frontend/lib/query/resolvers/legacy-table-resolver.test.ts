import { Table } from "@/lib/types/table";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";

describe("LegacyInferredTableResolver", () => {
  let resolver: LegacyInferredTableResolver;

  beforeEach(() => {
    resolver = new LegacyInferredTableResolver();
  });

  it("should resolve bare table names to iceberg.oso", async () => {
    const resolved = await resolver.resolveTables(
      { tables: { table1: Table.fromString("table1") }, errors: [] },
      {},
    );

    expect(resolved).toEqual({
      map: {
        table1: new Table("iceberg", "oso", "table1"),
      },
      errors: [],
    });
  });

  it("should resolve oso dataset to iceberg catalog", async () => {
    const resolved = await resolver.resolveTables(
      {
        tables: {
          "oso.table1": Table.fromString("oso.table1"),
        },
        errors: [],
      },
      {},
    );
    expect(resolved).toEqual({
      map: {
        "oso.table1": new Table("iceberg", "oso", "table1"),
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
      {},
    );
    expect(resolved).toEqual({
      map: {
        "custom.catalog.table1": new Table("custom", "catalog", "table1"),
      },
      errors: [],
    });
  });

  it("should leave datasets other than oso unchanged", async () => {
    const resolved = await resolver.resolveTables(
      {
        tables: {
          "other.table1": Table.fromString("other.table1"),
        },
        errors: [],
      },
      {},
    );
    expect(resolved).toEqual({
      map: {
        "other.table1": new Table("", "other", "table1"),
      },
      errors: [],
    });
  });
});
