import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { ControllableNotebook } from "@/components/widgets/controllable-notebook";
import { action } from "storybook/actions";
import { fn } from "storybook/test";

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories#default-export
const meta = {
  title: "widgets/ControllableNotebook",
  component: ControllableNotebook,
  parameters: {
    // Optional parameter to center the component in the Canvas. More info: https://storybook.js.org/docs/configure/story-layout
    layout: "fullscreen",
  },
  // This component will have an automatically generated Autodocs entry: https://storybook.js.org/docs/writing-docs/autodocs
  tags: ["autodocs"],
  // More on argTypes: https://storybook.js.org/docs/api/argtypes
  argTypes: {
    //backgroundColor: { control: 'color' },
  },
  args: {
    onNotebookConnected: fn(),
  },
} satisfies Meta<typeof ControllableNotebook>;

export default meta;
type Story = StoryObj<typeof meta>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {
  args: {
    notebookId: "test-notebook-id",
    className: "h-full w-full",
    hostControls: {
      saveNotebook: async (contents: string) => {
        action("saveNotebook")(contents);
        console.log("Saving notebook with contents:", contents);
      },
      readNotebook: async () => {
        action("readNotebook")();
        console.log("Reading notebook, returning null");
        return null;
      },
    },
    initialCode: "",
    notebookUrl:
      process.env.VITE_NOTEBOOK_URL ||
      process.env.NEXT_PUBLIC_NOTEBOOK_URL ||
      "https://marimo.opensource.observer/notebook",
    environment: {
      OSO_API_KEY: "test-api-key",
    },
    mode: "edit",
  },
  decorators: [
    (Story) => (
      <div style={{ height: "100vh" }}>
        <Story />
      </div>
    ),
  ],
};
