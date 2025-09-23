import React, { ReactNode } from "react";
import {
  GlobalContextMeta,
  DataProvider,
  GlobalActionsProvider,
} from "@plasmicapp/loader-nextjs";
import _ from "lodash";
import { toast, ExternalToast } from "sonner";
import * as config from "@/lib/config";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";

const PLASMIC_KEY = "globals";
const PLASMIC_CONTEXT_NAME = "OsoGlobalContext";
const DEFAULT_TOAST_OPTIONS: ExternalToast = {
  closeButton: true,
  duration: 5000, // in milliseconds
};
const SUCCESS_MESSAGE = "Done!";

type ExtractMethodNames<T> = {
  [K in keyof T]: T[K] extends (...args: any[]) => any ? K : never;
}[keyof T];
type ExtractMethods<T> = {
  [K in ExtractMethodNames<T>]: any;
};

const OsoGlobalActionNames: ExtractMethodNames<OsoAppClient>[] = [
  "getUser",
  "getMyUserProfile",
  "updateMyUserProfile",
  "createApiKey",
  "getMyApiKeys",
  "getApiKeysByOrgName",
  "deleteApiKeyById",
  "createOrganization",
  "getMyOrganizations",
  "getOrganizationById",
  "getOrganizationByName",
  "getOrganizationMembers",
  "addUserToOrganizationByEmail",
  "changeUserRole",
  "removeUserFromOrganization",
  "deleteOrganizationByName",
  "createChat",
  "getChatsByOrgName",
  "getChatById",
  "updateChat",
  "deleteChatById",
  "createNotebook",
  "forkNotebook",
  "getNotebooksByOrgName",
  "getNotebookById",
  "getNotebookByName",
  "moveNotebook",
  "updateNotebook",
  "deleteNotebookById",
  "getOrganizationCredits",
  "getOrganizationCreditTransactions",
  "getConnectors",
  "getConnectorById",
  "createConnector",
  "deleteConnector",
  "syncConnector",
  "getDynamicConnectorAndContextsByOrgId",
  "getDynamicConnectorContexts",
  "upsertDynamicConnectorContexts",
  "getConnectorRelationships",
  "createConnectorRelationship",
  "deleteConnectorRelationship",
  "buyCredits",
  "getCreditPackages",
  "getMyPurchaseHistory",
  "createInvitation",
  "listInvitationsForOrg",
  "acceptInvitation",
  "deleteInvitation",
  "getInviteById",
  "checkResourcePermission",
  "grantResourcePermission",
  "revokeResourcePermission",
  "makeResourcePublic",
  "makeResourcePrivate",
  "listResourcePermissions",
];
const OsoGlobalActions: Partial<ExtractMethods<OsoAppClient>> = _.fromPairs(
  OsoGlobalActionNames.map((name) => [
    name,
    { parameters: [{ name: "args", type: "object" }] },
  ]),
);

// Users will be able to set these props in Studio.
interface OsoGlobalContextProps {
  children?: ReactNode;
  errorCodeMap?: any; // Map of error codes to error messages
}

const OsoGlobalContextMeta: GlobalContextMeta<OsoGlobalContextProps> = {
  name: "OsoGlobalContext",
  props: {
    errorCodeMap: {
      type: "object",
      defaultValue: {},
      helpText: "Error code to message (e.g. {'23505': 'Duplicate username'})",
    },
  },
  globalActions: OsoGlobalActions,
};

function OsoGlobalContext(props: OsoGlobalContextProps) {
  const { children, errorCodeMap } = props;
  const { client } = useOsoAppClient();
  const [actionResult, setResult] = React.useState<any>(null);
  const [actionError, setError] = React.useState<any>(null);

  const data = {
    config,
    actionResult,
    actionError,
  };

  const handleSuccess = (result: any) => {
    console.log("Success: ", result);
    setResult(result);
    toast.success(SUCCESS_MESSAGE, DEFAULT_TOAST_OPTIONS);
    return result;
  };
  const handleError = (error: any) => {
    console.log("Error: ", error);
    setError(error);
    toast.error(
      errorCodeMap[error.code] ?? `${error.code}: ${error.message}`,
      DEFAULT_TOAST_OPTIONS,
    );
    return error;
  };

  const actions = React.useMemo(
    () =>
      _.fromPairs(
        OsoGlobalActionNames.map((method) => [
          method,
          (args: any) =>
            client![method](args).then(handleSuccess).catch(handleError),
        ]),
      ),
    [client],
  );

  return (
    <GlobalActionsProvider contextName={PLASMIC_CONTEXT_NAME} actions={actions}>
      <DataProvider name={PLASMIC_KEY} data={data}>
        {children}
      </DataProvider>
    </GlobalActionsProvider>
  );
}

export { OsoGlobalContext, OsoGlobalContextMeta };
