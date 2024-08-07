import { repeatedElement } from "@plasmicapp/loader-nextjs";
import React, { ReactElement, ReactNode } from "react";
import _ from "lodash";
import { plasmicRegistration } from "../../lib/plasmic-register";
import { DataProvider } from "@plasmicapp/loader-nextjs";

export interface MaxWidthRepeatProps {
  className?: string;
  data: Array<any>;
  columnSize: number;
  children?: ReactNode;
  horizontal?: ReactElement;
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

  const horizontal = !props.horizontal ? <div></div> : props.horizontal;

  const horizontalCreate = (children: ReactNode) => {
    return React.cloneElement(horizontal, [], children);
  };

  const rowRender = (chunk: Array<any>, rowIndex: number) => (
    <>
      {chunk.map((data, columnIndex) => {
        const elementIndex = rowIndex * columnSize + columnIndex;
        return (
          <DataProvider name="current" data={data} key={elementIndex}>
            {repeatedElement(elementIndex, children)}
          </DataProvider>
        );
      })}
    </>
  );

  return (
    <div className={className}>
      {chunked.map((chunk, rowIndex) => {
        return horizontalCreate(rowRender(chunk, rowIndex));
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
    horizontal: "slot",
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
  defaultStyles: {
    layout: "hbox",
  },
});
