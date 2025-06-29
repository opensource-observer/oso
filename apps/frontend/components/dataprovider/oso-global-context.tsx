import React, { ReactNode } from "react";
import { DataProvider, GlobalActionsProvider } from "@plasmicapp/loader-nextjs"; // or "@plasmicapp/loader-*""
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { ADT } from "ts-adt";
import * as config from "@/lib/config";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";

const PLASMIC_KEY = "globals";
const PLASMIC_CONTEXT_NAME = "OsoGlobalContext";
const AUTO_HIDE_DURATION = 5000; // in milliseconds
const SUCCESS_MESSAGE = "Done!";

type SnackbarState = ADT<{
  closed: Record<string, unknown>;
  success: Record<string, unknown>;
  error: {
    code: string;
    message: string;
  };
}>;

type ExtractMethodNames<T> = {
  [K in keyof T]: T[K] extends (...args: any[]) => any ? K : never;
}[keyof T];
type ExtractMethods<T> = {
  [K in ExtractMethodNames<T>]: any;
};

const OsoGlobalActions: Partial<ExtractMethods<OsoAppClient>> = {
  updateMyUserProfile: { parameters: [{ name: "args", type: "object" }] },
  createApiKey: { parameters: [{ name: "args", type: "object" }] },
  deleteApiKey: { parameters: [{ name: "args", type: "object" }] },
  getApiKeysByOrgId: {
    parameters: [{ name: "args", type: "object" }],
  },
  createOrganization: { parameters: [{ name: "args", type: "object" }] },
  addUserToOrganizationByEmail: {
    parameters: [{ name: "args", type: "object" }],
  },
  changeUserRole: { parameters: [{ name: "args", type: "object" }] },
  removeUserFromOrganization: {
    parameters: [{ name: "args", type: "object" }],
  },
  deleteOrganization: { parameters: [{ name: "args", type: "object" }] },
  createChat: { parameters: [{ name: "args", type: "object" }] },
  updateChat: { parameters: [{ name: "args", type: "object" }] },
  deleteChat: { parameters: [{ name: "args", type: "object" }] },
  createSqlQuery: { parameters: [{ name: "args", type: "object" }] },
  updateSqlQuery: { parameters: [{ name: "args", type: "object" }] },
  deleteSqlQuery: { parameters: [{ name: "args", type: "object" }] },
  getConnectors: { parameters: [{ name: "args", type: "object" }] },
  getConnectorById: {
    parameters: [{ name: "args", type: "object" }],
  },
  createConnector: { parameters: [{ name: "args", type: "object" }] },
  deleteConnector: { parameters: [{ name: "args", type: "object" }] },
  syncConnector: {
    parameters: [{ name: "args", type: "object" }],
  },
  getDynamicConnectorAndContextsByOrgId: {
    parameters: [{ name: "args", type: "object" }],
  },
  getDynamicConnectorContexts: {
    parameters: [{ name: "args", type: "object" }],
  },
  upsertDynamicConnectorContexts: {
    parameters: [{ name: "args", type: "object" }],
  },
  getConnectorRelationships: {
    parameters: [{ name: "args", type: "object" }],
  },
  createConnectorRelationship: {
    parameters: [{ name: "args", type: "object" }],
  },
  deleteConnectorRelationship: {
    parameters: [{ name: "args", type: "object" }],
  },
};

// Users will be able to set these props in Studio.
interface OsoGlobalContextProps {
  children?: ReactNode;
  errorCodeMap?: any; // Map of error codes to error messages
}

const OsoGlobalContextPropsRegistration: any = {
  errorCodeMap: {
    type: "object",
    defaultValue: {},
    helpText: "Error code to message (e.g. {'23505': 'Duplicate username'})",
  },
};

function OsoGlobalContext(props: OsoGlobalContextProps) {
  const { children, errorCodeMap } = props;
  const { client } = useOsoAppClient();
  const [actionResult, setResult] = React.useState<any>(null);
  const [actionError, setError] = React.useState<any>(null);
  const [snackbarState, setSnackbarState] = React.useState<SnackbarState>({
    _type: "closed",
  });
  const data = {
    config,
    actionResult,
    actionError,
  };

  const handleSuccess = (result: any) => {
    console.log("Success: ", result);
    setResult(result);
    setSnackbarState({ _type: "success" });
    return result;
  };
  const handleError = (error: any) => {
    console.log("Error: ", error);
    setError(error);
    setSnackbarState({
      _type: "error",
      ...error,
    });
    return error;
  };
  const handleClose = (
    _event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") {
      return;
    }
    setSnackbarState({ _type: "closed" });
  };
  const actions = React.useMemo(
    () => ({
      updateMyUserProfile: (args: any) =>
        client!
          .updateMyUserProfile(args)
          .then(handleSuccess)
          .catch(handleError),
      createApiKey: (args: any) =>
        client!.createApiKey(args).then(handleSuccess).catch(handleError),
      deleteApiKey: (args: any) =>
        client!.deleteApiKey(args).then(handleSuccess).catch(handleError),
      getApiKeysByOrgId: (args: any) =>
        client!.getApiKeysByOrgId(args).then(handleSuccess).catch(handleError),
      createOrganization: (args: any) =>
        client!.createOrganization(args).then(handleSuccess).catch(handleError),
      addUserToOrganizationByEmail: (args: any) =>
        client!
          .addUserToOrganizationByEmail(args)
          .then(handleSuccess)
          .catch(handleError),
      changeUserRole: (args: any) =>
        client!.changeUserRole(args).then(handleSuccess).catch(handleError),
      removeUserFromOrganization: (args: any) =>
        client!
          .removeUserFromOrganization(args)
          .then(handleSuccess)
          .catch(handleError),
      deleteOrganization: (args: any) =>
        client!.deleteOrganization(args).then(handleSuccess).catch(handleError),
      createChat: (args: any) =>
        client!.createChat(args).then(handleSuccess).catch(handleError),
      updateChat: (args: any) =>
        client!.updateChat(args).then(handleSuccess).catch(handleError),
      deleteChat: (args: any) =>
        client!.deleteChat(args).then(handleSuccess).catch(handleError),
      createSqlQuery: (args: any) =>
        client!.createSqlQuery(args).then(handleSuccess).catch(handleError),
      updateSqlQuery: (args: any) =>
        client!.updateSqlQuery(args).then(handleSuccess).catch(handleError),
      deleteSqlQuery: (args: any) =>
        client!.deleteSqlQuery(args).then(handleSuccess).catch(handleError),
      getConnectors: (args: any) =>
        client!.getConnectors(args).then(handleSuccess).catch(handleError),
      getConnectorById: (args: any) =>
        client!.getConnectorById(args).then(handleSuccess).catch(handleError),
      createConnector: (args: any) =>
        client!.createConnector(args).then(handleSuccess).catch(handleError),
      deleteConnector: (args: any) =>
        client!.deleteConnector(args).then(handleSuccess).catch(handleError),
      syncConnector: (args: any) =>
        client!.syncConnector(args).then(handleSuccess).catch(handleError),
      getDynamicConnectorAndContextsByOrgId: (args: any) =>
        client!
          .getDynamicConnectorAndContextsByOrgId(args)
          .then(handleSuccess)
          .catch(handleError),
      getDynamicConnectorContexts: (args: any) =>
        client!
          .getDynamicConnectorContexts(args)
          .then(handleSuccess)
          .catch(handleError),
      upsertDynamicConnectorContexts: (args: any) =>
        client!
          .upsertDynamicConnectorContexts(args)
          .then(handleSuccess)
          .catch(handleError),
      getConnectorRelationships: (args: any) =>
        client!
          .getConnectorRelationships(args)
          .then(handleSuccess)
          .catch(handleError),
      createConnectorRelationship: (args: any) =>
        client!
          .createConnectorRelationship(args)
          .then(handleSuccess)
          .catch(handleError),
      deleteConnectorRelationship: (args: any) =>
        client!
          .deleteConnectorRelationship(args)
          .then(handleSuccess)
          .catch(handleError),
    }),
    [client],
  );

  return (
    <GlobalActionsProvider contextName={PLASMIC_CONTEXT_NAME} actions={actions}>
      <DataProvider name={PLASMIC_KEY} data={data}>
        {children}
      </DataProvider>
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
            ? SUCCESS_MESSAGE
            : snackbarState._type === "error"
              ? errorCodeMap[snackbarState.code] ??
                `${snackbarState.code}: ${snackbarState.message}`
              : ""}
        </Alert>
      </Snackbar>
    </GlobalActionsProvider>
  );
}

export {
  OsoGlobalContext,
  OsoGlobalActions,
  OsoGlobalContextPropsRegistration,
};
