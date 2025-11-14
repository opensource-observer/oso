import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import React from "react";

export interface TimedSideEffectProps {
  onTick?: () => Promise<void>;
  onUnmount?: () => Promise<void>;
  intervalMs?: number;
  deps?: unknown[];
}

export function TimedSideEffect({
  deps,
  onTick,
  onUnmount,
  intervalMs = 30000,
}: TimedSideEffectProps) {
  React.useEffect(() => {
    const timer = setTimeout(() => void onTick?.(), intervalMs);
    return () => {
      clearTimeout(timer);
      void onUnmount?.();
    };
  }, [...(deps ?? []), intervalMs]);
  return null;
}

export const TimedSideEffectMeta: CodeComponentMeta<TimedSideEffectProps> = {
  name: "timed-side-effect",
  displayName: "Timed Side Effect",
  description: "Run actions on a timer.",
  props: {
    intervalMs: {
      type: "number",
      displayName: "Interval (ms)",
      description: "Interval in milliseconds between each tick.",
      defaultValueHint: 30000,
    },
    onTick: {
      type: "eventHandler",
      displayName: "On tick",
      description: "Actions to run on each tick of the timer.",
      argTypes: [],
    },
    onUnmount: {
      type: "eventHandler",
      displayName: "On unload",
      description:
        "Actions to run when this Side Effect component is unmounted.",
      argTypes: [],
    },
    deps: {
      type: "array",
      displayName: "When data changes",
      description:
        "List of values which should trigger a re-run of the actions if changed.",
    },
  },
};
