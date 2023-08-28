import _ from "lodash";

export class UniqueArray<T> {
  private uniqueMap: { [key: string]: boolean };
  private arr: T[];
  private idFunc: (value: T) => string;

  constructor(idFunc: (value: T) => string) {
    this.uniqueMap = {};
    this.arr = [];
    this.idFunc = idFunc;
  }

  push(obj: T) {
    const id = this.idFunc(obj);
    if (this.uniqueMap[id] !== undefined) {
      return this.arr.length;
    }
    this.uniqueMap[id] = true;
    this.arr.push(obj);
  }

  items(): T[] {
    return _.cloneDeep(this.arr);
  }
}

/**
 * asyncBatch creates batches of a given array for processing. This function
 * awaits the callback for every batch.
 *
 * @param arr - The array to process in batches
 * @param batchSize - The batch size
 * @param cb - The async callback
 * @returns
 */
export async function asyncBatch<T, R>(
  arr: T[],
  batchSize: number,
  cb: (batch: T[], batchLength: number, batchNumber: number) => Promise<R>,
): Promise<R[]> {
  let batch = [];
  let batchNumber = 0;
  const results = [];
  for (const item of arr) {
    batch.push(item);

    if (batch.length >= batchSize) {
      results.push(await cb(batch, batch.length, batchNumber));
      batchNumber += 1;
      batch = [];
    }
  }
  if (batch.length > 0) {
    results.push(await cb(batch, batch.length, batchNumber));
    batch = [];
  }
  return results;
}
