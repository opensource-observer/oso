"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { OSOChat } from "../../components/widgets/oso-chat";
import { format } from "sql-formatter";
import { logger } from "../../lib/logger";

const MonacoSQLEditor = dynamic(
  () => import("../../components/widgets/monaco-editor"),
  { ssr: false },
);

export default function SQLStudioPage() {
  const [sqlQuery, setSqlQuery] = useState("");
  const [results, setResults] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sqlQuery.trim()) return;

    setLoading(true);
    setError(null);
    setResults([]);
    setColumns([]);

    try {
      const response = await fetch("/api/v1/sql", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: sqlQuery }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to execute query");
      }

      if (!response.body) {
        throw new Error("Response body is not a readable stream");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";
      let accumulatedData: any[] = [];

      for (;;) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        try {
          const parsedData = JSON.parse(buffer);

          if (Array.isArray(parsedData)) {
            accumulatedData = parsedData;
          } else {
            accumulatedData = [parsedData];
          }

          if (accumulatedData.length > 0) {
            setColumns(Object.keys(accumulatedData[0]));
          }

          setResults([...accumulatedData]);

          buffer = "";
        } catch (e) {
          logger.error("Error parsing data:", e);
        }
      }

      buffer += decoder.decode();

      if (buffer.trim()) {
        try {
          const finalData = JSON.parse(buffer);

          if (Array.isArray(finalData)) {
            accumulatedData = finalData;
          } else {
            accumulatedData.push(finalData);
          }

          if (accumulatedData.length > 0) {
            setColumns(Object.keys(accumulatedData[0]));
          }

          setResults(accumulatedData);
        } catch (e) {
          logger.error("Error parsing final data:", e);
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
    } finally {
      setLoading(false);
    }
  };

  const formatQuery = () => {
    setSqlQuery((query) =>
      format(query, {
        language: "trino",
      }),
    );
  };

  const exampleQueries = [
    {
      name: "Top Projects",
      query:
        "SELECT project_name, display_name, star_count FROM code_metrics_by_project_v1 ORDER BY star_count DESC LIMIT 10",
    },
    {
      name: "Project Contributors",
      query:
        "SELECT project_name, display_name, contributor_count FROM code_metrics_by_project_v1 ORDER BY contributor_count DESC LIMIT 10",
    },
    {
      name: "Recent Activity",
      query:
        "SELECT event_type, COUNT(*) as count FROM event_types_v1 GROUP BY event_type ORDER BY count DESC LIMIT 10",
    },
  ];

  const renderResults = () => {
    if (!results || results.length === 0) return null;

    const displayColumns =
      columns.length > 0 ? columns : Object.keys(results[0]);

    return (
      <div className="overflow-x-auto bg-white rounded-lg shadow-md">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {displayColumns.map((column) => (
                <th
                  key={column}
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={rowIndex % 2 === 0 ? "bg-white" : "bg-gray-50"}
              >
                {displayColumns.map((column) => (
                  <td
                    key={`${rowIndex}-${column}`}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                  >
                    {typeof row[column] === "object"
                      ? JSON.stringify(row[column])
                      : String(row[column] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">
            OSO SQL Studio v2
          </h1>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6">
          <form
            onSubmit={(e) => {
              void handleSubmit(e);
            }}
            className="space-y-4"
          >
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="px-4 py-2 bg-gray-100 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-sm font-medium text-gray-700">SQL Query</h2>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    className="text-xs text-gray-600 hover:text-gray-900 px-2 py-1"
                    onClick={formatQuery}
                  >
                    Format
                  </button>
                  <button
                    type="button"
                    className="text-xs text-gray-600 hover:text-gray-900 px-2 py-1"
                    onClick={() => setSqlQuery("")}
                  >
                    Clear
                  </button>
                </div>
              </div>

              <div className="h-64 border-b border-gray-200">
                <MonacoSQLEditor
                  value={sqlQuery}
                  onChange={setSqlQuery}
                  height="100%"
                  theme="vs-light"
                  options={{
                    fontSize: 14,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    wordWrap: "on",
                  }}
                />
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex gap-2 overflow-x-auto pb-2">
                {exampleQueries.map((ex, index) => (
                  <button
                    key={index}
                    type="button"
                    className="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-100 whitespace-nowrap"
                    onClick={() => setSqlQuery(ex.query)}
                  >
                    {ex.name}
                  </button>
                ))}
              </div>

              <button
                type="submit"
                disabled={loading || !sqlQuery.trim()}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                    Running...
                  </>
                ) : (
                  "Run Query"
                )}
              </button>
            </div>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {results && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">
              Results ({results.length} rows)
            </h3>
            {renderResults()}
          </div>
        )}
      </main>

      <OSOChat />
    </div>
  );
}
