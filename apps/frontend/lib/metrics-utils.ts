/**
 * Various utilities for using metrics on the frontend
 */
import { groupRegistrations, registerFunction } from "./plasmic-register";

type ColumnReferenceFunc = (...args: any) => any;
type ColumnReference = ColumnReferenceFunc | string;
type MetricsTransformFunc = (
  metrics: Iterable<any>,
  column: ColumnReference,
) => any;

interface CardSummaryOptions {
  title: string;
  subtitle: string;
  operation: MetricsTransformFunc;
  column: ColumnReferenceFunc | string;
  value?: any;
}

/**
 * Convenience function that summarizes metrics for card rendering
 */
function summarizeForCards(
  metrics: Record<string, string>[],
  cards: CardSummaryOptions[],
) {
  return cards.map((card) => {
    card["value"] = card.operation(metrics, card.column);
    return card;
  });
}

export const register = groupRegistrations(
  registerFunction(summarizeForCards, {
    name: "summarizeForCards",
    namespace: "metrics",
    description: "summarizes a collection of metrics for card rendering",
  }),
);
