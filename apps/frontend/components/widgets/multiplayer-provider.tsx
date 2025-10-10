"use client";

import { useEffect, useState, type ReactNode } from "react";
import { type RealtimeChannel } from "@supabase/supabase-js";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { CodeComponentMeta, DataProvider } from "@plasmicapp/loader-nextjs";

// Define the shape of a user in the multiplayer context
type MultiplayerUser = {
  full_name: string | null;
  avatar_url: string | null;
  email: string | null;
};

interface MultiplayerUserProviderProps {
  children: ReactNode;
  room: string | null;
  testData?: MultiplayerUser[];
}

export const MultiplayerUserProviderMeta: CodeComponentMeta<MultiplayerUserProviderProps> =
  {
    name: "MultiplayerUserProvider",
    description: "Provides multiplayer user context to its children",
    props: {
      children: "slot",
      room: {
        type: "string",
        description: "The room identifier for the multiplayer session",
      },
      testData: {
        type: "object",
        editOnly: true,
      },
    },
    providesData: true,
  };

function MultiplayerUserProvider({
  children,
  room,
  testData,
}: MultiplayerUserProviderProps) {
  const { client: osoApp } = useOsoAppClient();
  const [users, setUsers] = useState<MultiplayerUser[]>([]);

  useEffect(() => {
    if (!osoApp || !room) {
      return;
    }
    let channel: RealtimeChannel;

    const setupChannel = async () => {
      // We need user profile to be part of the presence state
      const profile = await osoApp.getMyUserProfile();
      channel = await osoApp.getRealtimeChannel(room);

      channel.on("presence", { event: "sync" }, () => {
        const newState = channel.presenceState<MultiplayerUser>();
        const userList = Object.values(newState).flatMap(
          (presence) => presence,
        );
        setUsers(userList);
      });

      channel.subscribe((status) => {
        if (status !== "SUBSCRIBED") {
          return;
        }

        void channel.track({
          full_name: profile.full_name,
          avatar_url: profile.avatar_url,
          email: profile.email,
        });
      });
    };

    void setupChannel();

    return () => {
      if (channel) {
        void channel.unsubscribe();
      }
    };
  }, [room, osoApp]);

  return (
    <DataProvider name="users" data={testData ? testData : users}>
      {children}
    </DataProvider>
  );
}

export { MultiplayerUserProvider };
