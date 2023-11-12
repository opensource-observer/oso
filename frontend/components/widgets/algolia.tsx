"use client";

import "instantsearch.css/themes/algolia.css";
import algoliasearch from "algoliasearch/lite";
import Link from "next/link";
import path from "path";
import React from "react";
import { SearchBox, Highlight, useHits } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";
import SearchIcon from "@mui/icons-material/Search";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Modal from "@mui/material/Modal";
import Paper from "@mui/material/Paper";
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
    <Link
      href={path.join(PROJECT_PREFIX, hit.slug)}
      style={{
        width: "100%",
      }}
    >
      <ListItem
        style={{
          width: "100%",
          textAlign: "center",
          padding: "1rem",
        }}
      >
        <ListItemText>
          <Highlight attribute="name" hit={hit} />
        </ListItemText>
      </ListItem>
    </Link>
  );
}

function HitsContainer() {
  const { hits, results } = useHits();
  //console.log(hits);

  return (
    <List sx={{ width: "100%" }}>
      {results?.query &&
        hits.map((hit) => <Hit key={hit.objectID} hit={hit} />)}
    </List>
  );
}

function AlgoliaSearchBox() {
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  return (
    <div>
      <button onClick={handleOpen}>
        <SearchIcon />
      </button>
      <Modal open={open} onClose={handleClose}>
        <Paper
          elevation={4}
          sx={{
            width: "50%",
            height: "70%",
            padding: "8px",
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            bgcolor: "background.paper",
            overflow: "auto",
          }}
        >
          <InstantSearchNext
            searchClient={searchClient}
            indexName={ALGOLIA_INDEX}
            insights
          >
            <SearchBox placeholder={"Search projects..."} autoFocus={true} />
            <HitsContainer />
          </InstantSearchNext>
        </Paper>
      </Modal>
    </div>
  );
}

export default AlgoliaSearchBox;
