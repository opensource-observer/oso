"use client";

import "instantsearch.css/themes/algolia.css";
import algoliasearch from "algoliasearch/lite";
import React, { ReactElement } from "react";
import { SearchBox, useHits } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";
import { DataProvider } from "@plasmicapp/loader-nextjs";
import {
  ALGOLIA_APPLICATION_ID,
  ALGOLIA_API_KEY,
  ALGOLIA_INDEX,
} from "../../lib/config";

const searchClient = algoliasearch(ALGOLIA_APPLICATION_ID, ALGOLIA_API_KEY);
const PLASMIC_KEY = "searchItem";

type AlgoliaSearchListProps = {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this per item
  indexName?: string; // Choose a custom Algolia index
  showResultsOnEmptyQuery?: boolean; // Show some results even if no query
};

function HitsContainer(props: AlgoliaSearchListProps) {
  const { children } = props;
  const { hits, results } = useHits();
  //console.log(hits);

  return (
    <div>
      {results?.query &&
        hits.map((hit) => (
          <div key={hit.objectID}>
            <DataProvider name={PLASMIC_KEY} data={hit}>
              {children}
            </DataProvider>
          </div>
        ))}
    </div>
  );
}

/**
 * Infinite scroll list for Algolia search
 */
function AlgoliaSearchList(props: AlgoliaSearchListProps) {
  const {
    className,
    //children: rawChildren,
    indexName: rawIndexName,
    //showResultsOnEmptyQuery,
  } = props;
  //const children = rawChildren ?? <SearchIcon />;
  const indexName = rawIndexName ?? ALGOLIA_INDEX;

  return (
    <div className={className}>
      <InstantSearchNext
        searchClient={searchClient}
        indexName={indexName}
        insights
      >
        <SearchBox placeholder={"Search projects..."} autoFocus={true} />
        <HitsContainer {...props} />
      </InstantSearchNext>
    </div>
  );
}

export { AlgoliaSearchList };
