import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { PreviewTab } from "@/components/widgets/preview-tab";
import { http, HttpResponse, delay } from "msw";

const meta = {
  title: "widgets/PreviewTab",
  component: PreviewTab,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  argTypes: {
    datasetId: { control: "text" },
    modelOrTable: { control: "text" },
  },
} satisfies Meta<typeof PreviewTab>;

export default meta;
type Story = StoryObj<typeof meta>;

// Mock data for typical use case - user activity data
const userActivityData = [
  {
    user_id: "usr_001",
    email: "alice@example.com",
    total_orders: 12,
    revenue: 1250.5,
    signup_date: "2024-01-15",
    is_active: true,
    last_login: "2026-02-05T10:30:00Z",
  },
  {
    user_id: "usr_002",
    email: "bob@example.com",
    total_orders: 8,
    revenue: 890.25,
    signup_date: "2024-02-20",
    is_active: true,
    last_login: "2026-02-04T14:22:00Z",
  },
  {
    user_id: "usr_003",
    email: "carol@example.com",
    total_orders: 25,
    revenue: 3250.75,
    signup_date: "2023-11-10",
    is_active: true,
    last_login: "2026-02-06T08:15:00Z",
  },
  {
    user_id: "usr_004",
    email: "dave@example.com",
    total_orders: 0,
    revenue: 0,
    signup_date: "2024-03-01",
    is_active: false,
    last_login: "2024-06-20T16:45:00Z",
  },
  {
    user_id: "usr_005",
    email: "eve@example.com",
    total_orders: 45,
    revenue: 8920.0,
    signup_date: "2023-08-05",
    is_active: true,
    last_login: "2026-02-06T09:00:00Z",
  },
];

// Mock data with many columns to test horizontal scrolling
const wideTableData = [
  {
    id: 1,
    col_a: "Value A1",
    col_b: "Value B1",
    col_c: "Value C1",
    col_d: "Value D1",
    col_e: "Value E1",
    col_f: "Value F1",
    col_g: "Value G1",
    col_h: "Value H1",
    col_i: "Value I1",
    col_j: "Value J1",
    col_k: "Value K1",
    col_l: "Value L1",
    col_m: "Value M1",
    col_n: "Value N1",
    col_o: "Value O1",
    col_p: "Value P1",
    col_q: "Value Q1",
    col_r: "Value R1",
    col_s: "Value S1",
    col_t: "Value T1",
  },
  {
    id: 2,
    col_a: "Value A2",
    col_b: "Value B2",
    col_c: "Value C2",
    col_d: "Value D2",
    col_e: "Value E2",
    col_f: "Value F2",
    col_g: "Value G2",
    col_h: "Value H2",
    col_i: "Value I2",
    col_j: "Value J2",
    col_k: "Value K2",
    col_l: "Value L2",
    col_m: "Value M2",
    col_n: "Value N2",
    col_o: "Value O2",
    col_p: "Value P2",
    col_q: "Value Q2",
    col_r: "Value R2",
    col_s: "Value S2",
    col_t: "Value T2",
  },
  {
    id: 3,
    col_a: "Value A3",
    col_b: "Value B3",
    col_c: "Value C3",
    col_d: "Value D3",
    col_e: "Value E3",
    col_f: "Value F3",
    col_g: "Value G3",
    col_h: "Value H3",
    col_i: "Value I3",
    col_j: "Value J3",
    col_k: "Value K3",
    col_l: "Value L3",
    col_m: "Value M3",
    col_n: "Value N3",
    col_o: "Value O3",
    col_p: "Value P3",
    col_q: "Value Q3",
    col_r: "Value R3",
    col_s: "Value S3",
    col_t: "Value T3",
  },
];

// Helper function to generate GraphQL response structure
function createPreviewDataResponse(
  datasetId: string,
  modelId: string,
  modelName: string,
  previewData: any[],
) {
  return {
    data: {
      datasets: {
        edges: [
          {
            node: {
              id: datasetId,
              typeDefinition: {
                __typename: "DataModelDefinition",
                dataModels: {
                  edges: [
                    {
                      node: {
                        id: modelId,
                        name: modelName,
                        previewData: previewData,
                      },
                    },
                  ],
                },
              },
            },
          },
        ],
      },
    },
  };
}

const mswMock = http.post("/api/v1/osograph", async ({ request }) => {
  const {
    variables: { datasetId },
  } = (await request.json()) as { variables: { datasetId: string } };

  if (datasetId === "dataset_abc123") {
    return HttpResponse.json(
      createPreviewDataResponse(
        "dataset_abc123",
        "model_users_001",
        "users",
        userActivityData,
      ),
    );
  } else if (datasetId === "dataset_wide") {
    return HttpResponse.json(
      createPreviewDataResponse(
        "dataset_wide",
        "model_wide_001",
        "wide_table",
        wideTableData,
      ),
    );
  } else if (datasetId === "dataset_empty") {
    return HttpResponse.json(
      createPreviewDataResponse(
        "dataset_empty",
        "model_empty_001",
        "empty",
        [],
      ),
    );
  } else if (datasetId === "dataset_error") {
    return HttpResponse.json(
      {
        errors: [
          {
            message: "Failed to fetch preview data: Network connection timeout",
          },
        ],
      },
      { status: 500 },
    );
  } else if (datasetId === "dataset_loading") {
    await delay("infinite");
  }

  throw new Error(`No mock handler for datasetId: ${datasetId}`);
});
// Default story with normal user data
export const Default: Story = {
  args: {
    datasetId: "dataset_abc123",
    modelOrTable: "model_users_001",
  },
  parameters: {
    msw: {
      handlers: [mswMock],
    },
  },
};

// Loading state - skeleton loaders
export const LoadingState: Story = {
  args: {
    datasetId: "dataset_loading",
    modelOrTable: "model_users_002",
  },
  parameters: {
    msw: {
      handlers: [mswMock],
    },
  },
};

// Error state - shows error message with retry button
export const ErrorState: Story = {
  args: {
    datasetId: "dataset_error",
    modelOrTable: "model_users_003",
  },
  parameters: {
    msw: {
      handlers: [mswMock],
    },
  },
};

// Empty data state
export const EmptyData: Story = {
  args: {
    datasetId: "dataset_empty",
    modelOrTable: "model_empty_001",
  },
  parameters: {
    msw: {
      handlers: [mswMock],
    },
  },
};

// Wide table with many columns to test horizontal scrolling
export const WideTable: Story = {
  args: {
    datasetId: "dataset_wide",
    modelOrTable: "model_wide_001",
  },
  parameters: {
    msw: {
      handlers: [mswMock],
    },
  },
};
