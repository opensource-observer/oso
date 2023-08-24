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
