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
