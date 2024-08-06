import { repeatedElement } from "@plasmicapp/loader-nextjs";
import React, { ReactNode } from "react";
import _ from "lodash";
import { plasmicRegistration } from "../../lib/plasmic-register";
import { DataProvider } from "@plasmicapp/loader-nextjs";

export interface MaxWidthRepeatProps {
  className?: string;
  data: Array<any>;
  columnSize: number;
  children?: ReactNode;
  useTestData: boolean;
  testData: Array<any>;
}

/**
 * Allows repeating a user defined repeatable element with a maximum width
 *
 * @param props Properties
 * @returns
 */
export function MaxWidthRepeat(props: MaxWidthRepeatProps) {
  const { className, data, columnSize, children, testData, useTestData } =
    props;
  const chunked = useTestData
    ? _.chunk(testData, columnSize)
    : _.chunk(data, columnSize);

  return (
    <div className={className}>
      {chunked.map((chunk, rowIndex) => {
        return (
          <div key={rowIndex}>
            {chunk.map((data, columnIndex) => {
              const elementIndex = rowIndex * columnSize + columnIndex;
              return (
                <DataProvider name="current" data={data} key={elementIndex}>
                  {repeatedElement(elementIndex, children)}
                </DataProvider>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export const MaxWidthRepeatRegistration = plasmicRegistration(MaxWidthRepeat, {
  name: "MaxWithRepeat",
  description: "A component that repeats an internal component",
  providesData: true,
  props: {
    children: "slot",
    columnSize: {
      type: "number",
      defaultValue: 1,
      helpText: "Max number of columns",
    },
    data: {
      type: "object",
      defaultValue: [],
      helpText: "The data to render",
    },
    useTestData: {
      type: "boolean",
      helpText: "Render with test data",
      editOnly: true,
    },
    testData: "object",
  },
});
