import React from "react";
import { useChat } from "@ai-sdk/react";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "@/components/dataprovider/provider-view";
import { RegistrationProps } from "@/lib/types/plasmic";
import { useSupabaseState } from "@/components/hooks/supabase";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { logger } from "@/lib/logger";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_PLASMIC_KEY = "osoChat";
const CHAT_PATH = "/api/v1/chat";

/**
 * OSO app client
 */
type OsoChatProviderProps = CommonDataProviderProps & {
  // The agent that we want to talk to
  agentName?: string;
  // The chat_history row to save to
  chatId?: string;
};

const OsoChatProviderRegistration: RegistrationProps<OsoChatProviderProps> = {
  ...CommonDataProviderRegistration,
  agentName: {
    type: "string",
    helpText: "The agent's name (e.g. function_text2sql)",
  },
  chatId: {
    type: "string",
    helpText: "The chat 'id' to save to in Supabase",
  },
};

function OsoChatProvider(props: OsoChatProviderProps) {
  const { agentName, chatId, variableName, useTestData } = props;
  const supabaseState = useSupabaseState();
  const [firstLoad, setFirstLoad] = React.useState<boolean>(true);
  const { client } = useOsoAppClient();
  const session =
    supabaseState._type === "loggedIn" ? supabaseState.session : null;
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

  React.useEffect(() => {
    if (useTestData || !chatId || !client) {
      // Short circuit if not saving data
      return;
    }

    // Load the history from Supabase on first load
    if (firstLoad) {
      client
        .getChatById({ chatId })
        .then((c) => {
          setFirstLoad(false);
          //console.log(c.data);
          if (c.data) {
            chatData.setMessages(JSON.parse(c.data));
          }
        })
        .catch((e) => {
          logger.error(`Error loading chat: ${e}`);
        });
    } else if (chatData.messages) {
      // Save the chat messages if they change
      client
        .updateChat({
          id: chatId,
          updated_at: new Date().toISOString(),
          data: JSON.stringify(chatData.messages),
        })
        .then(() => {
          console.log(`Saved chat ${chatId} to 'chat_history'`);
        })
        .catch((e) => {
          logger.error(`Error saving chat: ${e}`);
        });
    }
  }, [firstLoad, client, useTestData, chatId, chatData.messages]);

  const key = variableName ?? DEFAULT_PLASMIC_KEY;
  //console.log(data);
  //console.log(JSON.stringify(data, null, 2));
  //console.log(error);

  return (
    <DataProviderView
      {...props}
      variableName={key}
      formattedData={{
        ...chatData,
        messages: chatData.messages,
      }}
      loading={false}
    />
  );
}

export { OsoChatProviderRegistration, OsoChatProvider };
export type { OsoChatProviderProps };
