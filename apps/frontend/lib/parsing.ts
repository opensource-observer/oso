import dayjs from "dayjs";
import _ from "lodash";
import { Parser, AST } from "node-sql-parser";

/**
 * Parse a comma-separated list into a string array
 * @param csv
 * @returns
 */
const csvToArray = (csv?: string | null) =>
  csv?.split(",").map((x) => x.trim()) ?? [];

/**
 * Parses string IDs into integers
 * @param ids
 * @returns
 */
const stringToIntArray = (ids?: string[]): number[] =>
  ids?.map((id) => parseInt(id)).filter((id) => !!id && !isNaN(id)) ?? [];

/**
 * Convert the event time to a date label
 */
const eventTimeToLabel = (t: any) => dayjs(t).format("YYYY-MM-DD");

/**
 * If we get enums (e.g. NPM_PACKAGE), normalize it into a readable label
 * @param t
 * @returns
 */
const eventTypeToLabel = (t: string) => _.capitalize(t.replace(/_/g, " "));

/**
 * Get the names of all tables referenced in a SQL AST
 * @param ast
 * @returns
 */
function getTableNamesFromAst(ast: AST): string[] {
  if (ast.type == "select") {
    const cteNames = ast.with ? _.flatMap(ast.with, (x) => x.name.value) : [];
    const cteTables = ast.with
      ? _.flatMap(ast.with, (x) => x.stmt.tableList)
      : [];
    // Sometimes the table name is prefixed with the operation
    // e.g. "select::null::event",
    // This just gets the last part
    const cteTrimmedNames = cteTables.map((x: string) => {
      const parts = x.split("::");
      return parts[parts.length - 1];
    });
    const tableNames = Array.isArray(ast.from)
      ? ast.from.map((x: any) => x.table)
      : [];
    const truthyNames = tableNames.filter((name: string) => !!name);
    const combinedNames = [...truthyNames, ...cteTrimmedNames];
    const removeCtes = combinedNames.filter(
      (name: string) => !cteNames.includes(name),
    );
    return removeCtes;
  } else {
    console.warn("SQL is not a SELECT statement");
    return [];
  }
}

/**
 * Get the names of all tables referenced in a SQL query
 * @param query
 * @returns
 */
function getTableNamesFromSql(query: string): string[] {
  const parser = new Parser();
  try {
    const ast = parser.astify(query, { database: "trino" });
    const tableNames = Array.isArray(ast)
      ? _.flatMap(ast, (x) => getTableNamesFromAst(x))
      : getTableNamesFromAst(ast);

    // De-duplicate
    return _.uniq(tableNames);
  } catch {
    return [];
  }
}

export {
  csvToArray,
  stringToIntArray,
  eventTimeToLabel,
  eventTypeToLabel,
  getTableNamesFromSql,
};
