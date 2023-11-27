import { AsyncResults } from "../utils/async-results.js";
import {
  ICommitResult,
  RecordHandle,
  RecordResponse,
  RecorderError,
} from "./types.js";
import _ from "lodash";

export class CommitResult implements ICommitResult {
  committed: string[];
  skipped: string[];
  invalid: string[];
  errors: unknown[];

  constructor() {
    this.committed = [];
    this.skipped = [];
    this.invalid = [];
    this.errors = [];
  }

  collectResultsForHandles(
    handles: RecordHandle[],
  ): AsyncResults<RecordResponse> {
    const handleIds = handles.map((h) => h.id);

    const committed = _.intersection(this.committed, handleIds);
    const skipped = _.intersection(this.skipped, handleIds);
    const invalid = _.intersection(this.invalid, handleIds);
    const missing = _.difference(
      handleIds,
      _.union(committed, skipped, invalid),
    );

    const results: AsyncResults<RecordResponse> = {
      success: _.union(committed, skipped),
      errors: [],
    };

    invalid.forEach((i) => {
      results.errors.push(new RecorderError(`invalid input for ${i}`));
    });
    missing.forEach((m) => {
      results.errors.push(new RecorderError(`missing result for ${m}`));
    });
    return results;
  }
}
