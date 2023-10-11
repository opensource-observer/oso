import algoliasearch from "algoliasearch/lite";
import {
  InstantSearch,
  SearchBox,
  Hits,
  Pagination,
} from "react-instantsearch";
import {
  ALGOLIA_APPLICATION_ID,
  ALGOLIA_API_KEY,
  ALGOLIA_INDEX,
} from "../../lib/config";

const searchClient = algoliasearch(ALGOLIA_APPLICATION_ID, ALGOLIA_API_KEY);

function AlgoliaSearchBox() {
  return (
    <InstantSearch
      searchClient={searchClient}
      indexName={ALGOLIA_INDEX}
      insights
    >
      <SearchBox />
      <Hits />
      <Pagination />
    </InstantSearch>
  );
}

export { AlgoliaSearchBox };
