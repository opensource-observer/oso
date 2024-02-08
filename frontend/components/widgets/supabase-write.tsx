import React, { ReactNode } from "react";
import { RegistrationProps } from "../../lib/types/plasmic";
import { HttpError } from "../../lib/types/errors";
import { assertNever, spawn } from "../../lib/common";
import { supabaseClient } from "../../lib/clients/supabase";

type DbActionType = "insert" | "update" | "upsert" | "delete";
const REQUIRES_DATA: DbActionType[] = ["insert", "update", "upsert"];
const REQUIRES_FILTERS: DbActionType[] = ["update", "delete"];

/**
 * Generic Supabase write component.
 *
 * Current limitations:
 * - Only supports click handlers
 */
type SupabaseWriteProps = {
  className?: string; // Plasmic CSS class
  children?: ReactNode; // Show this
  actionType?: DbActionType; // Selector for what to do on click
  tableName?: string;
  data?: any; // Data to insert
  filters?: any; // A list of filters, where each filter is `[ column, operator, value ]`
  // See https://supabase.com/docs/reference/javascript/filter
  // e.g. [ [ "address", "eq", "0xabc123" ] ]
};

const SupabaseWriteRegistration: RegistrationProps<SupabaseWriteProps> = {
  children: "slot",
  actionType: {
    type: "choice",
    options: ["insert", "update", "upsert", "delete"],
  },
  tableName: {
    type: "string",
    helpText: "Supabase table name",
  },
  data: {
    type: "object",
    defaultValue: {},
    helpText: "Data to insert",
  },
  filters: {
    type: "object",
    defaultValue: [],
    helpText: "e.g. [['id', 'lt', 10], ['name', 'eq', 'foobar']]",
    hidden: (props) =>
      props.actionType === "insert" || props.actionType === "upsert",
  },
};

function SupabaseWrite(props: SupabaseWriteProps) {
  // These props are set in the Plasmic Studio
  const { className, children, actionType, tableName, data, filters } = props;

  const clickHandler = async () => {
    if (!actionType) {
      return console.warn("SupabaseWrite: Select an actionType first");
    } else if (!tableName) {
      return console.warn("SupabaseWrite: Enter a tableName first");
    } else if (REQUIRES_DATA.includes(actionType) && !data) {
      return console.warn("SupabaseWrite: Enter valid data first");
    } else if (REQUIRES_FILTERS.includes(actionType) && !filters) {
      return console.warn(
        "SupabaseWrite: This actionType requires valid filters",
      );
    }

    let query =
      actionType === "insert"
        ? supabaseClient.from(tableName).insert(data)
        : actionType === "update"
          ? supabaseClient.from(tableName).update(data)
          : actionType === "upsert"
            ? supabaseClient.from(tableName).upsert(data)
            : actionType === "delete"
              ? supabaseClient.from(tableName).delete()
              : assertNever(actionType);

    // Iterate over the filters
    if (Array.isArray(filters)) {
      for (let i = 0; i < filters.length; i++) {
        const f = filters[i];
        if (!Array.isArray(f) || f.length < 3) {
          console.warn(`Invalid supabase filter: ${f}`);
          continue;
        }
        query = query.filter(f[0], f[1], f[2]);
      }
    }

    // Execute query
    const { error, status } = await query;
    if (error) {
      throw error;
    } else if (status > 300) {
      throw new HttpError(`Invalid status code: ${status}`);
    }
  };

  return (
    <div className={className} onClick={() => spawn(clickHandler())}>
      {children}
    </div>
  );
}

export { SupabaseWriteRegistration, SupabaseWrite };
export type { SupabaseWriteProps };
