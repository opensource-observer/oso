/**
 * Explicitly signals that a code path that has not been implemented yet.
 */
export class NotImplementedError extends Error {
  constructor(msg = "Not implemented") {
    super(msg);
  }
}

export class AssertionError extends Error {}
export class HttpError extends Error {}
export class MissingDataError extends Error {}
export class NullOrUndefinedValueError extends Error {}
export class UserInputError extends Error {}
