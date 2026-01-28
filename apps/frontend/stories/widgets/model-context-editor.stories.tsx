import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { ModelContextEditor } from "@/components/widgets/model-context-editor";
import type {
  DataModelColumn,
  ModelContext,
} from "@/lib/graphql/generated/graphql";

const meta = {
  title: "widgets/ModelContextEditor",
  component: ModelContextEditor,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  argTypes: {
    datasetId: {
      control: "text",
    },
    modelId: {
      control: "text",
    },
    schema: {
      control: "object",
    },
    existingContext: {
      control: "object",
    },
  },
} satisfies Meta<typeof ModelContextEditor>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleSchema: DataModelColumn[] = [
  {
    name: "user_id",
    type: "STRING",
    description: "Unique identifier for the user",
  },
  {
    name: "email",
    type: "STRING",
    description: "User's email address",
  },
  {
    name: "created_at",
    type: "TIMESTAMP",
    description: "Timestamp when the user was created",
  },
  {
    name: "is_active",
    type: "BOOLEAN",
    description: "Whether the user account is active",
  },
  {
    name: "total_orders",
    type: "INTEGER",
    description: null,
  },
];

const largeSchema: DataModelColumn[] = [
  {
    name: "transaction_id",
    type: "STRING",
    description: "Unique transaction identifier",
  },
  {
    name: "user_id",
    type: "STRING",
    description: "Reference to the user who made the transaction",
  },
  {
    name: "product_id",
    type: "STRING",
    description: "Reference to the product being purchased",
  },
  {
    name: "amount",
    type: "DECIMAL",
    description: "Transaction amount in USD",
  },
  {
    name: "currency",
    type: "STRING",
    description: "Currency code (ISO 4217)",
  },
  {
    name: "status",
    type: "STRING",
    description: "Transaction status (pending, completed, failed, refunded)",
  },
  {
    name: "payment_method",
    type: "STRING",
    description: "Payment method used (credit_card, debit_card, paypal, etc.)",
  },
  {
    name: "created_at",
    type: "TIMESTAMP",
    description: "When the transaction was initiated",
  },
  {
    name: "updated_at",
    type: "TIMESTAMP",
    description: "When the transaction was last updated",
  },
  {
    name: "completed_at",
    type: "TIMESTAMP",
    description: null,
  },
  {
    name: "merchant_id",
    type: "STRING",
    description: "Merchant or vendor identifier",
  },
  {
    name: "fee_amount",
    type: "DECIMAL",
    description: "Transaction processing fee",
  },
];

const existingContextWithData: Pick<ModelContext, "context" | "columnContext"> =
  {
    context:
      "This table contains user information for the application. It includes basic user details and activity status.",
    columnContext: [
      {
        name: "user_id",
        context: "Primary key. Always non-null and unique across all users.",
      },
      {
        name: "email",
        context:
          "Must be a valid email format. Used for login and notifications.",
      },
      {
        name: "is_active",
        context:
          "False indicates the account has been deactivated or suspended.",
      },
    ],
  };

const existingContextWithStaleColumns: Pick<
  ModelContext,
  "context" | "columnContext"
> = {
  context: "User data model with some outdated column contexts",
  columnContext: [
    {
      name: "user_id",
      context: "User identifier",
    },
    {
      name: "old_column_name",
      context:
        "This column no longer exists in the schema and should be filtered out",
    },
    {
      name: "another_removed_column",
      context: "Another stale column context",
    },
    {
      name: "email",
      context: "Email address",
    },
  ],
};

export const Empty: Story = {
  args: {
    datasetId: "dataset_001",
    modelId: "users",
    schema: sampleSchema,
    existingContext: null,
  },
};

export const WithExistingContext: Story = {
  args: {
    datasetId: "dataset_001",
    modelId: "users",
    schema: sampleSchema,
    existingContext: existingContextWithData,
  },
};

export const WithStaleColumns: Story = {
  args: {
    datasetId: "dataset_001",
    modelId: "users",
    schema: sampleSchema,
    existingContext: existingContextWithStaleColumns,
  },
};

export const LargeSchema: Story = {
  args: {
    datasetId: "dataset_002",
    modelId: "transactions",
    schema: largeSchema,
    existingContext: {
      context:
        "Comprehensive transaction data model tracking all financial transactions across the platform. Used for reporting, analytics, and reconciliation.",
      columnContext: [
        {
          name: "transaction_id",
          context: "UUID v4 format. Generated on transaction creation.",
        },
        {
          name: "amount",
          context: "Always positive. Refunds are tracked separately.",
        },
        {
          name: "status",
          context:
            "Workflow: pending -> completed/failed. Refunded is a terminal state.",
        },
      ],
    },
  },
};

export const MinimalSchema: Story = {
  args: {
    datasetId: "dataset_003",
    modelId: "simple_model",
    schema: [
      {
        name: "id",
        type: "STRING",
        description: null,
      },
      {
        name: "value",
        type: "INTEGER",
        description: null,
      },
    ],
    existingContext: null,
  },
};

export const NoSchema: Story = {
  args: {
    datasetId: "dataset_004",
    modelId: "pending_model",
    schema: undefined,
    existingContext: null,
  },
};
