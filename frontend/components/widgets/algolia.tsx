"use client";

import "instantsearch.css/themes/algolia.css";
import algoliasearch from "algoliasearch/lite";
import Link from "next/link";
import path from "path";
import React from "react";
import { SearchBox, Highlight, useHits } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";
import Box from "@mui/material/Box";
import Popover from "@mui/material/Popover";
import Stack from "@mui/material/Stack";
import {
  ALGOLIA_APPLICATION_ID,
  ALGOLIA_API_KEY,
  ALGOLIA_INDEX,
} from "../../lib/config";

const PROJECT_PREFIX = "/project/";
const searchClient = algoliasearch(ALGOLIA_APPLICATION_ID, ALGOLIA_API_KEY);

type HitProps = {
  hit: any;
};

function Hit({ hit }: HitProps) {
  return (
    <Link href={path.join(PROJECT_PREFIX, hit.slug)}>
      <article
        style={{
          width: "100%",
          textAlign: "center",
          padding: "1rem",
        }}
      >
        <h2>
          <Highlight attribute="name" hit={hit} />
        </h2>
      </article>
    </Link>
  );
}

type HitsContainerProps = {
  onClose: () => void;
};

function HitsContainer(props: HitsContainerProps) {
  const { onClose } = props;
  const { hits, results } = useHits();

  if (!results?.query || !hits || hits.length < 1) {
    onClose();
  }
  //console.log(hits);

  return (
    <Box sx={{ width: "100%" }}>
      <Stack spacing={0}>
        {hits.map((hit) => (
          <Hit key={hit.objectID} hit={hit} />
        ))}
      </Stack>
    </Box>
  );
}

function AlgoliaSearchBox() {
  const [anchorEl, setAnchorEl] = React.useState<HTMLFormElement | null>(null);
  const open = Boolean(anchorEl);
  const onClose = () => setAnchorEl(null);
  return (
    <InstantSearchNext
      searchClient={searchClient}
      indexName={ALGOLIA_INDEX}
      insights
    >
      <SearchBox
        placeholder={"Search projects..."}
        onSubmit={(event) => {
          event.preventDefault();
          setAnchorEl(event.currentTarget);
        }}
      />
      <Popover
        id={"search-popover"}
        sx={{
          minWidth: "500px",
        }}
        open={open}
        anchorEl={anchorEl}
        onClose={onClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
      >
        <HitsContainer onClose={onClose} />
      </Popover>
    </InstantSearchNext>
  );
}

export default AlgoliaSearchBox;
