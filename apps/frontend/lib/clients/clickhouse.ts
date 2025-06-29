import { createClient } from "@clickhouse/client";
import {
  CLICKHOUSE_DB_NAME,
  CLICKHOUSE_PASSWORD,
  CLICKHOUSE_URL,
  CLICKHOUSE_USERNAME,
} from "@/lib/config";

export function getClickhouseClient() {
  return createClient({
    url: CLICKHOUSE_URL,
    username: CLICKHOUSE_USERNAME,
    password: CLICKHOUSE_PASSWORD,
    database: CLICKHOUSE_DB_NAME,
    clickhouse_settings: {
      date_time_output_format: "iso",
    },
  });
}
