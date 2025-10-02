"use client";

import { useCallback, useEffect, useReducer } from "react";
import { compressToEncodedURIComponent } from "lz-string";
import { newMessagePortRpcSession } from "capnweb";
import {
  InitializationCommand,
  NotebookControls,
  NotebookControlsStub,
  NotebookHostControls,
} from "@/lib/notebook/notebook-controls";
import { logger } from "@/lib/logger";
import { NotebookHostRpc } from "@/lib/notebook/notebook-host-rpc";

interface ControllableNotebookProps {
  className?: string; // Plasmic CSS class
  initialCode?: string;
  notebookId: string;
  notebookUrl: string;
  environment: Record<string, string>;
  aiPrompt?: string;
  enablePostMessageStore?: boolean;
  onNotebookConnected: (rpcSession: NotebookControlsStub) => void;
  hostControls: NotebookHostControls;
  enableDebug?: boolean;
}

interface RequestConnectionOptions {
  hostRpc: NotebookHostRpc;
  notebookHostId: string;
  notebookUrl: string;
  iframe: HTMLIFrameElement;
}

function requestConnection(options: RequestConnectionOptions) {
  const { hostRpc, notebookHostId, notebookUrl, iframe } = options;
  const messageChannel = new MessageChannel();
  if (!iframe.contentWindow) {
    return;
  }
  console.log("Requesting connection to notebook iframe");

  newMessagePortRpcSession(messageChannel.port1, hostRpc);

  iframe.contentWindow.postMessage(
    {
      command: "requestConnection",
      id: notebookHostId,
    },
    new URL(notebookUrl).origin,
  );
}

type NotebookConnectionState =
  | "INITIAL"
  | "LOADING"
  | "CONNECTING"
  | "CONNECTED";

interface NotebookDetails {
  notebookId: string;
  notebookUrl: string;
}

type CleanUpFunction = () => void;

type ConnectionStateUpdate = {
  iframe?: HTMLIFrameElement | null;
  state: NotebookConnectionState;
  transitionCleanUp?: CleanUpFunction;
  appendUnloadCleanUp?: CleanUpFunction[];
};

class ConnectionState {
  private iframe: HTMLIFrameElement | null;
  private _state: NotebookConnectionState;
  private _transitionCleanUp: CleanUpFunction;
  private _unloadCleanUp: CleanUpFunction[];
  private _hostRpc: NotebookHostRpc;
  private _notebookHostId: string;

  private onNotebookConnectedListener:
    | ((session: NotebookControlsStub) => void)
    | null = null;

  constructor(hostRpc: NotebookHostRpc) {
    this.iframe = null;
    this._state = "INITIAL";
    this._transitionCleanUp = () => {};
    this._unloadCleanUp = [];
    this.onNotebookConnectedListener = null;
    this._hostRpc = hostRpc;

    // We set a unique id for each instance of the notebook to avoid collisions if
    // there are multiple notebooks rendered at once. This allows us to have
    // multiple independent notebooks on the same page. This is a purely ephemeral
    // value that is not to be persisted in a database, it's purely for the client
    // side.
    this._notebookHostId = crypto.randomUUID();
  }

  get state() {
    return this._state;
  }

  get hostRpc() {
    return this._hostRpc;
  }

  get notebookHostId() {
    return this._notebookHostId;
  }

  addOnNotebookConnectedListener(
    listener: (session: NotebookControlsStub) => void,
  ) {
    this.onNotebookConnectedListener = listener;
  }

  removeOnNotebookConnectedListener() {
    this.onNotebookConnectedListener = null;
  }

  emitNotebookConnected(session: NotebookControlsStub) {
    if (this.onNotebookConnectedListener) {
      this.onNotebookConnectedListener(session);
    }
  }

  transitionCleanUp() {
    this._transitionCleanUp();
    this._transitionCleanUp = () => {};
  }

  unloadCleanUp() {
    this._unloadCleanUp.forEach((fn) => fn());
    this._unloadCleanUp = [];
  }

  update(update: ConnectionStateUpdate) {
    if (update.iframe !== undefined) {
      this.iframe = update.iframe;
    }
    if (update.state !== undefined) {
      this._state = update.state;
    }
    if (update.transitionCleanUp !== undefined) {
      this._transitionCleanUp = update.transitionCleanUp;
    }
    if (update.appendUnloadCleanUp !== undefined) {
      this._unloadCleanUp.push(...update.appendUnloadCleanUp);
    }
    return this;
  }

  reset() {
    this.transitionCleanUp();
    this.unloadCleanUp();
    this.iframe = null;
    this._state = "INITIAL";
  }

  setRpcHandler(handler: NotebookHostControls) {
    this._hostRpc.setHandler(handler);
  }
}

type ConnectingAction = {
  state: "CONNECTING";
  iframe: HTMLIFrameElement;
  notebookDetails: NotebookDetails;
  dispatch: React.Dispatch<ConnectionAction>;
};

type LoadingAction = {
  state: "LOADING";
  iframe: HTMLIFrameElement;
  notebookDetails: NotebookDetails;
  dispatch: React.Dispatch<ConnectionAction>;
};

type ConnectedAction = {
  state: "CONNECTED";
  iframe: HTMLIFrameElement;
  notebookDetails: NotebookDetails;
  session: NotebookControlsStub;
  sendPort: MessagePort;
  recvPort: MessagePort;
  dispatch: React.Dispatch<ConnectionAction>;
};

type InitialAction = {
  state: "INITIAL";
  iframe: null;
  notebookDetails: NotebookDetails;
  dispatch: React.Dispatch<ConnectionAction>;
};

function createInitialState(): ConnectionState {
  return new ConnectionState(new NotebookHostRpc());
}

type ConnectionAction =
  | ConnectingAction
  | LoadingAction
  | ConnectedAction
  | InitialAction;

type StateTransition<T extends ConnectionAction> = (
  state: ConnectionState,
  action: T,
) => ConnectionState;

interface NotebookStateTransitions {
  LOADING: StateTransition<LoadingAction>;
  CONNECTING: StateTransition<ConnectingAction>;
  CONNECTED: StateTransition<ConnectedAction>;
  INITIAL: StateTransition<InitialAction>;
}

function validStateTransition<T extends ConnectionAction>(
  fn: StateTransition<T>,
): StateTransition<T> {
  return (state: ConnectionState, action: T): ConnectionState => {
    // Clean up the previous state
    state.transitionCleanUp();
    // Call wrapped state transition
    return fn(state, action);
  };
}

const loadingState = validStateTransition(
  (state: ConnectionState, action: LoadingAction) => {
    // Any time the iframe load event is triggered we must start trying to connect
    // to the iframe by triggering the CONNECTING state
    const handleLoad = () => {
      action.dispatch({
        state: "CONNECTING",
        iframe: action.iframe!,
        dispatch: action.dispatch,
        notebookDetails: action.notebookDetails,
      });
    };
    action.iframe.addEventListener("load", handleLoad);
    return state.update({
      iframe: action.iframe,
      state: "LOADING",
      transitionCleanUp: () => {},
      appendUnloadCleanUp: [
        () => {
          action.iframe.removeEventListener("load", handleLoad);
        },
      ],
    });
  },
);

function invalidStateTransition(
  from: NotebookConnectionState,
  to: NotebookConnectionState,
): StateTransition<any> {
  return () => {
    throw new Error(`Invalid state transition from ${from} to ${to}`);
  };
}

const resetToInitialState = validStateTransition(
  (state: ConnectionState, _action: InitialAction) => {
    // Completely unload the iframe and reset to initial state
    state.reset();
    return state;
  },
);

const reconnectingState = validStateTransition(
  (state: ConnectionState, action: ConnectingAction) => {
    // Start trying to connect to the iframe
    const { notebookUrl } = action.notebookDetails;
    const { hostRpc, notebookHostId } = state;
    const iframe = action.iframe;
    const connectionInterval = setInterval(() => {
      requestConnection({ hostRpc, notebookHostId, notebookUrl, iframe });
    }, 500);

    // Listen for the iframe to respond
    const handleConnectionResponse = (event: MessageEvent<any>) => {
      if (event.source !== iframe.contentWindow) {
        return;
      }
      if (!event.data || !event.data.command || !event.data.id) {
        return;
      }

      if (event.data.command === "initialize") {
        const command = event.data as InitializationCommand;

        if (!command.recvPort) {
          logger.error("No recvPort provided in initialize command");
          return;
        }
        if (!command.sendPort) {
          logger.error("No sendPort provided in initialize command");
          return;
        }

        const sendPort: MessagePort = command.sendPort;
        const session = newMessagePortRpcSession<NotebookControls>(sendPort);

        // Listen on the recvPort
        newMessagePortRpcSession(command.recvPort, hostRpc);

        // Once the session is ready we notify the parent component

        // Stop listening for messages once we've connected
        window.removeEventListener("message", handleConnectionResponse);

        // Stop the connection retry interval
        if (connectionInterval) {
          clearInterval(connectionInterval);
        }

        action.dispatch({
          state: "CONNECTED",
          iframe: action.iframe,
          notebookDetails: action.notebookDetails,
          session,
          sendPort: command.sendPort,
          recvPort: command.recvPort,
          dispatch: action.dispatch,
        });
      }
    };
    window.addEventListener("message", handleConnectionResponse);

    return state.update({
      iframe: action.iframe,
      state: "CONNECTING",
      transitionCleanUp: () => {
        clearInterval(connectionInterval);
        window.removeEventListener("message", handleConnectionResponse);
      },
    });
  },
);

const notebookStateMachine: Record<
  NotebookConnectionState,
  NotebookStateTransitions
> = {
  INITIAL: {
    LOADING: loadingState,
    CONNECTING: invalidStateTransition("INITIAL", "CONNECTING"),
    CONNECTED: invalidStateTransition("INITIAL", "CONNECTED"),
    INITIAL: validStateTransition((state) => state),
  },
  LOADING: {
    LOADING: (state) => state, // No-op if already loading
    CONNECTING: reconnectingState,
    CONNECTED: invalidStateTransition("LOADING", "CONNECTED"),
    INITIAL: resetToInitialState,
  },
  CONNECTING: {
    LOADING: invalidStateTransition("CONNECTING", "LOADING"),
    CONNECTING: reconnectingState,
    CONNECTED: validStateTransition((state, action) => {
      // Notify the parent component that the notebook is connected
      state.emitNotebookConnected(action.session);

      // Successfully connected to the iframe
      return state.update({
        iframe: action.iframe,
        state: "CONNECTED",
        transitionCleanUp: () => {
          // Stop listening on the ports if we start unloading the iframe
          action.recvPort.close();
          action.sendPort.close();
        },
      });
    }),
    INITIAL: resetToInitialState,
  },
  CONNECTED: {
    LOADING: invalidStateTransition("CONNECTED", "LOADING"),
    CONNECTING: reconnectingState,
    CONNECTED: invalidStateTransition("CONNECTED", "CONNECTED"),
    INITIAL: resetToInitialState,
  },
};

function changeConnectingState(
  state: ConnectionState,
  action: ConnectionAction,
): ConnectionState {
  const currentState = notebookStateMachine[state.state];
  switch (action.state) {
    case "LOADING":
      currentState.LOADING(state, action);
      break;
    case "CONNECTING":
      currentState.CONNECTING(state, action);
      break;
    case "CONNECTED":
      currentState.CONNECTED(state, action);
      break;
    case "INITIAL":
      currentState.INITIAL(state, action);
      break;
    default:
      throw new Error(`Unknown action: ${action}`);
  }
  return state;
}

// Very specific hook for controlling the state of the connection to the notebook
function useNotebookConnection(
  onNotebookConnected: (rpcSession: NotebookControlsStub) => void,
): [ConnectionState, React.Dispatch<ConnectionAction>] {
  const [connectionState, updateConnectionState] = useReducer(
    changeConnectingState,
    createInitialState(),
  );

  // If for whatever reason the onNotebookConnected changes we need to update
  // the state event listener
  const onNotebookConnectedCallback = useCallback(
    (session: NotebookControlsStub) => {
      onNotebookConnected(session);
    },
    [onNotebookConnected],
  );

  useEffect(() => {
    connectionState.addOnNotebookConnectedListener(onNotebookConnectedCallback);
    return () => {
      connectionState.removeOnNotebookConnectedListener();
    };
  }, [onNotebookConnected]);

  return [connectionState, updateConnectionState];
}

function generateNotebooklUrl(
  notebookUrl: string,
  notebookId: string,
  initialCode: string | undefined,
  environment: Record<string, string>,
  aiPrompt: string | undefined,
  enablePostMessageStore: boolean,
  enableDebug: boolean,
) {
  const envString = compressToEncodedURIComponent(JSON.stringify(environment));
  // Generate query params
  const queryParams = new URLSearchParams();
  if (aiPrompt) {
    queryParams.append("aiPrompt", aiPrompt);
  }
  if (initialCode) {
    queryParams.append("code", initialCode);
  }
  queryParams.append("env", envString);

  if (enablePostMessageStore) {
    queryParams.append("enablePostMessageStore", "true");
  }
  if (enableDebug) {
    queryParams.append("enableDebug", "true");
  }

  const queryString = queryParams.toString();
  const fullNotebookUrl = `${notebookUrl}?notebook=${notebookId}#${queryString}`;

  return fullNotebookUrl;
}

/**
 * A very generic notebook component that renders a marimo notebook that we can
 * control. This component does not have any supabase or other specific logic so
 * we can easily embed/test this in a storybook or other environment. This
 * component uses a state machine to handle the complex state required to setup
 * the connection to the iframe used to load the notebook. The state machine is
 * defined in the `notebookStateMachine` object. Much of the state machine is
 * dedicated to managing the connection lifecycle and ensuring that the notebook
 * is properly initialized and ready for use.
 *
 * @param props ControllableNotebookProps
 */
function ControllableNotebook(props: ControllableNotebookProps) {
  const {
    className,
    initialCode,
    notebookUrl,
    environment,
    aiPrompt,
    enablePostMessageStore = true,
    enableDebug = false,
    onNotebookConnected,
    hostControls: handler,
    notebookId,
  } = props;
  // We only need to set the hostRpc once, we can reconnect to different iframes
  // as needed
  const [connectionState, updateConnectionState] =
    useNotebookConnection(onNotebookConnected);

  useEffect(() => {
    connectionState.setRpcHandler(handler);
  }, [handler]);

  const refCallback = useCallback(
    (iframe: HTMLIFrameElement | null) => {
      const notebookDetails: NotebookDetails = {
        notebookId,
        notebookUrl,
      };
      // If the iframe is null we reset to the initial state as we are unloading
      // the iframe
      if (!iframe) {
        updateConnectionState({
          state: "INITIAL",
          iframe: null,
          dispatch: updateConnectionState,
          notebookDetails,
        });
        return;
      }
      updateConnectionState({
        state: "LOADING",
        iframe,
        dispatch: updateConnectionState,
        notebookDetails,
      });
    },
    [notebookId, notebookUrl, onNotebookConnected],
  );

  const fullNotebookUrl = generateNotebooklUrl(
    notebookUrl,
    notebookId,
    initialCode,
    environment,
    aiPrompt,
    enablePostMessageStore,
    enableDebug,
  );

  return (
    <iframe
      ref={refCallback}
      className={className}
      src={fullNotebookUrl}
    ></iframe>
  );
}

export { ControllableNotebook, type ControllableNotebookProps };
