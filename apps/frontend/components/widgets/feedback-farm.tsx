import React, { ReactElement } from "react";
import { FeedbackFarm } from "@feedbackfarm/react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { FEEDBACK_FARM_ID } from "@/lib/config";

export type FeedbackWrapperProps = {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this
};

const FeedbackWrapperMeta: CodeComponentMeta<FeedbackWrapperProps> = {
  name: "FeedbackWrapper",
  description: "Feedback Farm click handler",
  props: {
    children: "slot",
  },
};

function FeedbackWrapper(props: FeedbackWrapperProps) {
  const { className, children } = props;

  if (!children) {
    return <p>Missing children</p>;
  }

  return (
    <div className={className}>
      <FeedbackFarm projectId={FEEDBACK_FARM_ID}>{children}</FeedbackFarm>
    </div>
  );
}

export { FeedbackWrapper, FeedbackWrapperMeta };
