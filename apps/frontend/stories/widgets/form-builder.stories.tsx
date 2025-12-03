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
