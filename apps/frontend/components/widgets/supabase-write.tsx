import React, { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { toast, ExternalToast } from "sonner";
import { HttpError, assertNever, spawn } from "@opensource-observer/utils";
import { usePostHog } from "posthog-js/react";
import { EVENTS } from "@/lib/types/posthog";
import { RegistrationProps } from "@/lib/types/plasmic";
import { useSupabaseState } from "@/components/hooks/supabase";

type DbActionType = "insert" | "update" | "upsert" | "delete";
const REQUIRES_DATA: DbActionType[] = ["insert", "update", "upsert"];
const REQUIRES_FILTERS: DbActionType[] = ["update", "delete"];
const DEFAULT_TOAST_OPTIONS: ExternalToast = {
  closeButton: true,
  duration: 5000, // in milliseconds
};
const SUCCESS_MESSAGE = "Done!";

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
  redirectOnComplete?: string; // URL to redirect to after completion;
  errorCodeMap?: any; // Map of error codes to error messages
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
  redirectOnComplete: "string",
  errorCodeMap: {
    type: "object",
    defaultValue: {},
    helpText: "Error code to message (e.g. {'23505': 'Duplicate username'})",
  },
};

function SupabaseWrite(props: SupabaseWriteProps) {
  // These props are set in the Plasmic Studio
  const {
    className,
    children,
    actionType,
    tableName,
    data,
    filters,
    redirectOnComplete,
    errorCodeMap,
  } = props;
  const posthog = usePostHog();
  const supabaseState = useSupabaseState();
  const router = useRouter();

  const clickHandler = async () => {
    if (!supabaseState?.supabaseClient) {
      return console.warn("SupabaseWrite: Supabase client not initialized yet");
    } else if (!actionType) {
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
    const supabaseClient = supabaseState.supabaseClient;

    let query =
      actionType === "insert"
        ? supabaseClient.from(tableName as any).insert(data)
        : actionType === "update"
          ? supabaseClient.from(tableName as any).update(data)
          : actionType === "upsert"
            ? supabaseClient.from(tableName as any).upsert(data)
            : actionType === "delete"
              ? supabaseClient.from(tableName as any).delete()
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
    posthog.capture(EVENTS.DB_WRITE, {
      tableName,
      actionType,
      status,
    });
    if (error) {
      console.warn("SupabaseWrite error: ", error);
      toast.error(
        errorCodeMap[error.code] ?? `${error.code}: ${error.message}`,
        DEFAULT_TOAST_OPTIONS,
      );
      return;
      //throw error;
    } else if (status > 300) {
      throw new HttpError(`Invalid status code: ${status}`);
    }

    // Success!
    toast.success(SUCCESS_MESSAGE, DEFAULT_TOAST_OPTIONS);
    if (redirectOnComplete) {
      router.push(redirectOnComplete);
    } else {
      // router.refresh() will keep client-side state cached, and doesn't trigger refresh of queries
      //router.refresh();
      window.location.reload();
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
