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
  const [value, setValue] = React.useState<string>(defaultValue || "");

  const extensions = useCodeMirrorExtensions({
    language,
    schema,
    editorOptions,
  });

  return (
    <CodeMirror
      className={className}
      value={value}
      theme="light"
      extensions={extensions}
      height={`${height}px`}
      onChange={(value) => {
        setValue(value);
        onChange?.(value);
      }}
      editable={editable}
    />
  );
}

export default CodeEditor;
