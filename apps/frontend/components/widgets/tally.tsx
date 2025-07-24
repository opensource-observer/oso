import React, { ReactElement } from "react";
import Script from "next/script";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

type TallyLayout = "modal" | undefined;
type TallyEmojiAnimation =
  | "none"
  | "wave"
  | "tada"
  | "heart-beat"
  | "spin"
  | "flash"
  | "bounce"
  | "rubber-band"
  | "head-shake"
  | undefined;

export type TallyPopupProps = {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this
  formId?: string; // Tally form ID
  layout?: TallyLayout; // Tally layout type
  width?: string; // Width of the Tally form
  emoji?: string; // Emoji to use in the Tally form
  emojiAnimation?: TallyEmojiAnimation; // Enable emoji animation
};

const TallyPopupMeta: CodeComponentMeta<TallyPopupProps> = {
  name: "TallyPopup",
  description: "Tally.so popup form",
  props: {
    children: "slot",
    formId: {
      type: "string",
      helpText: "Tally form ID",
      required: true,
    },
    layout: {
      type: "choice",
      options: ["modal"],
    },
    width: {
      type: "string",
      helpText: "Width of the Tally form in pixels (e.g. '600')",
    },
    emoji: {
      type: "string",
      helpText: "Emoji to use in the Tally form (e.g. '👋')",
    },
    emojiAnimation: {
      type: "choice",
      options: [
        "none",
        "wave",
        "tada",
        "heart-beat",
        "spin",
        "flash",
        "bounce",
        "rubber-band",
        "head-shake",
      ],
      helpText: "Enable emoji animation",
    },
  },
};

function TallyPopup(props: TallyPopupProps) {
  const { className, children, formId, layout, width, emoji, emojiAnimation } =
    props;

  if (!formId) {
    return <p>Missing formId</p>;
  } else if (!children) {
    return <p>Missing children</p>;
  }

  const link =
    `#tally-open=${formId}` +
    (layout ? `&tally-layout=${layout}` : "") +
    (width ? `&tally-width=${width}` : "") +
    (emoji ? `&tally-emoji-text=${emoji}` : "") +
    (emojiAnimation ? `&tally-emoji-animation=${emojiAnimation}` : "");

  return (
    <>
      <Script async src="https://tally.so/widgets/embed.js" />
      <div className={className}>
        <a href={link}>{children}</a>
      </div>
    </>
  );
}

export { TallyPopup, TallyPopupMeta };
