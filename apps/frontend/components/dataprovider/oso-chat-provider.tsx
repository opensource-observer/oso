import React from "react";
import {
  CommonDataProviderProps,
  CommonDataProviderRegistration,
  DataProviderView,
} from "./provider-view";
import { useSupabaseState } from "../hooks/supabase";
import { useChat, Message } from "@ai-sdk/react";

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

const OsoChatProviderRegistration: any = {
  ...CommonDataProviderRegistration,
  agentName: {
    type: "string",
    helpText: "The agent's name (e.g. function_text2sql)",
  },
};

interface OsoChatActions {
  handleInputChange(
    event:
      | React.ChangeEvent<HTMLInputElement>
      | React.ChangeEvent<HTMLTextAreaElement>,
  ): void;
  handleSubmit(event?: { preventDefault?: () => void }): void;
  setMessages(messages: Message[]): void;
}

const OsoChatProvider = React.forwardRef<OsoChatActions>(
  function OsoChatProvider(props: OsoChatProviderProps, ref) {
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

    const {
      messages,
      input,
      status,
      handleInputChange,
      handleSubmit,
      setMessages,
    } = useChat({
      api: CHAT_PATH,
      headers: headers,
    });
    React.useImperativeHandle(
      ref,
      () => ({
        handleInputChange(
          event:
            | React.ChangeEvent<HTMLInputElement>
            | React.ChangeEvent<HTMLTextAreaElement>,
        ) {
          handleInputChange(event);
        },
        handleSubmit(event?: { preventDefault?: () => void }) {
          handleSubmit(event);
        },
        setMessages(messages: Message[]) {
          setMessages(messages);
        },
      }),
      [session],
    );

    const key = variableName ?? DEFAULT_PLASMIC_KEY;
    const displayMessages = useTestData ? testData : messages;
    //console.log(data);
    //console.log(JSON.stringify(data, null, 2));
    //console.log(error);

    return (
      <DataProviderView
        {...props}
        variableName={key}
        formattedData={{
          input,
          status,
          messages: displayMessages,
        }}
        loading={false}
      />
    );
  },
);

export { OsoChatProviderRegistration, OsoChatProvider };
export type { OsoChatProviderProps };
