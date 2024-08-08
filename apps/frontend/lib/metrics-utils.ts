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
}

interface CardSummary {
  title: string;
  subtitle: string;
  value: string;
}

/**
 * Convenience function that summarizes metrics for card rendering
 */
function summarizeForCards(
  metrics: Record<string, string>[],
  cards: CardSummaryOptions[],
): CardSummary[] {
  return cards.map((card) => {
    const value = card.operation(metrics, card.column);
    return {
      title: card.title,
      subtitle: card.subtitle,
      value: value,
    };
  });
}

export const register = groupRegistrations(
  registerFunction(summarizeForCards, {
    name: "summarizeForCards",
    namespace: "metrics",
    description: "summarizes a collection of metrics for card rendering",
    importPath: "./lib/metrics-utils",
    isDefaultExport: false,
    params: [
      {
        name: "metrics",
        type: "any",
        description: "The metrics object",
      },
      {
        name: "cards",
        type: "any",
        description: "The definitions for the cards you wish to display",
      },
    ],
    returnValue: {
      type: "array",
      description: "an array of cards {title, subtitle, value}",
    },
  }),
);
