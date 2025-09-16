/**
 * Regardless of the data query, this will be the intermediate
 * format we need to normalize against before we put it into the
 * data formatters (for charts)
 **/
type EventData = {
  metricId: string;
  metricName: string;
  entityId: string;
  entityName: string;
  date: string;
  amount: number;
};

type NotebookKey = { orgName: string; notebookName: string };

export type { EventData, NotebookKey };
