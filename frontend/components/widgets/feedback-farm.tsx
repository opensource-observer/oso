import React, { ReactElement } from "react";
import { FeedbackFarm } from "@feedbackfarm/react";

export type FeedbackWrapperProps = {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this
};

function FeedbackWrapper(props: FeedbackWrapperProps) {
  const { className, children } = props;

  if (!children) {
    return <p>Missing children</p>;
  }

  return (
    <div className={className}>
      <FeedbackFarm projectId="project_id">{children}</FeedbackFarm>
    </div>
  );
}

export { FeedbackWrapper };
