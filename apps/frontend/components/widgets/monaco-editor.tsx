"use client";

import Editor from "@monaco-editor/react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

interface MonacoEditorProps {
  className?: string;
  defaultValue?: string;
  value?: string;
  onChange?: (value: string) => void;
  height?: string;
  language?: string;
  theme?: string;
  options?: any;
}

const MonacoEditorMeta: CodeComponentMeta<MonacoEditorProps> = {
  name: "MonacoEditor",
  description: "Monaco editor",
  props: {
    defaultValue: {
      type: "string",
    },
    value: {
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
    height: {
      type: "string",
      defaultValue: "200px",
    },
    language: {
      type: "string",
      defaultValue: "sql",
    },
    theme: {
      type: "string",
      defaultValue: "vs-light",
    },
    options: {
      type: "object",
      defaultValue: {},
    },
  },
  states: {
    value: {
      type: "writable",
      variableType: "text",
      valueProp: "value",
      onChangeProp: "onChange",
    },
  },
};

function MonacoEditor({
  className,
  defaultValue,
  value,
  onChange,
  height,
  language,
  theme,
  options,
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
      className={className}
      height={height}
      language={language}
      defaultValue={defaultValue}
      value={value}
      theme={theme}
      options={defaultOptions}
      onChange={(value) => (onChange ? onChange(value || "") : undefined)}
      loading={
        <div className="flex items-center justify-center h-full">
          Loading editor...
        </div>
      }
    />
  );
}

export { MonacoEditor, MonacoEditorMeta };
