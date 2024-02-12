/* eslint-disable @typescript-eslint/naming-convention */
import {
  Utf8,
  Int64,
  List,
  Field,
} from "@cloudquery/plugin-sdk-javascript/arrow";
import { JSONType } from "@cloudquery/plugin-sdk-javascript/types/json";
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
import { fetchData } from "oss-directory";

/* eslint-disable import/no-named-as-default-member */
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(customParseFormat);
dayjs.extend(localizedFormat);

const getColumnResolver = (c: string): ColumnResolver => {
  return (_meta, resource) => {
    const dataItem = resource.getItem();
    const columnData = (dataItem as Record<string, unknown>)[c];
    try {
      resource.setColumData(c, columnData);
    } catch (e) {
      console.log("caught error");
      console.log(e);
      throw e;
    }
    return Promise.resolve();
  };
};

async function ossDataToTable<T>(
  name: string,
  data: T[],
  columnDefs: Column[],
): Promise<Table> {
  const tableResolver: TableResolver = (_clientMeta, _parent, stream) => {
    for (const d of data) {
      stream.write(d);
    }
    return Promise.resolve();
  };
  return createTable({
    name: name,
    columns: columnDefs,
    resolver: tableResolver,
  });
}

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

export const getTables = async (): Promise<Table[]> => {
  const { collections, projects } = await fetchData();
  const tables = [
    await ossDataToTable("collections_ossd", collections, [
      newColumn("slug", {
        primaryKey: true,
        unique: true,
        notNull: true,
      }),
      newColumn("name", {
        notNull: true,
      }),
      newColumn("version", {
        type: new Int64(),
      }),
      newColumn("projects", {
        type: new List(new Field("projects", new Utf8())),
      }),
    ]),
    await ossDataToTable("projects_ossd", projects, [
      newColumn("slug", {
        primaryKey: true,
        unique: true,
        notNull: true,
      }),
      newColumn("name", {
        notNull: true,
      }),
      newColumn("github", {
        type: new JSONType(),
        // Ideally we'd be able to use structs to more precisely specify the
        //types on the data. However, there seems to be issues with this on the
        //JS SDK. Will need to check the python/go sdk for cloudquery type: new
        //List(new Field("_blockchain", new JSONType())),
      }),
      newColumn("npm", {
        type: new JSONType(),
      }),
      newColumn("blockchain", {
        type: new JSONType(),
      }),
    ]),
  ];

  return tables;
};
