import React, { ReactNode } from "react";
import { DataProvider, GlobalActionsProvider } from "@plasmicapp/loader-nextjs"; // or "@plasmicapp/loader-*""
import * as config from "../../lib/config";
import { OsoAppClient } from "../../lib/clients/oso-app";

const PLASMIC_KEY = "globals";
const PLASMIC_CONTEXT_NAME = "OsoGlobalContext";

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
}

function OsoGlobalContext(props: OsoGlobalContextProps) {
  const { children } = props;
  const [actionResult, setResult] = React.useState<any>(null);
  const [actionError, setError] = React.useState<any>(null);
  const osoClient = new OsoAppClient();
  const data = {
    config,
    actionResult,
    actionError,
  };

  const actions = React.useMemo(
    () => ({
      updateMyUserProfile: (args: any) =>
        osoClient.updateMyUserProfile(args).then(setResult).catch(setError),
      createApiKey: (args: any) =>
        osoClient.createApiKey(args).then(setResult).catch(setError),
      deleteApiKey: (args: any) =>
        osoClient.deleteApiKey(args).then(setResult).catch(setError),
      createOrganization: (args: any) =>
        osoClient.createOrganization(args).then(setResult).catch(setError),
      addUserToOrganizationByEmail: (args: any) =>
        osoClient
          .addUserToOrganizationByEmail(args)
          .then(setResult)
          .catch(setError),
      changeUserRole: (args: any) =>
        osoClient.changeUserRole(args).then(setResult).catch(setError),
      removeUserFromOrganization: (args: any) =>
        osoClient
          .removeUserFromOrganization(args)
          .then(setResult)
          .catch(setError),
      deleteOrganization: (args: any) =>
        osoClient.deleteOrganization(args).then(setResult).catch(setError),
    }),
    [osoClient],
  );

  return (
    <GlobalActionsProvider contextName={PLASMIC_CONTEXT_NAME} actions={actions}>
      <DataProvider name={PLASMIC_KEY} data={data}>
        {children}
      </DataProvider>
    </GlobalActionsProvider>
  );
}

export { OsoGlobalContext, OsoGlobalActions };
