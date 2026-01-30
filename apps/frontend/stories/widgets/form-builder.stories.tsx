import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { FormBuilder, FormSchema } from "@/components/widgets/form-builder";
import { action } from "storybook/actions";
import { Button } from "@/components/ui/button";
import React from "react";

const meta = {
  title: "widgets/FormBuilder",
  component: FormBuilder,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof FormBuilder>;

export default meta;
type Story = StoryObj<typeof meta>;

const simpleSchema: FormSchema = {
  firstName: {
    type: "string",
    label: "First Name",
    required: true,
  },
  lastName: {
    type: "string",
    label: "Last Name",
  },
  age: {
    type: "number",
    label: "Age",
    required: true,
    description: "Please enter your age in years.",
  },
  birthDate: {
    type: "date",
    label: "Birth Date",
    required: true,
  },
};

export const SimpleForm: Story = {
  args: {
    schema: simpleSchema,
    onSubmit: action("onSubmit"),
    className: "w-[400px]",
  },
};

const complexSchema: FormSchema = {
  personalInfo: {
    type: "object",
    label: "Personal Information",
    properties: {
      fullName: {
        type: "string",
        label: "Full Name",
        required: true,
        defaultValue: "John Doe",
      },
      email: {
        type: "string",
        label: "Email",
        required: true,
        description: "We will not share your email.",
      },
    },
  },
  preferences: {
    type: "object",
    label: "Preferences",
    properties: {
      newsletter: {
        type: "string",
        label: "Newsletter",
        options: ["Daily", "Weekly", "Monthly", "Never"],
        required: true,
      },
      favoriteNumber: {
        type: "number",
        label: "Favorite Number",
      },
      receiveUpdates: {
        type: "boolean",
        label: "Receive Updates",
        description: "Get notified about new features.",
        defaultValue: true,
      },
    },
  },
};

export const ComplexForm: Story = {
  args: {
    schema: complexSchema,
    onSubmit: action("onSubmit"),
    className: "w-[400px]",
  },
};

const withDefaultsAndPlaceholdersSchema: FormSchema = {
  username: {
    type: "string",
    label: "Username",
    required: true,
    placeholder: "Enter your username",
  },
  role: {
    type: "string",
    label: "Role",
    options: ["Admin", "User", "Guest"],
    defaultValue: "User",
    placeholder: "Select a role",
  },
  profile: {
    type: "object",
    label: "Profile",
    properties: {
      bio: {
        type: "string",
        label: "Biography",
        defaultValue: "A default bio.",
        placeholder: "Tell us about yourself",
      },
      experience: {
        type: "number",
        label: "Years of Experience",
        defaultValue: 5,
        placeholder: "e.g., 10",
      },
    },
  },
};

export const WithDefaultsAndPlaceholders: Story = {
  args: {
    schema: withDefaultsAndPlaceholdersSchema,
    onSubmit: action("onSubmit"),
    className: "w-[400px]",
  },
};

export const WithCustomFooter: Story = {
  args: {
    schema: simpleSchema,
    onSubmit: action("onSubmit"),
    className: "w-[400px]",
    footer: (
      <div className="flex justify-end space-x-2">
        <Button variant="outline" type="button">
          Cancel
        </Button>
        <Button type="submit">Save Changes</Button>
      </div>
    ),
  },
};

const withDisabledAndHiddenFieldsSchema: FormSchema = {
  visibleField: {
    type: "string",
    label: "Visible Field",
    defaultValue: "I am visible",
  },
  disabledField: {
    type: "string",
    label: "Disabled Field",
    defaultValue: "I am disabled",
    disabled: true,
  },
  hiddenField: {
    type: "string",
    label: "Hidden Field",
    defaultValue: "I should not be visible",
    hidden: true,
  },
};

export const WithDisabledAndHiddenFields: Story = {
  args: {
    schema: withDisabledAndHiddenFieldsSchema,
    onSubmit: action("onSubmit"),
    className: "w-[400px]",
  },
};

export const HorizontalForm: Story = {
  args: {
    schema: simpleSchema,
    onSubmit: action("onSubmit"),
    className: "w-[600px]",
    horizontal: true,
  },
};

const advancedSchema: FormSchema = {
  name: {
    type: "string",
    label: "Name",
    required: true,
    placeholder: "my_source",
  },
  endpoint: {
    type: "string",
    label: "Endpoint",
    required: true,
    placeholder: "https://api.example.com/graphql",
  },
  paginationType: {
    type: "string",
    label: "Pagination Type",
    options: ["OFFSET", "CURSOR", "RELAY", "KEYSET"],
    placeholder: "Select pagination",
    advanced: true,
    advancedGroup: "Pagination",
  },
  pageSize: {
    type: "number",
    label: "Page Size",
    placeholder: "50",
    advanced: true,
    advancedGroup: "Pagination",
  },
  retryEnabled: {
    type: "boolean",
    label: "Enable Retry",
    advanced: true,
    advancedGroup: "Retry",
  },
  retryMax: {
    type: "number",
    label: "Max Retries",
    placeholder: "3",
    advanced: true,
    advancedGroup: "Retry",
  },
};

export const WithAdvancedGroups: Story = {
  args: {
    schema: advancedSchema,
    onSubmit: action("onSubmit"),
    className: "w-[600px]",
  },
};

const arraySchema: FormSchema = {
  tags: {
    type: "array",
    label: "Tags",
    itemType: "string",
    description: "Add tags to categorize your item",
    required: true,
  },
  priorities: {
    type: "array",
    label: "Priorities",
    itemType: "number",
    description: "Add priority values (numbers)",
  },
  features: {
    type: "array",
    label: "Features",
    itemType: "boolean",
    description: "Toggle features on/off",
  },
};

export const WithArrayFields: Story = {
  args: {
    schema: arraySchema,
    onSubmit: action("onSubmit"),
    className: "w-[600px]",
  },
};

const arrayWithOptionsSchema: FormSchema = {
  categories: {
    type: "array",
    label: "Categories",
    itemType: "string",
    itemOptions: ["Technology", "Science", "Arts", "Sports", "Music"],
    description: "Select categories from the list",
    required: true,
  },
  customRoles: {
    type: "array",
    label: "Custom Role Names",
    itemType: "string",
    description: "Enter custom role names",
  },
};

export const WithArrayInputsAndOptions: Story = {
  args: {
    schema: arrayWithOptionsSchema,
    onSubmit: action("onSubmit"),
    className: "w-[600px]",
  },
};

const arrayOfObjectsSchema: FormSchema = {
  resources: {
    type: "array",
    label: "Resources",
    itemType: "object",
    itemProperties: {
      name: {
        type: "string",
        label: "Resource Name",
        required: true,
      },
      endpoint: {
        type: "string",
        label: "Endpoint",
        required: true,
      },
      write_disposition: {
        type: "string",
        label: "Write Disposition",
        options: ["merge", "append", "replace"],
      },
    },
    description: "List of API endpoint definitions",
    required: true,
  },
};

export const WithArrayOfObjects: Story = {
  args: {
    schema: arrayOfObjectsSchema,
    onSubmit: action("onSubmit"),
    className: "w-[700px]",
  },
};

export const WithDefaultValuesOverride: Story = {
  args: {
    schema: simpleSchema,
    defaultValues: {
      firstName: "Jane",
      lastName: "Smith",
      age: 30,
      birthDate: new Date("1994-01-15"),
    },
    onSubmit: action("onSubmit"),
    className: "w-[400px]",
  },
};

const dynamicObjectSchema: FormSchema = {
  headers: {
    type: "object",
    label: "HTTP Headers",
    allowDynamicKeys: true,
    description: "Add custom HTTP headers as key-value pairs",
    defaultValue: {
      "Content-Type": "application/json",
      Authorization: "Bearer token123",
    },
  },
  queryParams: {
    type: "object",
    label: "Query Parameters",
    allowDynamicKeys: true,
    description: "Add query parameters for the request",
    skipIfEmpty: true,
  },
  metadata: {
    type: "object",
    label: "Custom Metadata",
    allowDynamicKeys: true,
    required: true,
    description: "Required metadata fields",
  },
};

export const WithDynamicObjects: Story = {
  args: {
    schema: dynamicObjectSchema,
    onSubmit: action("onSubmit"),
    className: "w-[700px]",
  },
};

const simpleUnionSchema: FormSchema = {
  notificationType: {
    type: "union",
    label: "Notification Type",
    required: true,
    discriminator: "type",
    variantSelector: "dropdown",
    variants: [
      {
        value: "email",
        label: "Email",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "email",
            hidden: true,
          },
          emailAddress: {
            type: "string",
            label: "Email Address",
            required: true,
            placeholder: "user@example.com",
          },
          subject: {
            type: "string",
            label: "Subject",
            required: true,
            placeholder: "Notification subject",
          },
        },
      },
      {
        value: "sms",
        label: "SMS",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "sms",
            hidden: true,
          },
          phoneNumber: {
            type: "string",
            label: "Phone Number",
            required: true,
            placeholder: "+1234567890",
          },
          message: {
            type: "string",
            label: "Message",
            required: true,
            placeholder: "Your message here",
          },
        },
      },
      {
        value: "push",
        label: "Push Notification",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "push",
            hidden: true,
          },
          deviceId: {
            type: "string",
            label: "Device ID",
            required: true,
            placeholder: "device-12345",
          },
          title: {
            type: "string",
            label: "Title",
            required: true,
            placeholder: "Notification title",
          },
          body: {
            type: "string",
            label: "Body",
            required: true,
            placeholder: "Notification body",
          },
        },
      },
    ],
  },
};

export const WithSimpleUnion: Story = {
  args: {
    schema: simpleUnionSchema,
    onSubmit: action("onSubmit"),
    className: "w-[600px]",
  },
};

const authenticationSchema: FormSchema = {
  apiUrl: {
    type: "string",
    label: "API URL",
    required: true,
    placeholder: "https://api.example.com",
  },
  authentication: {
    type: "union",
    label: "Authentication Method",
    description: "Choose how to authenticate with the API",
    discriminator: "type",
    variantSelector: "tabs",
    nullable: true,
    variants: [
      {
        value: "bearer",
        label: "Bearer Token",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "bearer",
            hidden: true,
          },
          token: {
            type: "string",
            label: "Token",
            required: true,
            placeholder: "your-bearer-token",
          },
        },
      },
      {
        value: "api_key",
        label: "API Key",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "api_key",
            hidden: true,
          },
          apiKey: {
            type: "string",
            label: "API Key",
            required: true,
            placeholder: "your-api-key",
          },
          headerName: {
            type: "string",
            label: "Header Name",
            defaultValue: "X-API-Key",
            placeholder: "X-API-Key",
          },
        },
      },
      {
        value: "basic",
        label: "Basic Auth",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "basic",
            hidden: true,
          },
          username: {
            type: "string",
            label: "Username",
            required: true,
            placeholder: "username",
          },
          password: {
            type: "string",
            label: "Password",
            required: true,
            placeholder: "password",
          },
        },
      },
    ],
  },
};

export const WithAuthenticationUnion: Story = {
  args: {
    schema: authenticationSchema,
    onSubmit: action("onSubmit"),
    className: "w-[700px]",
  },
};

const endpointConfigSchema: FormSchema = {
  resourceName: {
    type: "string",
    label: "Resource Name",
    required: true,
    placeholder: "users",
  },
  endpoint: {
    type: "union",
    label: "Endpoint Configuration",
    description: "Configure the API endpoint",
    collapseNested: false,
    variants: [
      {
        value: "simple",
        label: "Simple Path",
        properties: {
          path: {
            type: "string",
            label: "Endpoint Path",
            required: true,
            placeholder: "/api/users",
          },
        },
      },
      {
        value: "advanced",
        label: "Advanced Configuration",
        properties: {
          path: {
            type: "string",
            label: "Endpoint Path",
            placeholder: "/api/users",
            skipIfEmpty: true,
          },
          method: {
            type: "string",
            label: "HTTP Method",
            options: ["GET", "POST", "PUT", "PATCH", "DELETE"],
            defaultValue: "GET",
          },
          headers: {
            type: "object",
            label: "Headers",
            description: "Custom headers for this endpoint",
            allowDynamicKeys: true,
            skipIfEmpty: true,
          },
          params: {
            type: "object",
            label: "Query Parameters",
            description: "Query parameters for the request",
            allowDynamicKeys: true,
            skipIfEmpty: true,
          },
        },
      },
    ],
  },
};

export const WithEndpointUnion: Story = {
  args: {
    schema: endpointConfigSchema,
    onSubmit: action("onSubmit"),
    className: "w-[800px]",
  },
};

const paginationSchema: FormSchema = {
  dataSource: {
    type: "string",
    label: "Data Source",
    required: true,
    placeholder: "API endpoint",
  },
  pagination: {
    type: "union",
    label: "Pagination Strategy",
    description: "Choose how to paginate through results",
    discriminator: "type",
    variantSelector: "dropdown",
    nullable: true,
    collapseNested: true,
    variants: [
      {
        value: "offset",
        label: "Offset-based",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "offset",
            hidden: true,
          },
          limit: {
            type: "number",
            label: "Page Size",
            required: true,
            defaultValue: 100,
            placeholder: "100",
          },
          offsetParam: {
            type: "string",
            label: "Offset Parameter",
            defaultValue: "offset",
            placeholder: "offset",
          },
          limitParam: {
            type: "string",
            label: "Limit Parameter",
            defaultValue: "limit",
            placeholder: "limit",
          },
        },
      },
      {
        value: "cursor",
        label: "Cursor-based",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "cursor",
            hidden: true,
          },
          cursorPath: {
            type: "string",
            label: "Cursor Path (JSONPath)",
            required: true,
            placeholder: "$.pagination.next_cursor",
            description: "Path to next cursor in response",
          },
          cursorParam: {
            type: "string",
            label: "Cursor Parameter",
            defaultValue: "cursor",
            placeholder: "cursor",
          },
        },
      },
      {
        value: "page_number",
        label: "Page Number",
        properties: {
          type: {
            type: "string",
            label: "Type",
            defaultValue: "page_number",
            hidden: true,
          },
          pageSize: {
            type: "number",
            label: "Page Size",
            required: true,
            defaultValue: 50,
            placeholder: "50",
          },
          startPage: {
            type: "number",
            label: "Starting Page",
            defaultValue: 1,
            placeholder: "1",
          },
          pageParam: {
            type: "string",
            label: "Page Parameter",
            defaultValue: "page",
            placeholder: "page",
          },
        },
      },
    ],
  },
};

export const WithPaginationUnion: Story = {
  args: {
    schema: paginationSchema,
    onSubmit: action("onSubmit"),
    className: "w-[700px]",
  },
};

const nestedUnionSchema: FormSchema = {
  resources: {
    type: "array",
    label: "API Resources",
    itemType: "object",
    description:
      "Configure multiple API endpoints with different authentication",
    itemProperties: {
      name: {
        type: "string",
        label: "Name",
        required: true,
        placeholder: "resource_name",
      },
      endpoint: {
        type: "string",
        label: "Endpoint Path",
        required: true,
        placeholder: "/api/resource",
      },
      auth: {
        type: "union",
        label: "Authentication",
        discriminator: "type",
        variantSelector: "dropdown",
        nullable: true,
        collapseNested: true,
        variants: [
          {
            value: "inherit",
            label: "Inherit from Global",
            properties: {
              type: {
                type: "string",
                label: "Type",
                defaultValue: "inherit",
                hidden: true,
              },
            },
          },
          {
            value: "bearer",
            label: "Bearer Token",
            properties: {
              type: {
                type: "string",
                label: "Type",
                defaultValue: "bearer",
                hidden: true,
              },
              token: {
                type: "string",
                label: "Token",
                required: true,
                placeholder: "resource-specific-token",
              },
            },
          },
          {
            value: "api_key",
            label: "API Key",
            properties: {
              type: {
                type: "string",
                label: "Type",
                defaultValue: "api_key",
                hidden: true,
              },
              key: {
                type: "string",
                label: "API Key",
                required: true,
                placeholder: "resource-specific-key",
              },
            },
          },
        ],
      },
    },
  },
};

export const WithNestedUnionsInArray: Story = {
  args: {
    schema: nestedUnionSchema,
    onSubmit: action("onSubmit"),
    className: "w-[900px]",
  },
};

const dynamicObjectWithDefaultsSchema: FormSchema = {
  apiEndpoint: {
    type: "string",
    label: "API Endpoint",
    required: true,
    placeholder: "https://api.example.com",
  },
  headers: {
    type: "object",
    label: "Request Headers",
    allowDynamicKeys: true,
    description: "Custom headers for the API request",
  },
  queryParams: {
    type: "object",
    label: "Query Parameters",
    allowDynamicKeys: true,
    description: "Query parameters to send with the request",
  },
};

export const WithDynamicObjectDefaults: Story = {
  args: {
    schema: dynamicObjectWithDefaultsSchema,
    defaultValues: {
      apiEndpoint: "https://api.github.com/repos/test/repo",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer github_pat_123",
        "X-Custom-Header": "custom-value",
      },
      queryParams: {
        page: "1",
        per_page: "100",
        sort: "created",
      },
    },
    onSubmit: action("onSubmit"),
    className: "w-[800px]",
  },
};

const unionWithDynamicObjectSchema: FormSchema = {
  resourceName: {
    type: "string",
    label: "Resource Name",
    required: true,
    placeholder: "users",
  },
  config: {
    type: "union",
    label: "Configuration Type",
    description: "Choose how to configure this resource",
    variantSelector: "dropdown",
    variants: [
      {
        value: "basic",
        label: "Basic Configuration",
        properties: {
          endpoint: {
            type: "string",
            label: "Endpoint URL",
            required: true,
            placeholder: "/api/users",
          },
        },
      },
      {
        value: "advanced",
        label: "Advanced Configuration",
        properties: {
          endpoint: {
            type: "string",
            label: "Endpoint URL",
            required: true,
            placeholder: "/api/users",
          },
          method: {
            type: "string",
            label: "HTTP Method",
            options: ["GET", "POST", "PUT", "PATCH", "DELETE"],
            defaultValue: "GET",
          },
          headers: {
            type: "object",
            label: "Custom Headers",
            description: "Headers specific to this endpoint",
            allowDynamicKeys: true,
            skipIfEmpty: true,
          },
          queryParams: {
            type: "object",
            label: "Query Parameters",
            description: "Default query parameters for this endpoint",
            allowDynamicKeys: true,
            skipIfEmpty: true,
          },
        },
      },
    ],
  },
};

export const WithUnionContainingDynamicObjectDefaults: Story = {
  args: {
    schema: unionWithDynamicObjectSchema,
    defaultValues: {
      resourceName: "repositories",
      config: {
        endpoint: "/api/v1/repositories",
        method: "GET",
        headers: {
          Authorization: "Bearer token_xyz",
          Accept: "application/vnd.github.v3+json",
        },
        queryParams: {
          type: "all",
          sort: "updated",
          direction: "desc",
        },
      },
    },
    onSubmit: action("onSubmit"),
    className: "w-[900px]",
  },
};

const validationErrorSchema: FormSchema = {
  username: {
    type: "string",
    label: "Username",
    required: true,
    description: "Your unique username",
  },
  email: {
    type: "string",
    label: "Email Address",
    required: true,
  },
  profile: {
    type: "object",
    label: "Profile Information",
    properties: {
      bio: {
        type: "string",
        label: "Biography",
        required: true,
      },
      age: {
        type: "number",
        label: "Age",
        required: true,
      },
    },
  },
  tags: {
    type: "array",
    label: "Tags",
    itemType: "string",
    required: true,
    description: "At least one tag is required",
  },
  apiKey: {
    type: "string",
    label: "API Key",
    required: true,
    advanced: true,
    advancedGroup: "Advanced Settings",
  },
};

export const WithValidationErrors: Story = {
  args: {
    schema: validationErrorSchema,
    onSubmit: action("onSubmit"),
    className: "w-[600px]",
  },
};
