"use client";

import React, { useMemo } from "react";
import { EditorView, EditorState } from "@uiw/react-codemirror";
import CodeMirrorMerge from "react-codemirror-merge";
import {
  CodeDiffProps,
  useCodeMirrorExtensions,
} from "@/components/widgets/code-editor/utils";

const Original = CodeMirrorMerge.Original;
const Modified = CodeMirrorMerge.Modified;

export function CodeDiff({
  className,
  oldCode = "",
  newCode = "",
  language = "sql",
  editorOptions,
}: CodeDiffProps) {
  const additionalExtensions = useMemo(
    () => [EditorView.editable.of(false), EditorState.readOnly.of(true)],
    [],
  );

  const extensions = useCodeMirrorExtensions(
    {
      language,
      editorOptions,
    },
    additionalExtensions,
  );

  return (
    <CodeMirrorMerge
      className={className}
      theme="light"
      orientation="b-a"
      gutter={false}
    >
      <Original value={oldCode} extensions={extensions} />
      <Modified value={newCode} extensions={extensions} />
    </CodeMirrorMerge>
  );
}

export default CodeDiff;
