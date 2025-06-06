import React from "react";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "./provider-view";
import { RegistrationProps } from "../../lib/types/plasmic";
import { useSupabaseState } from "../hooks/supabase";
import { useChat } from "@ai-sdk/react";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_PLASMIC_KEY = "osoChat";
const CHAT_PATH = "/api/v1/chat";

/**
 * OSO app client
 */
type OsoChatProviderProps = CommonDataProviderProps & {
  // The agent that we want to talk to
  agentName?: string;
};

const OsoChatProviderRegistration: RegistrationProps<OsoChatProviderProps> = {
  ...CommonDataProviderRegistration,
  agentName: {
    type: "string",
    helpText: "The agent's name (e.g. function_text2sql)",
  },
};

function OsoChatProvider(props: OsoChatProviderProps) {
  const { agentName, variableName, testData, useTestData } = props;
  const supabaseState = useSupabaseState();
  const session = supabaseState?.session;
  const headers: Record<string, string> = {};

  if (session) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }
  if (agentName) {
    headers["X-AgentName"] = agentName;
  }

  const chatData = useChat({
    api: CHAT_PATH,
    headers: headers,
  });

  const key = variableName ?? DEFAULT_PLASMIC_KEY;
  const displayMessages = useTestData ? testData : chatData.messages;
  //console.log(data);
  //console.log(JSON.stringify(data, null, 2));
  //console.log(error);

  return (
    <DataProviderView
      {...props}
      variableName={key}
      formattedData={{
        ...chatData,
        messages: displayMessages,
      }}
      loading={false}
    />
  );
}

export { OsoChatProviderRegistration, OsoChatProvider };
export type { OsoChatProviderProps };
