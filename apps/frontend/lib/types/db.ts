/**
 * Regardless of the data query, this will be the intermediate
 * format we need to normalize against before we put it into the
 * data formatters (for charts)
 **/
type EventData = {
  typeName: string;
  id: string;
  date: string;
  amount: number;
};

/**
 * Abstract entity data that could come from either an `Artifact` or `Project`
 */
type EntityData = {
  id: string;
  name: string;
};

export type { EventData, EntityData };
