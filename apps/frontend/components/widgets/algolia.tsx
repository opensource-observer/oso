"use client";

import "instantsearch.css/themes/algolia.css";
import algoliasearch from "algoliasearch/lite";
import React, { ReactElement, useEffect, useRef } from "react";
import { SearchBox, useInfiniteHits } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";
import { DataProvider } from "@plasmicapp/loader-nextjs";
import {
  ALGOLIA_APPLICATION_ID,
  ALGOLIA_API_KEY,
  ALGOLIA_INDEX,
} from "../../lib/config";

const searchClient = algoliasearch(ALGOLIA_APPLICATION_ID, ALGOLIA_API_KEY);
const PLASMIC_KEY = "searchItem";
const DEFAULT_PLACEHOLDER = "Search...";

type AlgoliaSearchListProps = {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this per item
  indexName?: string; // Choose a custom Algolia index
  placeholder?: string; // Placeholder for search box
  showResultsOnEmptyQuery?: boolean; // Show some results even if no query
};

function HitsContainer(props: AlgoliaSearchListProps) {
  const { children, showResultsOnEmptyQuery } = props;
  const { results, items, isLastPage, showMore } = useInfiniteHits();
  const sentinelRef = useRef(null);
  //console.log(results);

  useEffect(() => {
    if (sentinelRef.current !== null) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !isLastPage) {
            showMore();
          }
        });
      });
      observer.observe(sentinelRef.current);
      return () => {
        observer.disconnect();
      };
    }
  }, [isLastPage, showMore]);

  return (
    <div>
      {(showResultsOnEmptyQuery || results?.query) &&
        items.map((hit) => (
          <div key={hit.objectID}>
            <DataProvider name={PLASMIC_KEY} data={hit}>
              {children}
            </DataProvider>
          </div>
        ))}
      <div
        ref={sentinelRef}
        tabIndex={0}
        aria-hidden="true"
        style={{
          width: "0px",
          height: "0px",
          overflow: "hidden",
          outline: "none",
        }}
      ></div>
    </div>
  );
}

/**
 * Infinite scroll list for Algolia search
 */
function AlgoliaSearchList(props: AlgoliaSearchListProps) {
  const {
    className,
    indexName: rawIndexName,
    placeholder: rawPlaceholder,
  } = props;
  const indexName = rawIndexName ?? ALGOLIA_INDEX;
  const placeholder = rawPlaceholder ?? DEFAULT_PLACEHOLDER;

  return (
    <div className={className}>
      <InstantSearchNext
        searchClient={searchClient}
        indexName={indexName}
        insights
        future={{
          preserveSharedStateOnUnmount: true,
        }}
      >
        <SearchBox placeholder={placeholder} autoFocus={true} />
        <HitsContainer {...props} />
      </InstantSearchNext>
    </div>
  );
}

//export { AlgoliaSearchList };
export default AlgoliaSearchList;
