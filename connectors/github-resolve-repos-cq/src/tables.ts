/* eslint-disable @typescript-eslint/naming-convention */
import { Utf8 } from "@cloudquery/plugin-sdk-javascript/arrow";
import type {
  Column,
  ColumnResolver,
} from "@cloudquery/plugin-sdk-javascript/schema/column";
import type {
  Table,
  TableResolver,
} from "@cloudquery/plugin-sdk-javascript/schema/table";
import { createTable } from "@cloudquery/plugin-sdk-javascript/schema/table";
import dayjs from "dayjs";
import customParseFormat from "dayjs/plugin/customParseFormat.js";
import localizedFormat from "dayjs/plugin/localizedFormat.js";
import timezone from "dayjs/plugin/timezone.js";
import utc from "dayjs/plugin/utc.js";
import { GraphQLClient } from "graphql-request";
import fs from "fs";
import readline from "readline";
import { getReposFromUrls } from "./github/repositories.js";

/* eslint-disable import/no-named-as-default-member */
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(customParseFormat);
dayjs.extend(localizedFormat);

const getColumnResolver = (c: string): ColumnResolver => {
  return (meta, resource) => {
    const dataItem = resource.getItem();
    resource.setColumData(c, (dataItem as Record<string, unknown>)[c]);
    return Promise.resolve();
  };
};

// eslint-disable-next-line @typescript-eslint/require-await
const getRepositories = async (
  input: () => readline.Interface,
  client: GraphQLClient,
): Promise<Table> => {
  const columnDefinitions: Column[] = [
    newColumn("url", {
      primaryKey: true,
      unique: true,
      notNull: true,
    }),
    newColumn("name", {
      notNull: true,
    }),
    newColumn("owner", {
      notNull: true,
    }),
  ];

  const tableResolver: TableResolver = async (clientMeta, parent, stream) => {
    for await (const line of input()) {
      const project = JSON.parse(line) as {
        slug: string;
        github: Array<{ url: string }>;
      };
      console.log(`Loading ${project.slug}`);
      const repos = await getReposFromUrls(
        client,
        project.github.map((p) => p.url),
      );
      for (const repo of repos) {
        stream.write(repo);
      }
    }
    return;
  };
  return createTable({
    name: "repositories",
    columns: columnDefinitions,
    resolver: tableResolver,
  });
};

function newColumn(name: string, opts?: Partial<Column>): Column {
  const options = opts || {};
  return {
    name: name,
    type: options.type || new Utf8(),
    description: options.description || "",
    primaryKey: options.primaryKey || false,
    notNull: options.primaryKey || false,
    incrementalKey: options.incrementalKey || false,
    unique: options.unique || false,
    ignoreInTests: options.ignoreInTests || false,
    resolver: getColumnResolver(name),
  };
}

export const getTables = async (
  inputPath: string,
  client: GraphQLClient,
): Promise<Table[]> => {
  const tables = [
    await getRepositories(() => {
      const fileStream = fs.createReadStream(inputPath);

      return readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity,
      });
    }, client),
  ];

  return tables;
};
