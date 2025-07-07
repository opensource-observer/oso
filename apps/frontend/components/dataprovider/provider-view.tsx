import { DataProvider } from "@plasmicapp/loader-nextjs";
import { ReactNode } from "react";
import { RegistrationProps } from "@/lib/types/plasmic";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_VARIABLE_NAME = "data";

type CommonDataProviderProps = {
  className?: string; // Plasmic CSS class
  variableName?: string; // Name to use in Plasmic data picker
  children?: ReactNode; // Show this
  loadingChildren?: ReactNode; // Show during loading if !ignoreLoading
  ignoreLoading?: boolean; // Skip the loading visual
  forceLoading?: boolean; // Display the loadingChildren (Studio only)
  errorChildren?: ReactNode; // Show if error
  ignoreError?: boolean; // Skip the error visual
  forceError?: boolean; // Display errorChildren (Studio only)
  useTestData?: boolean; // Use the testData prop instead of querying database
  testData?: any;
};

type DataProviderViewProps = CommonDataProviderProps & {
  formattedData: any;
  loading: boolean;
  error?: Error | null;
};

const CommonDataProviderRegistration: RegistrationProps<CommonDataProviderProps> =
  {
    // Data variable
    variableName: {
      type: "string",
      helpText: "Name to use in Plasmic data picker. Must be unique per query.",
    },
    // Plasmic elements
    children: {
      type: "slot",
      defaultValue: {
        type: "text",
        value: "Placeholder",
      },
    },
    loadingChildren: {
      type: "slot",
      defaultValue: {
        type: "text",
        value: "Placeholder",
      },
    },
    ignoreLoading: {
      type: "boolean",
      helpText: "Don't show 'loadingChildren' even if we're still loading data",
      advanced: true,
    },
    forceLoading: {
      type: "boolean",
      helpText: "Render loadingChildren",
      editOnly: true,
      advanced: true,
    },
    errorChildren: {
      type: "slot",
      defaultValue: {
        type: "text",
        value: "Placeholder",
      },
    },
    ignoreError: {
      type: "boolean",
      helpText: "Don't show 'errorChildren' even if we get an error",
      advanced: true,
    },
    forceError: {
      type: "boolean",
      helpText: "Render errorChildren",
      editOnly: true,
      advanced: true,
    },
    useTestData: {
      type: "boolean",
      helpText: "Render with test data",
      editOnly: true,
      advanced: true,
    },
    testData: {
      type: "object",
      advanced: true,
    },
  };

/**
 * Common view logic for EventDataProviders
 * @param props
 * @returns
 */
function DataProviderView(props: DataProviderViewProps) {
  const key = props.variableName ?? DEFAULT_VARIABLE_NAME;
  // Show when loading or error
  if (
    props.forceLoading ||
    (!props.useTestData &&
      props.loading &&
      !props.ignoreLoading &&
      !!props.loadingChildren)
  ) {
    return <div className={props.className}> {props.loadingChildren} </div>;
  } else if (
    props.forceError ||
    (!props.useTestData &&
      props.error &&
      !props.ignoreError &&
      !!props.errorChildren)
  ) {
    return (
      <div className={props.className}>
        <DataProvider name={key} data={props.error}>
          {props.errorChildren}
        </DataProvider>
      </div>
    );
  }
  const data = props.useTestData ? props.testData : props.formattedData;
  return (
    <div className={props.className}>
      <DataProvider name={key} data={data}>
        {props.children}
      </DataProvider>
    </div>
  );
}

export { CommonDataProviderRegistration, DataProviderView };
export type { CommonDataProviderProps };
