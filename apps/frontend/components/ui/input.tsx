import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import * as React from "react";

import { cn } from "@/lib/utils";

type InputProps = React.ComponentProps<"input"> & {
  onPressEnter?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
};
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className,
        )}
        ref={ref}
        onKeyUp={(e) => {
          if (e.key === "Enter" && props.onPressEnter) {
            props.onPressEnter(e);
          }
        }}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

const InputMeta: CodeComponentMeta<InputProps> = {
  name: "Input",
  description: "shadcn/ui Input component",
  props: {
    type: {
      type: "choice",
      options: ["text", "email", "date", "password", "number", "file", "url"],
      defaultValue: "text",
    },
    value: "string",
    placeholder: "string",
    onChange: {
      type: "eventHandler",
      argTypes: [{ name: "event", type: "string" }],
    },
    onPressEnter: {
      type: "eventHandler",
      argTypes: [{ name: "event", type: "object" }],
    },
    disabled: "boolean",
  },
  states: {
    value: {
      type: "writable",
      valueProp: "value",
      variableType: "text",
      onChangeProp: "onChange",
    },
  },
};

export { Input, InputMeta };
