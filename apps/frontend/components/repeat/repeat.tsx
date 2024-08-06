import { repeatedElement } from "@plasmicapp/loader-nextjs";
import React, { ReactNode } from "react";
import _ from "lodash";
import { plasmicRegistration } from "../../lib/plasmic-register";

const RepeatContext = React.createContext<any | undefined>(undefined);

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
  const { className, data, columnSize, children } = props;
  const chunked = _.chunk(data, columnSize);

  return (
    <div className={className}>
      {chunked.map((chunk, rowIndex) => {
        return (
          <div key={rowIndex}>
            {chunk.map((data, columnIndex) => {
              const elementIndex = rowIndex * columnSize + columnIndex;
              return (
                <RepeatContext.Provider value={data} key={elementIndex}>
                  {repeatedElement(elementIndex, children)}
                </RepeatContext.Provider>
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
  props: {
    children: "slot",
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
