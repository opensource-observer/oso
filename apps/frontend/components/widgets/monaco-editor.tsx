"use client";

import Editor from "@monaco-editor/react";

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: string;
  theme?: string;
  options?: any;
}

export default function MonacoSQLEditor({
  value,
  onChange,
  height = "200px",
  theme = "vs-light",
  options = {},
}: MonacoEditorProps) {
  const defaultOptions = {
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 14,
    tabSize: 2,
    wordWrap: "on",
    automaticLayout: true,
    fontFamily: "Menlo, Monaco, 'Courier New', monospace",
    formatOnPaste: true,
    ...options,
  };

  return (
    <Editor
      height={height}
      language="sql"
      value={value}
      theme={theme}
      options={defaultOptions}
      onChange={(value) => onChange(value || "")}
      loading={
        <div className="flex items-center justify-center h-full">
          Loading editor...
        </div>
      }
    />
  );
}
