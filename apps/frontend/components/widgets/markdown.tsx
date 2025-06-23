"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownProps = {
  className?: string;
  content?: string; // Show this per item
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

export { Markdown };
