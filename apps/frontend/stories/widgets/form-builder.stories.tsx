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
