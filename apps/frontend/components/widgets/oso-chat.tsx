"use client";

import { useChat } from "@ai-sdk/react";
import { ReactElement, useEffect, useRef, useState } from "react";
import { useSupabaseState } from "../hooks/supabase";
import ReactMarkdown from "react-markdown";

const CHAT_PATH = "/api/v1/chat";

interface OSOChatProps {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this
}

export function OSOChat(props: OSOChatProps) {
  const { className, children } = props;
  const supabaseState = useSupabaseState();
  const session = supabaseState?.session;
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    status,
    setMessages,
  } = useChat({
    api: CHAT_PATH,
    headers: session
      ? {
          Authorization: `Bearer ${session.access_token}`,
        }
      : undefined,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isOpen, setIsOpen] = useState(false);

  const exampleQueries = [
    "Show me the top 5 projects by star count",
    "What tables are available in the OSO data lake?",
    "What metrics are tracked for repositories?",
    "How many artifacts are associated with the most popular projects?",
  ];

  const deleteConversation = () => {
    setMessages([]);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        120,
        textareaRef.current.scrollHeight,
      )}px`;
    }
  }, [input]);

  const renderContent = (content: string) => {
    return (
      <div className="prose prose-sm max-w-none overflow-hidden">
        <div className="overflow-x-auto">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    );
  };

  const TypingAnimation = () => (
    <div className="flex space-x-1 items-center p-2">
      <div
        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
        style={{ animationDelay: "0ms" }}
      ></div>
      <div
        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
        style={{ animationDelay: "150ms" }}
      ></div>
      <div
        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
        style={{ animationDelay: "300ms" }}
      ></div>
    </div>
  );

  if (!children) {
    return <p>Missing children</p>;
  }

  return (
    <>
      <div className={className} onClick={() => setIsOpen(true)}>
        {children}
      </div>

      <div
        className={`fixed inset-0 bg-black bg-opacity-30 z-50 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setIsOpen(false)}
      >
        <div
          className={`absolute top-0 right-0 h-full bg-white transform transition-transform duration-300 ease-in-out shadow-lg ${
            isOpen ? "translate-x-0" : "translate-x-full"
          }`}
          style={{ width: "450px" }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-lg font-medium text-blue-600">
              OSO SQL Assistant
            </h3>
            <div className="flex space-x-2">
              {messages.length > 0 && (
                <button
                  onClick={deleteConversation}
                  className="p-1 rounded-full text-gray-500 hover:bg-gray-100"
                  title="Delete conversation"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-full text-gray-500 hover:bg-gray-100"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          <div className="h-[calc(100%-120px)] overflow-y-auto p-5 space-y-5 bg-white">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full">
                <div className="max-w-md text-center space-y-4">
                  <h4 className="font-medium text-lg text-blue-600">
                    SQL Assistant
                  </h4>
                  <p className="text-gray-600">
                    Ask questions about OSO data in natural language.
                  </p>

                  <div className="space-y-2 mt-6 text-left">
                    {exampleQueries.map((query, index) => (
                      <div
                        key={index}
                        className="p-3 rounded-lg bg-blue-50 text-blue-800 text-sm cursor-pointer hover:bg-blue-100 transition-colors"
                        onClick={() =>
                          handleInputChange({
                            target: {
                              value: query,
                            },
                          } as any)
                        }
                      >
                        {query}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`p-4 rounded-lg ${
                    message.role === "user"
                      ? "bg-blue-50 text-blue-800 max-w-[85%]"
                      : "bg-white border border-gray-100 text-gray-800 max-w-[85%]"
                  }`}
                >
                  {message.role === "user" ? (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  ) : (
                    renderContent(message.content)
                  )}
                </div>
              </div>
            ))}

            {status === "streaming" && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-100 text-gray-800 rounded-lg max-w-[85%]">
                  <TypingAnimation />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100 bg-white">
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                placeholder="Ask about OSO data..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none min-h-[44px] max-h-[120px] overflow-y-auto"
                disabled={status === "streaming" || status === "submitted"}
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (input.trim()) {
                      handleSubmit(e);
                    }
                  }
                }}
              />
              <button
                type="submit"
                disabled={
                  status === "streaming" ||
                  status === "submitted" ||
                  !input.trim()
                }
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 flex items-center justify-center w-12 h-12 transition-all duration-200 transform hover:scale-105 shadow-md"
              >
                {status === "streaming" || status === "submitted" ? (
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 5l7 7-7 7M5 5l7 7-7 7"
                    />
                  </svg>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
