import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { LogViewer } from "@/components/widgets/log-viewer";
import type { LogEntry } from "@/components/widgets/log-viewer";

const meta = {
  title: "widgets/LogViewer",
  component: LogViewer,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  argTypes: {
    maxHeight: {
      control: { type: "number", min: 200, max: 1000, step: 50 },
    },
    showTimestamp: {
      control: "boolean",
    },
    showControls: {
      control: "boolean",
    },
  },
} satisfies Meta<typeof LogViewer>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleLogs: LogEntry[] = [
  {
    event: "Reporting run 332dd146-19cd-4701-8de2-c01ea18a91f9 as started.",
    log_level: "info",
    timestamp: "2026-01-22T17:21:56.517357+00:00",
  },
  {
    extra: { dataset_id: "1c5c61da-5a4c-46ac-9d39-f491cd05e70c" },
    event: "Received DataIngestionRunRequest",
    log_level: "info",
    timestamp: "2026-01-22T17:21:56.548588+00:00",
  },
  {
    extra: {
      dataset_id: "1c5c61da-5a4c-46ac-9d39-f491cd05e70c",
      config_id: "9d8a6899-acbb-40db-b04a-d62cbd255b3c",
      factory_type: "REST",
    },
    event: "Config validated",
    log_level: "info",
    timestamp: "2026-01-22T17:21:56.561803+00:00",
  },
  {
    extra: {
      dataset_id: "1c5c61da-5a4c-46ac-9d39-f491cd05e70c",
      config_id: "9d8a6899-acbb-40db-b04a-d62cbd255b3c",
      num_endpoints: 1,
    },
    event: "Creating REST API resources",
    log_level: "info",
    timestamp: "2026-01-22T17:21:56.576330+00:00",
  },
  {
    extra: {
      pipeline_name: "816bf05469fa465294a2346a2c987db0_1c5c61da5a4c46ac9",
      dataset_schema:
        "org_816bf05469fa465294a2346a2c987db0__1c5c61da5a4c46ac9d39f491cd05e70c",
    },
    event: "Running dlt pipeline",
    log_level: "info",
    timestamp: "2026-01-22T17:21:56.795539+00:00",
  },
  {
    extra: {
      pipeline_name: "816bf05469fa465294a2346a2c987db0_1c5c61da5a4c46ac9",
      loaded_packages: 1,
    },
    event: "Data ingestion completed successfully",
    log_level: "info",
    timestamp: "2026-01-22T17:21:57.106409+00:00",
  },
  {
    extra: {
      num_tables: 1,
      dataset_id: "1c5c61da-5a4c-46ac-9d39-f491cd05e70c",
    },
    event: "Creating materializations for ingested tables",
    log_level: "info",
    timestamp: "2026-01-22T17:21:57.107004+00:00",
  },
  {
    event: "Creating materialization",
    log_level: "info",
    timestamp: "2026-01-22T17:21:57.107031+00:00",
  },
  {
    extra: {
      table_name: "ethereum",
      warehouse_fqn:
        "user_shared.org_816bf05469fa465294a2346a2c987db0__1c5c61da5a4c46ac9d39f491cd05e70c.ethereum",
    },
    event: "Created materialization",
    log_level: "info",
    timestamp: "2026-01-22T17:21:57.130212+00:00",
  },
];

const mixedLevelLogs: LogEntry[] = [
  {
    event: "Application started",
    log_level: "info",
    timestamp: "2026-01-22T10:00:00.000000+00:00",
  },
  {
    event: "Connected to database",
    log_level: "info",
    timestamp: "2026-01-22T10:00:01.234567+00:00",
    extra: {
      host: "localhost",
      port: 5432,
      database: "myapp",
    },
  },
  {
    event: "Cache miss for key: user_session_123",
    log_level: "warning",
    timestamp: "2026-01-22T10:00:05.123456+00:00",
    extra: {
      cache_key: "user_session_123",
      ttl: 3600,
    },
  },
  {
    event: "Slow query detected",
    log_level: "warning",
    timestamp: "2026-01-22T10:00:10.987654+00:00",
    extra: {
      query: "SELECT * FROM large_table WHERE status = 'active'",
      duration_ms: 2500,
      threshold_ms: 1000,
    },
  },
  {
    event: "Failed to connect to external API",
    log_level: "error",
    timestamp: "2026-01-22T10:00:15.111111+00:00",
    extra: {
      api_url: "https://api.example.com/v1/data",
      status_code: 503,
      error_message: "Service Unavailable",
      retry_count: 3,
    },
  },
  {
    event: "Debugging user authentication flow",
    log_level: "debug",
    timestamp: "2026-01-22T10:00:20.222222+00:00",
    extra: {
      user_id: "usr_abc123",
      auth_method: "oauth2",
      scopes: ["read", "write"],
    },
  },
  {
    event: "Database connection pool exhausted",
    log_level: "error",
    timestamp: "2026-01-22T10:00:25.333333+00:00",
    extra: {
      max_connections: 20,
      active_connections: 20,
      waiting_requests: 5,
    },
  },
  {
    event: "Request processed successfully",
    log_level: "info",
    timestamp: "2026-01-22T10:00:30.444444+00:00",
    extra: {
      endpoint: "/api/users",
      method: "GET",
      status_code: 200,
      duration_ms: 45,
    },
  },
];

export const Default: Story = {
  args: {
    testData: true,
    testLogs: sampleLogs,
    title: "Console Output",
    maxHeight: 600,
    showTimestamp: true,
    showControls: true,
  },
};

export const MixedLogLevels: Story = {
  args: {
    testData: true,
    testLogs: mixedLevelLogs,
    title: "Application Logs",
    maxHeight: 600,
    showTimestamp: true,
    showControls: true,
  },
};

export const LargeDataset: Story = {
  args: {
    testData: true,
    testLogs: Array.from({ length: 100 }, (_, i) => ({
      event: `Log entry ${i + 1}: Processing item batch`,
      log_level:
        i % 10 === 0
          ? "error"
          : i % 5 === 0
            ? "warning"
            : i % 3 === 0
              ? "debug"
              : "info",
      timestamp: new Date(
        Date.now() - (100 - i) * 1000,
      ).toISOString() as `${string}+00:00`,
      extra:
        i % 4 === 0
          ? {
              batch_id: `batch_${i}`,
              items_processed: Math.floor(Math.random() * 100),
              duration_ms: Math.floor(Math.random() * 500),
            }
          : undefined,
    })) as LogEntry[],
    title: "Large Log Dataset (100 entries)",
    maxHeight: 600,
    showTimestamp: true,
    showControls: true,
  },
};
