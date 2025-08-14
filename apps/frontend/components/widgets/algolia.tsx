"use client";

import "instantsearch.css/themes/algolia.css";
import { liteClient } from "algoliasearch/lite";
import React, { ReactElement, useEffect, useRef } from "react";
import { Index, SearchBox, useInfiniteHits } from "react-instantsearch";
import { InstantSearchNext } from "react-instantsearch-nextjs";
import { CodeComponentMeta, DataProvider } from "@plasmicapp/loader-nextjs";
import {
  ALGOLIA_APPLICATION_ID,
  ALGOLIA_API_KEY,
  ALGOLIA_INDEX,
} from "@/lib/config";

const searchClient = liteClient(ALGOLIA_APPLICATION_ID, ALGOLIA_API_KEY);
const PLASMIC_KEY = "searchItem";
const DEFAULT_PLACEHOLDER = "Search...";
const DEFAULT_INDEX = "projects";
const INDEX_DELIMITER = ",";

type AlgoliaSearchListProps = {
  className?: string; // Plasmic CSS class
  children?: ReactElement; // Show this per item
  indexName?: string; // Choose a custom Algolia index
  placeholder?: string; // Placeholder for search box
  defaultSearchResults?: any; // Show some results even if no query
};

const AlgoliaSearchListMeta: CodeComponentMeta<AlgoliaSearchListProps> = {
  name: "AlgoliaSearchList",
  description: "Algolia-powered search list",
  props: {
    children: "slot",
    indexName: {
      type: "string",
      defaultValue: ALGOLIA_INDEX,
      helpText: "Comma-separated Algolia index names",
    },
    placeholder: "string",
    defaultSearchResults: "object",
  },
  providesData: true,
};

function HitsContainer(props: AlgoliaSearchListProps) {
  const { children, defaultSearchResults } = props;
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

  const isResultsReady = results?.query || Array.isArray(defaultSearchResults);
  const displayItems = results?.query ? items : defaultSearchResults;

  return (
    <div>
      {isResultsReady &&
        displayItems.map((hit: any, i: number) => (
          <div key={hit.objectID ?? i}>
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
  const indices = (rawIndexName ?? ALGOLIA_INDEX).split(INDEX_DELIMITER);
  const rootIndex = indices.length > 0 ? indices[0] : DEFAULT_INDEX;
  const placeholder = rawPlaceholder ?? DEFAULT_PLACEHOLDER;

  return (
    <div className={className}>
      <InstantSearchNext
        searchClient={searchClient}
        indexName={rootIndex}
        insights
        future={{
          preserveSharedStateOnUnmount: true,
        }}
      >
        <SearchBox placeholder={placeholder} autoFocus={true} />
        {indices.map((i) => (
          <Index key={i} indexName={i}>
            <HitsContainer {...props} />
          </Index>
        ))}
      </InstantSearchNext>
    </div>
  );
}

export { AlgoliaSearchListMeta, AlgoliaSearchList };
export default AlgoliaSearchList;
