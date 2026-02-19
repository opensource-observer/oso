"use client";

import {
  useState,
  useEffect,
  useCallback,
  useTransition,
  Suspense,
} from "react";
import {
  useApolloClient,
  useMutation,
  useSuspenseQuery,
} from "@apollo/client/react";
import { toast } from "sonner";
import { Search, Database, Clock, Table2, RefreshCw, X } from "lucide-react";
import {
  MARKETPLACE_DATASETS,
  SUBSCRIBE_TO_DATASET,
  UNSUBSCRIBE_FROM_DATASET,
} from "@/app/beta/[orgName]/marketplace/_graphql/queries";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { DatasetType } from "@/lib/graphql/generated/graphql";
import { MarketplaceSkeleton } from "@/app/beta/[orgName]/marketplace/_components/marketplace-skeleton";

const DATASET_TYPE_LABELS: Record<string, string> = {
  USER_MODEL: "Model",
  STATIC_MODEL: "Static",
  DATA_INGESTION: "Ingestion",
  DATA_CONNECTION: "Connection",
};

export const PAGE_SIZE = 25;

interface MarketplaceDataGridProps {
  orgId: string;
  debouncedSearch: string;
  typeFilter: string;
  afterCursor: string | null;
  setAfterCursor: (cursor: string | null) => void;
}

function MarketplaceDataGrid({
  orgId,
  debouncedSearch,
  typeFilter,
  afterCursor,
  setAfterCursor,
}: MarketplaceDataGridProps) {
  // Fetch marketplace datasets - reads from preloaded cache on first render
  const { data, refetch } = useSuspenseQuery(MARKETPLACE_DATASETS, {
    variables: {
      first: PAGE_SIZE,
      after: afterCursor,
      search: debouncedSearch || undefined,
      datasetType:
        typeFilter !== "all" ? (typeFilter as DatasetType) : undefined,
      orgId,
    },
  });

  const [subscribe, { loading: subscribing }] = useMutation(
    SUBSCRIBE_TO_DATASET,
    {
      refetchQueries: [MARKETPLACE_DATASETS],
    },
  );
  const [unsubscribe, { loading: unsubscribing }] = useMutation(
    UNSUBSCRIBE_FROM_DATASET,
    {
      refetchQueries: [MARKETPLACE_DATASETS],
    },
  );

  const handleSubscribe = useCallback(
    async (datasetId: string) => {
      try {
        await subscribe({
          variables: { input: { datasetId, orgId } },
        });
        toast.success("Subscribed to dataset");
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Failed to subscribe");
      }
    },
    [orgId, subscribe, refetch],
  );

  const handleUnsubscribe = useCallback(
    async (datasetId: string) => {
      try {
        await unsubscribe({
          variables: { input: { datasetId, orgId } },
        });
        toast.success("Unsubscribed from dataset");
      } catch (err) {
        toast.error(
          err instanceof Error ? err.message : "Failed to unsubscribe",
        );
      }
    },
    [orgId, unsubscribe, refetch],
  );

  const connection = data?.marketplaceDatasets;
  const datasets = connection?.edges ?? [];
  const pageInfo = connection?.pageInfo;
  const totalCount = connection?.totalCount ?? 0;

  return (
    <>
      {/* Results count */}
      <p className="text-sm text-muted-foreground mb-4">
        {totalCount} {totalCount === 1 ? "dataset" : "datasets"} found
      </p>

      {/* Dataset cards */}
      {datasets.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Database className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">No datasets found</h3>
          <p className="text-muted-foreground mt-1">
            {debouncedSearch || typeFilter !== "all"
              ? "Try adjusting your search or filters."
              : "No public datasets are available yet."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map(({ node: dataset, cursor }) => (
            <Card key={cursor} className="flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Badge variant="secondary">
                    {DATASET_TYPE_LABELS[dataset.type] ?? dataset.type}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {dataset.organization.displayName ??
                      dataset.organization.name}
                  </span>
                </div>
                <h3 className="font-semibold text-base mt-2 leading-tight">
                  {dataset.displayName ?? dataset.name}
                </h3>
                <p className="text-xs text-muted-foreground font-mono mt-1 min-h-[1rem]">
                  {dataset.name}
                </p>
              </CardHeader>
              <CardContent className="flex-1 pb-3">
                {dataset.description ? (
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {dataset.description}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground italic">
                    No description
                  </p>
                )}
                <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Table2 className="h-3.5 w-3.5" />
                    {dataset.tables?.totalCount ?? 0}{" "}
                    {dataset.tables?.totalCount === 1 ? "table" : "tables"}
                  </span>
                  {dataset.updatedAt && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      {new Date(dataset.updatedAt).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </CardContent>
              <CardFooter className="pt-0">
                {dataset.isSubscribed ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    disabled={unsubscribing}
                    onClick={() => void handleUnsubscribe(dataset.id)}
                  >
                    {unsubscribing ? "Unsubscribing..." : "Unsubscribe"}
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className="w-full"
                    disabled={subscribing}
                    onClick={() => void handleSubscribe(dataset.id)}
                  >
                    {subscribing ? "Subscribing..." : "Subscribe"}
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {(pageInfo?.hasNextPage || afterCursor) && (
        <div className="flex justify-center gap-4 mt-8">
          {afterCursor && (
            <Button variant="outline" onClick={() => setAfterCursor(null)}>
              First page
            </Button>
          )}
          {pageInfo?.hasNextPage && pageInfo?.endCursor && (
            <Button
              variant="outline"
              onClick={() => setAfterCursor(pageInfo.endCursor!)}
            >
              Next page
            </Button>
          )}
        </div>
      )}
    </>
  );
}

interface MarketplaceContentProps {
  orgId: string;
}

export function MarketplaceContent({ orgId }: MarketplaceContentProps) {
  const client = useApolloClient();
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [afterCursor, setAfterCursor] = useState<string | null>(null);
  const [_, startTransition] = useTransition();

  // Debounce search input with transition
  useEffect(() => {
    const timer = setTimeout(() => {
      startTransition(() => {
        setDebouncedSearch(searchInput);
        setAfterCursor(null);
      });
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const handleRefresh = useCallback(() => {
    client
      .refetchQueries({
        include: [MARKETPLACE_DATASETS],
      })
      .then(() => {
        toast.success("Marketplace data refreshed");
      })
      .catch((err) => {
        toast.error(
          err instanceof Error ? err.message : "Failed to refresh data",
        );
      });
  }, [client]);

  const handleClearSearch = useCallback(() => {
    setSearchInput("");
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Data Marketplace</h1>
        <p className="text-muted-foreground mt-1">
          Browse and subscribe to public datasets for your organization.
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-8">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search datasets or organizations..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9 pr-9"
          />
          {searchInput && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Select
          value={typeFilter}
          onValueChange={(value) => {
            setTypeFilter(value);
            setAfterCursor(null);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {Object.entries(DATASET_TYPE_LABELS).map(([key, label]) => (
              <SelectItem key={key} value={key}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="icon"
          onClick={handleRefresh}
          aria-label="Refresh marketplace data"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <Suspense fallback={<MarketplaceSkeleton />}>
        <MarketplaceDataGrid
          orgId={orgId}
          debouncedSearch={debouncedSearch}
          typeFilter={typeFilter}
          afterCursor={afterCursor}
          setAfterCursor={setAfterCursor}
        />
      </Suspense>
    </div>
  );
}
