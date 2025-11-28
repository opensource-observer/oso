"use client";

import React from "react";
import CodeMirror from "@uiw/react-codemirror";
import {
  CodeEditorProps,
  useCodeMirrorExtensions,
} from "@/components/widgets/code-editor/utils";

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
  const extensions = useCodeMirrorExtensions({
    language,
    schema,
    editorOptions,
  });

  return (
    <CodeMirror
      className={className}
      value={defaultValue}
      theme="light"
      extensions={extensions}
      height={`${height}px`}
      onChange={onChange ? onChange : undefined}
      editable={editable}
    />
  );
}

export default CodeEditor;
