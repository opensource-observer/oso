import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import * as React from "react";

import { cn } from "@/lib/utils";

type TextareaProps = React.ComponentProps<"textarea">;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Textarea.displayName = "Textarea";

const TextareaMeta: CodeComponentMeta<TextareaProps> = {
  name: "Textarea",
  description: "shadcn/ui Textarea component",
  props: {
    value: "string",
    placeholder: "string",
    onChange: {
      type: "eventHandler",
      argTypes: [{ name: "event", type: "string" }],
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

export { Textarea, TextareaMeta };
