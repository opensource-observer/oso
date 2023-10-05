import _ from "lodash";

type Addressable = number | string;

export class UniqueArray<T> {
  private uniqueMap: { [key: Addressable]: boolean };
  private arr: T[];
  private idFunc: (value: T) => Addressable;

  constructor(idFunc: (value: T) => Addressable) {
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

  pop(): T | undefined {
    const obj = this.arr.pop();
    if (obj) {
      const id = this.idFunc(obj);
      delete this.uniqueMap[id];
    }
    return obj;
  }

  items(): T[] {
    return _.cloneDeep(this.arr);
  }

  get length() {
    return this.arr.length;
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
  const results: R[] = [];
  for (const item of arr) {
    batch.push(item);

    if (batch.length >= batchSize) {
      const batchResult = await cb(batch, batch.length, batchNumber);
      results.push(batchResult);
      batchNumber += 1;
      batch = [];
    }
  }
  if (batch.length > 0) {
    const batchResult = await cb(batch, batch.length, batchNumber);
    results.push(batchResult);
    batch = [];
  }
  return results;
}
