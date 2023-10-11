"use client";

import "instantsearch.css/themes/algolia.css";
import algoliasearch from "algoliasearch/lite";
import { SearchBox, Hits } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";
import {
  ALGOLIA_APPLICATION_ID,
  ALGOLIA_API_KEY,
  ALGOLIA_INDEX,
} from "../../lib/config";

const searchClient = algoliasearch(ALGOLIA_APPLICATION_ID, ALGOLIA_API_KEY);

function AlgoliaSearchBox() {
  return (
    <InstantSearchNext
      searchClient={searchClient}
      indexName={ALGOLIA_INDEX}
      insights
    >
      <SearchBox />
      <Hits />
    </InstantSearchNext>
  );
}

export { AlgoliaSearchBox };
