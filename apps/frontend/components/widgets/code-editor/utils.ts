import { useMemo } from "react";
import { python } from "@codemirror/lang-python";
import { sql, SQLNamespace } from "@codemirror/lang-sql";
import { json } from "@codemirror/lang-json";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import {
  basicSetup,
  BasicSetupOptions,
  EditorView,
  Extension,
} from "@uiw/react-codemirror";

export const DEFAULT_THEME = EditorView.theme({
  "&": {
    fontFamily: "Menlo, Monaco, 'Courier New', monospace",
    fontSize: "14px",
  },
});

const ALL_LANGUAGES = ["python", "sql", "json"] as const;
export type CodeLanguage = (typeof ALL_LANGUAGES)[number];

export function createLanguageExtension(
  language: CodeLanguage,
  schema?: SQLNamespace,
): Extension {
  switch (language) {
    case "python":
      return python();
    case "sql":
      return sql({
        upperCaseKeywords: true,
        schema: schema,
      });
    case "json":
      return json();
    default:
      throw new Error(`Unsupported language: ${language}`);
  }
}

export function useCodeMirrorExtensions(
  {
    language,
    schema,
    editorOptions,
  }: {
    language: CodeLanguage;
    schema?: SQLNamespace;
    editorOptions?: BasicSetupOptions;
  },
  additionalExtensions: Extension[] = [],
) {
  return useMemo(
    () => [
      createLanguageExtension(language, schema),
      basicSetup({
        tabSize: 2,
        autocompletion: true,
        bracketMatching: true,
        foldGutter: false,
        indentOnInput: true,
        lineNumbers: true,
        ...editorOptions,
      }),
      DEFAULT_THEME,
      ...additionalExtensions,
    ],
    [language, schema, editorOptions, additionalExtensions],
  );
}

interface CodeSharedProps {
  className?: string;
  editorOptions?: BasicSetupOptions;
  language?: CodeLanguage;
}

export interface CodeEditorProps extends CodeSharedProps {
  defaultValue?: string;
  onChange?: (value: string) => void;
  schema?: SQLNamespace;
  height?: number;
  editable?: boolean;
}

export interface CodeDiffProps extends CodeSharedProps {
  oldCode?: string;
  newCode?: string;
}

const SharedMeta: CodeComponentMeta<CodeSharedProps>["props"] = {
  language: {
    type: "choice",
    options: [...ALL_LANGUAGES],
    defaultValueHint: "sql",
  },
  editorOptions: {
    type: "object",
    advanced: true,
  },
};

export const CodeEditorMeta: CodeComponentMeta<CodeEditorProps> = {
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
    ...SharedMeta,
    height: {
      type: "number",
      defaultValueHint: 200,
    },
    editable: {
      type: "boolean",
      defaultValueHint: true,
    },
    schema: {
      type: "object",
      helpText: "SQL schema for autocompletion",
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

export const CodeDiffMeta: CodeComponentMeta<CodeDiffProps> = {
  name: "CodeDiff",
  description: "CodeMirror code diff view",
  props: {
    oldCode: {
      type: "string",
      displayName: "Old Code",
    },
    newCode: {
      type: "string",
      displayName: "New Code",
    },
    ...SharedMeta,
  },
};
