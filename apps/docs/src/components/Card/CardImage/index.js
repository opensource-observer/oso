import React from "react";
import PropTypes from "prop-types";
import clsx from "clsx";
import useBaseUrl from "@docusaurus/useBaseUrl"; // Import the useBaseUrl function from Docusaurus

const CardImage = ({ className, style, cardImageUrl, alt, title }) => {
  const generatedCardImageUrl = useBaseUrl(cardImageUrl);
  return (
    <img
      className={clsx("card__image", className)}
      style={style}
      src={generatedCardImageUrl}
      alt={alt}
      title={title}
    />
  );
};

CardImage.propTypes = {
  className: PropTypes.string,
  style: PropTypes.object,
  cardImageUrl: PropTypes.string.isRequired,
  alt: PropTypes.string,
  title: PropTypes.string,
};

export default CardImage;
