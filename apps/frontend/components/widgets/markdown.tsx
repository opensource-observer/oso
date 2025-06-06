"use client";

import ReactMarkdown from "react-markdown";

type MarkdownProps = {
  className?: string;
  content?: string; // Show this per item
};

function Markdown(props: MarkdownProps) {
  const { className, content } = props;
  return (
    <div className={className}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}

export { Markdown };
