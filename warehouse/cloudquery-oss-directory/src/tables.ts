/* eslint-disable @typescript-eslint/naming-convention */
import {
  Utf8,
  Int64,
  List,
  Field,
  TimestampSecond,
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
import _ from "lodash";

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(customParseFormat);
dayjs.extend(localizedFormat);

type TableOptions = {
  suffix: string;
};

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
    isIncremental: true,
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

export const getTables = async (options: TableOptions): Promise<Table[]> => {
  const { collections, projects } = await fetchData();
  const tables = [
    await ossDataToTable(
      `collections${options.suffix}`,
      collections.map((c) => {
        return _.merge(
          {
            sync_time: new Date(),
          },
          c,
        );
      }),
      [
        newColumn("name", {
          primaryKey: true,
          unique: true,
          notNull: true,
        }),
        newColumn("display_name", {
          notNull: true,
        }),
        newColumn("description", {}),
        newColumn("version", {
          type: new Int64(),
        }),
        newColumn("projects", {
          type: new List(new Field("projects", new Utf8())),
        }),
        newColumn("sync_time", {
          type: new TimestampSecond("UTC"),
          incrementalKey: true,
        }),
      ],
    ),
    await ossDataToTable(
      `projects${options.suffix}`,
      projects.map((p) => {
        return _.merge(
          {
            sync_time: new Date(),
          },
          p,
        );
      }),
      [
        newColumn("name", {
          primaryKey: true,
          unique: true,
          notNull: true,
        }),
        newColumn("display_name", {
          notNull: true,
        }),
        newColumn("description", {}),
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
        newColumn("sync_time", {
          type: new TimestampSecond("UTC"),
          incrementalKey: true,
        }),
      ],
    ),
  ];

  return tables;
};
