import React from "react";
import PropTypes from "prop-types";
import clsx from "clsx";

const CardBody = ({
  className, // classNamees for the container card
  style, // Custom styles for the container card
  children, // Content to be included within the card
  textAlign,
  variant,
  italic = false,
  noDecoration = false,
  transform,
  breakWord = false,
  truncate = false,
  weight,
}) => {
  const text = textAlign ? `text--${textAlign}` : "";
  const textColor = variant ? `text--${variant}` : "";
  const textItalic = italic ? "text--italic" : "";
  const textDecoration = noDecoration ? "text-no-decoration" : "";
  const textType = transform ? `text--${transform}` : "";
  const textBreak = breakWord ? "text--break" : "";
  const textTruncate = truncate ? "text--truncate" : "";
  const textWeight = weight ? `text--${weight}` : "";
  return (
    <div
      className={clsx(
        "card__body",
        className,
        text,
        textType,
        textColor,
        textItalic,
        textDecoration,
        textBreak,
        textTruncate,
        textWeight,
      )}
      style={style}
    >
      {children}
    </div>
  );
};

CardBody.propTypes = {
  className: PropTypes.string,
  style: PropTypes.object,
  children: PropTypes.node,
  textAlign: PropTypes.oneOf(["left", "right", "center", "justify"]),
  variant: PropTypes.string,
  italic: PropTypes.bool,
  noDecoration: PropTypes.bool,
  transform: PropTypes.oneOf(["uppercase", "lowercase", "capitalize"]),
  breakWord: PropTypes.bool,
  truncate: PropTypes.bool,
  weight: PropTypes.oneOf(["bold", "semibold", "normal", "light"]),
};

export default CardBody;
