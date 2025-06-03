"use client";

import Editor from "@monaco-editor/react";

interface MonacoEditorProps {
  className?: string;
  value?: string;
  onChange?: (value: string) => void;
  height?: string;
  language?: string;
  theme?: string;
  options?: any;
}

function MonacoEditor({
  className,
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

export { MonacoEditor };
