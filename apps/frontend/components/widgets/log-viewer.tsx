"use client";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import React, { useState, memo, useMemo, useRef } from "react";
import { cn } from "@/lib/utils";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Info,
  XCircle,
  AlertTriangle,
  Bug,
  ChevronRight,
  Copy,
  Check,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { logger } from "@/lib/logger";
import { z } from "zod";
import { useAsync } from "react-use";

const LogEntrySchema = z.object({
  event: z.string(),
  log_level: z.preprocess(
    (val) => (typeof val === "string" ? val.toLowerCase() : val),
    z.enum(["info", "error", "warning", "debug", "critical"]),
  ),
  timestamp: z.string(),
  extra: z.record(z.unknown()).optional(),
});

export interface LogEntry {
  event: string;
  log_level: "info" | "error" | "warning" | "debug" | "critical";
  timestamp: string;
  extra?: Record<string, unknown>;
}

interface LogViewerProps {
  className?: string;
  logsUrl?: string;
  testData?: LogEntry[];
  title?: string;
  maxHeight?: number;
  showTimestamp?: boolean;
  showControls?: boolean;
}

const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }).format(date);
  } catch {
    return timestamp;
  }
};

const getLogLevelStyles = (level: LogEntry["log_level"]) => {
  const styles = {
    info: {
      bg: "bg-blue-50",
      text: "text-blue-700",
      border: "border-blue-200",
      icon: Info,
    },
    error: {
      bg: "bg-red-50",
      text: "text-red-700",
      border: "border-red-200",
      icon: XCircle,
    },
    warning: {
      bg: "bg-amber-50",
      text: "text-amber-700",
      border: "border-amber-200",
      icon: AlertTriangle,
    },
    debug: {
      bg: "bg-gray-50",
      text: "text-gray-600",
      border: "border-gray-200",
      icon: Bug,
    },
    critical: {
      bg: "bg-orange-50",
      text: "text-orange-500",
      border: "border-orange-200",
      icon: XCircle,
    },
  };
  return styles[level];
};

interface JsonViewerProps {
  data: Record<string, unknown>;
}

const JsonViewer = memo(({ data }: JsonViewerProps) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      logger.error("Failed to copy:", err);
    }
  };

  const renderValue = (value: unknown): React.ReactNode => {
    if (value === null) {
      return <span className="text-gray-400 font-mono text-xs">null</span>;
    }
    if (value === undefined) {
      return <span className="text-gray-400 font-mono text-xs">undefined</span>;
    }
    if (typeof value === "string") {
      return (
        <span className="text-green-600 font-mono text-xs">
          &ldquo;{value}&rdquo;
        </span>
      );
    }
    if (typeof value === "number") {
      return <span className="text-purple-600 font-mono text-xs">{value}</span>;
    }
    if (typeof value === "boolean") {
      return (
        <span className="text-amber-600 font-mono text-xs">
          {value.toString()}
        </span>
      );
    }
    if (typeof value === "object" && !Array.isArray(value)) {
      return (
        <div className="ml-4 mt-1">
          {Object.entries(value as Record<string, unknown>).map(
            ([k, v], idx) => (
              <div key={`${k}-${idx}`} className="flex gap-2">
                <span className="text-blue-600 font-mono text-xs">{k}:</span>
                {renderValue(v)}
              </div>
            ),
          )}
        </div>
      );
    }
    if (Array.isArray(value)) {
      return (
        <div className="ml-4 mt-1">
          {value.map((item, idx) => (
            <div key={idx} className="flex gap-2">
              <span className="text-gray-400 font-mono text-xs">[{idx}]:</span>
              {renderValue(item)}
            </div>
          ))}
        </div>
      );
    }
    return <span className="font-mono text-xs">{String(value)}</span>;
  };

  return (
    <div className="relative border-l-2 border-gray-200 pl-3 py-2 mt-2 bg-gray-50/50 ml-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => {
          void copyToClipboard();
        }}
        className="absolute top-1 right-1 h-6 w-6"
        title="Copy to clipboard"
      >
        {copied ? (
          <Check className="w-3 h-3 text-green-600" />
        ) : (
          <Copy className="w-3 h-3 text-gray-400" />
        )}
      </Button>
      {Object.entries(data).map(([key, value], idx) => (
        <div key={`${key}-${idx}`} className="flex gap-2 mb-1">
          <span className="text-blue-600 font-mono text-xs font-semibold">
            {key}:
          </span>
          {renderValue(value)}
        </div>
      ))}
    </div>
  );
});
JsonViewer.displayName = "JsonViewer";

interface LogEntryComponentProps {
  log: LogEntry;
  showTimestamp: boolean;
}

const LogEntryComponent = memo(
  ({ log, showTimestamp }: LogEntryComponentProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const styles = getLogLevelStyles(log.log_level);
    const Icon = styles.icon;
    const hasExtra = log.extra && Object.keys(log.extra).length > 0;

    return (
      <>
        <TableRow className="hover:bg-muted/50">
          {showTimestamp && (
            <TableCell className="font-mono text-xs text-muted-foreground py-3 align-top">
              {formatTimestamp(log.timestamp)}
            </TableCell>
          )}
          <TableCell className="py-3 align-top">
            <Badge
              className={cn(
                "gap-1 w-fit font-normal",
                styles.bg,
                styles.text,
                "border-0",
              )}
            >
              <Icon className="w-3 h-3" />
              <span className="text-xs">{log.log_level}</span>
            </Badge>
          </TableCell>
          <TableCell className="font-mono text-sm py-3 align-top">
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
              <div className="flex items-start gap-1">
                {hasExtra ? (
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5 p-0 shrink-0 -ml-1"
                    >
                      <ChevronRight
                        className={cn(
                          "w-3.5 h-3.5 transition-transform duration-200",
                          isOpen && "rotate-90",
                        )}
                      />
                    </Button>
                  </CollapsibleTrigger>
                ) : (
                  <div className="w-4 shrink-0" />
                )}
                <span className="break-words">{log.event}</span>
              </div>
              {hasExtra && log.extra && (
                <CollapsibleContent>
                  <JsonViewer
                    key={`${log.timestamp}-${log.event}-extra`}
                    data={log.extra}
                  />
                </CollapsibleContent>
              )}
            </Collapsible>
          </TableCell>
        </TableRow>
      </>
    );
  },
);
LogEntryComponent.displayName = "LogEntryComponent";

export function LogViewer({
  className,
  logsUrl,
  testData,
  title = "Console Output",
  maxHeight = 600,
  showTimestamp = true,
  showControls = true,
}: LogViewerProps) {
  const [levelFilter, setLevelFilter] = useState<string[]>([]);
  const memoizedTestData = useMemo(() => testData, [testData]);
  const previousLogsRef = useRef<LogEntry[]>([]);
  const previousContentRef = useRef<string | null>(null);

  const {
    loading,
    error,
    value: logs,
  } = useAsync(async () => {
    if (memoizedTestData) {
      return memoizedTestData;
    }

    if (!logsUrl) {
      return [];
    }

    const response = await fetch(logsUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch logs: ${response.statusText}`);
    }

    const text = await response.text();

    if (text === previousContentRef.current) {
      return previousLogsRef.current;
    }

    previousContentRef.current = text;

    const lines = text
      .trim()
      .split("\n")
      .filter((line) => line.trim());

    const parsedLogs = lines.map((line, index) => {
      const parsed = JSON.parse(line);
      const result = LogEntrySchema.safeParse(parsed);

      if (!result.success) {
        const errors = result.error.errors
          .map((e) => `${e.path.join(".")}: ${e.message}`)
          .join(", ");
        throw new Error(`Invalid log format at line ${index + 1}: ${errors}`);
      }

      return result.data;
    });

    previousLogsRef.current = parsedLogs;
    return parsedLogs;
  }, [logsUrl, memoizedTestData]);

  const safeLogs = logs ?? [];

  const filteredLogs =
    levelFilter.length === 0
      ? safeLogs
      : safeLogs.filter((log) => levelFilter.includes(log.log_level));

  const logCounts = safeLogs.reduce<Record<string, number>>((acc, log) => {
    acc[log.log_level] = (acc[log.log_level] || 0) + 1;
    return acc;
  }, {});

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="font-semibold text-lg">{title}</h3>
          {showControls && (
            <div className="flex items-center gap-2 flex-wrap">
              <ToggleGroup
                type="multiple"
                value={levelFilter}
                onValueChange={setLevelFilter}
                className="justify-start"
              >
                {(
                  ["info", "warning", "error", "debug"] as Array<
                    LogEntry["log_level"]
                  >
                ).map((level) => {
                  const styles = getLogLevelStyles(level);
                  const count = logCounts[level] || 0;
                  const LevelIcon = styles.icon;
                  return (
                    <ToggleGroupItem
                      key={level}
                      value={level}
                      aria-label={`Filter ${level} logs`}
                      className={cn(
                        "gap-1 text-xs h-8",
                        levelFilter.includes(level) && styles.bg,
                        levelFilter.includes(level) && styles.text,
                      )}
                      disabled={count === 0}
                    >
                      <LevelIcon className="w-3 h-3" />
                      {level}: {count}
                    </ToggleGroupItem>
                  );
                })}
              </ToggleGroup>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div
          className="overflow-y-auto bg-muted/30"
          style={{ maxHeight: `${maxHeight}px` }}
        >
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading logs...
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12 text-red-600 text-sm">
              {error.message}
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
              {levelFilter.length > 0
                ? "No logs matching the selected filters"
                : "No logs to display"}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  {showTimestamp && (
                    <TableHead className="w-[100px] font-mono text-xs">
                      Time
                    </TableHead>
                  )}
                  <TableHead className="w-[110px] text-xs">Level</TableHead>
                  <TableHead className="text-xs">Message</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.map((log, index) => (
                  <LogEntryComponent
                    key={`${log.timestamp}-${log.event}-${index}`}
                    log={log}
                    showTimestamp={showTimestamp}
                  />
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export const LogViewerMeta: CodeComponentMeta<LogViewerProps> = {
  name: "LogViewer",
  description:
    "GitHub Actions-inspired console log viewer with expandable JSON metadata",
  props: {
    logsUrl: {
      type: "string",
      description: "URL to fetch JSONL logs from (e.g., GCS bucket URL)",
    },
    testData: {
      type: "array",
      editOnly: true,
      defaultValue: [
        {
          event: "Application started",
          log_level: "info",
          timestamp: "2026-01-26T20:16:11.053Z",
        },
      ],
      description: "Test logs for Plasmic editor preview",
    },
    title: {
      type: "string",
      defaultValue: "Console Output",
    },
    maxHeight: {
      type: "number",
      defaultValue: 600,
    },
    showTimestamp: {
      type: "boolean",
      defaultValue: true,
    },
    showControls: {
      type: "boolean",
      defaultValue: true,
    },
  },
};
