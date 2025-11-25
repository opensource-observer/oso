"use client";

import React, { useMemo } from "react";
import CodeMirror, {
  basicSetup,
  EditorView,
  Extension,
} from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { sql, SQLNamespace } from "@codemirror/lang-sql";
import { CodeEditorProps } from "@/components/widgets/code-editor/types";

const DEFAULT_THEME = EditorView.theme({
  "&": {
    fontFamily: "Menlo, Monaco, 'Courier New', monospace",
    fontSize: "14px",
  },
});

function createLanguageExtension(
  language: string,
  schema: SQLNamespace,
): Extension {
  switch (language) {
    case "python":
      return python();
    case "sql":
      return sql({
        upperCaseKeywords: true,
        schema: schema,
      });
    default:
      throw new Error(`Unsupported language: ${language}`);
  }
}

function CodeEditor({
  className,
  defaultValue,
  onChange,
  language = "sql",
  schema,
  height = 200,
  editable = true,
  editorOptions,
}: CodeEditorProps) {
  const languageExtension = useMemo(
    () => createLanguageExtension(language, schema),
    [language, schema],
  );

  return (
    <CodeMirror
      className={className}
      value={defaultValue}
      theme="light"
      extensions={[
        languageExtension,
        basicSetup({
          tabSize: 2,
          autocompletion: true,
          bracketMatching: true,
          foldGutter: false,
          indentOnInput: true,
          ...editorOptions,
        }),
        DEFAULT_THEME,
      ]}
      height={`${height}px`}
      onChange={onChange ? onChange : undefined}
      editable={editable}
    />
  );
}

export default CodeEditor;
