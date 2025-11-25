import type { SQLNamespace } from "@codemirror/lang-sql";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import type { BasicSetupOptions } from "@uiw/react-codemirror";

interface CodeEditorProps {
  className?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  language?: "python" | "sql";
  schema: SQLNamespace;
  height?: number;
  editable?: boolean;
  editorOptions?: BasicSetupOptions;
}

const CodeEditorMeta: CodeComponentMeta<CodeEditorProps> = {
  name: "CodeEditor",
  description: "CodeMirror code editor",
  props: {
    defaultValue: {
      type: "string",
    },
    onChange: {
      type: "eventHandler",
      argTypes: [
        {
          name: "value",
          type: "string",
        },
      ],
    },
    language: {
      type: "choice",
      options: ["python", "sql"],
      defaultValueHint: "sql",
    },
    schema: {
      type: "object",
      helpText: "SQL schema for autocompletion",
      advanced: true,
    },
    height: {
      type: "number",
      defaultValueHint: 200,
    },
    editable: {
      type: "boolean",
      defaultValueHint: true,
    },
    editorOptions: {
      type: "object",
      advanced: true,
    },
  },
  states: {
    value: {
      type: "readonly",
      variableType: "text",
      onChangeProp: "onChange",
      initFunc: (props) => props.defaultValue || "",
    },
  },
};

export { CodeEditorMeta, type CodeEditorProps };
