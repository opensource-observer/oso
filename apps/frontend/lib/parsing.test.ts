import { getTableNamesFromSql } from "@/lib/parsing";

describe("parses SQL", () => {
  it("handles simple retrieval", () => {
    const names = getTableNamesFromSql(`SELECT * FROM event`);
    expect(names.length).toBe(1);
    expect(names).toContain("event");
  });

  it("handles ctes", () => {
    const names = getTableNamesFromSql(`
WITH Devs AS (
    SELECT 
        p."id" AS "projectId",
        e."fromId" AS "fromId",
        TO_CHAR(DATE_TRUNC('MONTH', e."time"), 'YYYY-MM-01') AS "bucketMonthly",
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN e."typeId" = 4 THEN e."time" END) >= 10 THEN 'FULL_TIME_DEV'
            WHEN COUNT(DISTINCT CASE WHEN e."typeId" = 4 THEN e."time" END) >= 1 THEN 'PART_TIME_DEV'
            ELSE 'OTHER_CONTRIBUTOR'
        END AS "devType",
        1 AS amount
    FROM 
        event e
    JOIN 
        project_artifacts_artifact paa ON e."toId" = paa."artifactId"
    JOIN 
        project p ON paa."projectId" = p.id
        
    WHERE
        e."typeId" IN (
            2,
            3,
            4,
            6,
            18
        )
    GROUP BY
        p."id",
        e."fromId",
        TO_CHAR(DATE_TRUNC('MONTH', e."time"), 'YYYY-MM-01')
)
SELECT
    Devs."projectId",
    Devs."devType",
    Devs."bucketMonthly",
    SUM(Devs."amount") AS "amount"
FROM 
    Devs
GROUP BY
    Devs."projectId",
    Devs."devType",
    Devs."bucketMonthly";
    `);
    expect(names.length).toBe(3);
    expect(names).toContain("event");
    expect(names).toContain("project_artifacts_artifact");
    expect(names).toContain("project");
  });

  it("handles joins", () => {
    const names = getTableNamesFromSql(`
SELECT
    p."slug" AS project_slug,
    p."name" AS project_name,
    a1."name" AS artifact_name,
    a2."name" AS contributor_name,
    e."time" AS event_time,
    e."type" AS event_type
FROM
    project p
JOIN
    project_artifacts_artifact paa ON p."id" = paa."projectId"
JOIN
    artifact a1 ON paa."artifactId" = a1."id"
JOIN
    event e ON a1."id" = e."toId"
JOIN
    artifact a2 ON e."fromId" = a2."id"
JOIN
    collection_projects_project cpp ON p."id" = cpp."projectId"
JOIN
    collection c ON cpp."collectionId" = c."id"    
WHERE 
    c."slug" = 'a'
    AND a1."namespace" = 'a'
    `);
    expect(names.length).toBe(6);
    expect(names).toContain("project");
    expect(names).toContain("project_artifacts_artifact");
    expect(names).toContain("artifact");
    expect(names).toContain("event");
    expect(names).toContain("collection_projects_project");
    expect(names).toContain("collection");
  });

  it("handle trino syntax", () => {
    const names = getTableNamesFromSql(`
      SHOW CATALOGS
    `);
    expect(names.length).toBe(0);
  });

  it("doesn't break when failing to parse", () => {
    const names = getTableNamesFromSql(`
      SHOW SCHEMAS FROM iceberg
    `);
    expect(names.length).toBe(0);
  });
});
