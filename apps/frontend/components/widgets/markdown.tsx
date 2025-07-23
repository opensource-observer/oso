"use client";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownProps = {
  className?: string;
  content?: string; // Show this per item
};

const MarkdownMeta: CodeComponentMeta<MarkdownProps> = {
  name: "Markdown",
  description: "Render Markdown",
  props: {
    content: {
      type: "string",
      defaultValue: "Hello World",
      helpText: "Markdown string",
    },
  },
};

function Markdown(props: MarkdownProps) {
  const { className, content } = props;
  return (
    <div className={className}>
      <div className={"prose"}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>
    </div>
  );
}

export { Markdown, MarkdownMeta };
