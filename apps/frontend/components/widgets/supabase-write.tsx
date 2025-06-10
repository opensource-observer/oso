import React, { ReactNode } from "react";
import { useRouter } from "next/navigation";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { ADT } from "ts-adt";
import { HttpError, assertNever, spawn } from "@opensource-observer/utils";
import { usePostHog } from "posthog-js/react";
import { EVENTS } from "@/lib/types/posthog";
import { RegistrationProps } from "@/lib/types/plasmic";
import { useSupabaseState } from "@/components/hooks/supabase";

type SnackbarState = ADT<{
  closed: Record<string, unknown>;
  success: Record<string, unknown>;
  error: {
    code: string;
    message: string;
  };
}>;
type DbActionType = "insert" | "update" | "upsert" | "delete";
const REQUIRES_DATA: DbActionType[] = ["insert", "update", "upsert"];
const REQUIRES_FILTERS: DbActionType[] = ["update", "delete"];
const AUTO_HIDE_DURATION = 5000; // in milliseconds

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
  const [snackbarState, setSnackbarState] = React.useState<SnackbarState>({
    _type: "closed",
  });

  const handleClose = (
    _event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") {
      return;
    }
    setSnackbarState({ _type: "closed" });
  };
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
      setSnackbarState({ _type: "error", ...error });
      return;
      //throw error;
    } else if (status > 300) {
      throw new HttpError(`Invalid status code: ${status}`);
    }

    // Success!
    setSnackbarState({ _type: "success" });
    if (redirectOnComplete) {
      router.push(redirectOnComplete);
    } else {
      // router.refresh() will keep client-side state cached, and doesn't trigger refresh of queries
      //router.refresh();
      window.location.reload();
    }
  };

  return (
    <div>
      <div className={className} onClick={() => spawn(clickHandler())}>
        {children}
      </div>
      <Snackbar
        open={snackbarState._type !== "closed"}
        autoHideDuration={AUTO_HIDE_DURATION}
        onClose={handleClose}
      >
        <Alert
          onClose={handleClose}
          severity={
            snackbarState._type === "success"
              ? "success"
              : snackbarState._type === "error"
                ? "error"
                : "info"
          }
          variant="filled"
          sx={{ width: "100%" }}
        >
          {snackbarState._type === "success"
            ? "Done!"
            : snackbarState._type === "error"
              ? errorCodeMap[snackbarState.code] ??
                `${snackbarState.code}: ${snackbarState.message}`
              : ""}
        </Alert>
      </Snackbar>
    </div>
  );
}

export { SupabaseWriteRegistration, SupabaseWrite };
export type { SupabaseWriteProps };
