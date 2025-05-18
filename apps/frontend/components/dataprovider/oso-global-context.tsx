import React, { ReactNode } from "react";
import { DataProvider, GlobalActionsProvider } from "@plasmicapp/loader-nextjs"; // or "@plasmicapp/loader-*""
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { ADT } from "ts-adt";
import * as config from "../../lib/config";
import { OsoAppClient } from "../../lib/clients/oso-app";
import { RegistrationProps } from "../../lib/types/plasmic";

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

const OsoGlobalActions: any = {
  updateMyUserProfile: { parameters: [{ name: "args", type: "object" }] },
  createApiKey: { parameters: [{ name: "args", type: "object" }] },
  deleteApiKey: { parameters: [{ name: "args", type: "object" }] },
  createOrganization: { parameters: [{ name: "args", type: "object" }] },
  addUserToOrganizationByEmail: {
    parameters: [{ name: "args", type: "object" }],
  },
  changeUserRole: { parameters: [{ name: "args", type: "object" }] },
  removeUserFromOrganization: {
    parameters: [{ name: "args", type: "object" }],
  },
  deleteOrganization: { parameters: [{ name: "args", type: "object" }] },
};

// Users will be able to set these props in Studio.
interface OsoGlobalContextProps {
  children?: ReactNode;
  errorCodeMap?: any; // Map of error codes to error messages
}

const OsoGlobalContextPropsRegistration: RegistrationProps<OsoGlobalContextProps> =
  {
    errorCodeMap: {
      type: "object",
      defaultValue: {},
      helpText: "Error code to message (e.g. {'23505': 'Duplicate username'})",
    },
  };

function OsoGlobalContext(props: OsoGlobalContextProps) {
  const { children, errorCodeMap } = props;
  const [actionResult, setResult] = React.useState<any>(null);
  const [actionError, setError] = React.useState<any>(null);
  const [snackbarState, setSnackbarState] = React.useState<SnackbarState>({
    _type: "closed",
  });
  const osoClient = new OsoAppClient();
  const data = {
    config,
    actionResult,
    actionError,
  };

  const handleSuccess = (result: any) => {
    setResult(result);
    setSnackbarState({ _type: "success" });
  };
  const handleError = (error: any) => {
    setError(error);
    setSnackbarState({
      _type: "error",
      ...error,
    });
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
        osoClient
          .updateMyUserProfile(args)
          .then(handleSuccess)
          .catch(handleError),
      createApiKey: (args: any) =>
        osoClient.createApiKey(args).then(handleSuccess).catch(handleError),
      deleteApiKey: (args: any) =>
        osoClient.deleteApiKey(args).then(handleSuccess).catch(handleError),
      createOrganization: (args: any) =>
        osoClient
          .createOrganization(args)
          .then(handleSuccess)
          .catch(handleError),
      addUserToOrganizationByEmail: (args: any) =>
        osoClient
          .addUserToOrganizationByEmail(args)
          .then(handleSuccess)
          .catch(handleError),
      changeUserRole: (args: any) =>
        osoClient.changeUserRole(args).then(handleSuccess).catch(handleError),
      removeUserFromOrganization: (args: any) =>
        osoClient
          .removeUserFromOrganization(args)
          .then(handleSuccess)
          .catch(handleError),
      deleteOrganization: (args: any) =>
        osoClient
          .deleteOrganization(args)
          .then(handleSuccess)
          .catch(handleError),
    }),
    [osoClient],
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
