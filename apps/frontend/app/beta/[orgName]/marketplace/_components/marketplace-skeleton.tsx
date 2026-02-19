import { Skeleton } from "@/components/ui/skeleton";

export function MarketplaceSkeleton() {
  return (
    <>
      {/* Results count skeleton */}
      <Skeleton className="h-5 w-32 mb-4" />

      {/* Dataset cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-6 space-y-4">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-5 w-24" />
            </div>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <div className="flex items-center justify-between pt-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-9 w-28" />
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
