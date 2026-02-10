import { Table } from "@/lib/types/table";
import { PermissionsResolver } from "@/lib/query/resolvers/permissions-resolver";

describe("PermissionResolver", () => {
  let resolver: PermissionsResolver;

  beforeEach(() => {
    resolver = new PermissionsResolver([
      (table) => {
        if (table.catalog === "ignore_me") {
          return table;
        }
        return null;
      },
    ]);
  });

  it("should not change tables if orgName in metadata matches catalog", async () => {
    const resolved = await resolver.resolveTables(
      { table1: Table.fromString("test_org.test_dataset.table1") },
      { orgName: "test_org" },
    );
    await expect(resolved).toEqual({
      table1: new Table("test_org", "test_dataset", "table1"),
    });
  });

  it("should throw permissions error if orgName in metadata doesn't match catalog", async () => {
    await expect(async () => {
      await resolver.resolveTables(
        { table1: Table.fromString("test_org.test_dataset.table1") },
        { orgName: "other_org" },
      );
    }).rejects.toThrow(/test_org\.test_dataset\.table1/);
  });

  it("should throw permissions error if table is not an FQN", async () => {
    await expect(async () => {
      await resolver.resolveTables(
        {
          table1: Table.fromString("test_org.test_dataset.table1"),
          table2: Table.fromString("table2"),
        },
        { orgName: "test_org" },
      );
    }).rejects.toThrow(/table2/);
  });

  it("should resolve ignore_me", async () => {
    const resolved = await resolver.resolveTables(
      {
        table1: Table.fromString("test_org.test_dataset.table1"),
        table2: Table.fromString("ignore_me.db.table"),
      },
      { orgName: "test_org" },
    );
    expect(resolved).toEqual({
      table1: new Table("test_org", "test_dataset", "table1"),
      table2: new Table("ignore_me", "db", "table"),
    });
  });
});
