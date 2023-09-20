import { DateTime } from "luxon";
import {
  findMissingRanges,
  Range,
  removeOverlappingRanges,
  doRangesIntersect,
  rangesEqual,
  rangeFromISO,
} from "./ranges.js";

describe("findMissingRanges", () => {
  it("should find missing ranges correctly", () => {
    const ranges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T04:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T10:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T11:00:00"),
      },
    ];

    const startDate: DateTime = DateTime.fromISO("2023-01-01T00:00:00");
    const endDate: DateTime = DateTime.fromISO("2023-01-01T12:00:00");

    const missingRanges: Range[] = findMissingRanges(
      startDate,
      endDate,
      ranges,
    );

    expect(missingRanges).toEqual([
      {
        startDate: DateTime.fromISO("2023-01-01T04:00:00"),
        endDate: DateTime.fromISO("2023-01-01T08:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T11:00:00"),
        endDate: DateTime.fromISO("2023-01-01T12:00:00"),
      },
    ]);
  });

  it("should find missing ranges correctly if ranges are out of order", () => {
    const ranges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T10:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T11:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T04:00:00"),
      },
    ];

    const startDate: DateTime = DateTime.fromISO("2023-01-01T00:00:00");
    const endDate: DateTime = DateTime.fromISO("2023-01-01T12:00:00");

    const missingRanges: Range[] = findMissingRanges(
      startDate,
      endDate,
      ranges,
    );

    expect(missingRanges).toEqual([
      {
        startDate: DateTime.fromISO("2023-01-01T04:00:00"),
        endDate: DateTime.fromISO("2023-01-01T08:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T11:00:00"),
        endDate: DateTime.fromISO("2023-01-01T12:00:00"),
      },
    ]);
  });

  it("should handle no missing ranges", () => {
    const ranges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T04:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T04:00:00"),
        endDate: DateTime.fromISO("2023-01-01T12:00:00"),
      },
    ];

    const beginDate: DateTime = DateTime.fromISO("2023-01-01T00:00:00");
    const endDate: DateTime = DateTime.fromISO("2023-01-01T12:00:00");

    const missingRanges: Range[] = findMissingRanges(
      beginDate,
      endDate,
      ranges,
    );

    expect(missingRanges).toEqual([]);
  });
});

describe("removeOverlappingRanges", () => {
  it("should remove overlapping ranges and choose the largest range", () => {
    const inputRanges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T04:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T03:00:00"),
        endDate: DateTime.fromISO("2023-01-01T07:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T10:00:00"),
      },
    ];

    const expectedRanges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T04:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T10:00:00"),
      },
    ];

    const nonOverlappingRanges: Range[] = removeOverlappingRanges(inputRanges);

    expect(nonOverlappingRanges).toEqual(expectedRanges);
  });

  it("should handle non-overlapping ranges", () => {
    const inputRanges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T02:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T03:00:00"),
        endDate: DateTime.fromISO("2023-01-01T05:00:00"),
      },
      {
        startDate: DateTime.fromISO("2023-01-01T08:00:00"),
        endDate: DateTime.fromISO("2023-01-01T10:00:00"),
      },
    ];

    const expectedRanges: Range[] = [...inputRanges];

    const nonOverlappingRanges: Range[] = removeOverlappingRanges(inputRanges);

    expect(nonOverlappingRanges).toEqual(expectedRanges);
  });

  it("should handle empty input", () => {
    const inputRanges: Range[] = [];

    const expectedRanges: Range[] = [];

    const nonOverlappingRanges: Range[] = removeOverlappingRanges(inputRanges);

    expect(nonOverlappingRanges).toEqual(expectedRanges);
  });

  it("should handle single range", () => {
    const inputRanges: Range[] = [
      {
        startDate: DateTime.fromISO("2023-01-01T00:00:00"),
        endDate: DateTime.fromISO("2023-01-01T04:00:00"),
      },
    ];

    const expectedRanges: Range[] = [...inputRanges];

    const nonOverlappingRanges: Range[] = removeOverlappingRanges(inputRanges);

    expect(nonOverlappingRanges).toEqual(expectedRanges);
  });
});

describe("doRangesIntersect", () => {
  it("should return true for intersecting ranges", () => {
    const range1: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T04:00:00"),
    };

    const range2: Range = {
      startDate: DateTime.fromISO("2023-01-01T03:00:00"),
      endDate: DateTime.fromISO("2023-01-01T07:00:00"),
    };

    const intersect = doRangesIntersect(range1, range2);

    expect(intersect).toBe(true);
  });

  it("should return true for ranges that are equal", () => {
    const range1: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-02T00:00:00"),
    };

    const range2: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-02T00:00:00"),
    };

    const intersect = doRangesIntersect(range1, range2);

    expect(intersect).toBe(true);
  });

  it("should return false for non-intersecting ranges", () => {
    const range1: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T04:00:00"),
    };

    const range2: Range = {
      startDate: DateTime.fromISO("2023-01-01T04:00:00"),
      endDate: DateTime.fromISO("2023-01-01T07:00:00"),
    };

    const intersect = doRangesIntersect(range1, range2);

    expect(intersect).toBe(false);
  });

  it("should return true for partially overlapping ranges", () => {
    const range1: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T04:00:00"),
    };

    const range2: Range = {
      startDate: DateTime.fromISO("2023-01-01T03:00:00"),
      endDate: DateTime.fromISO("2023-01-01T05:00:00"),
    };

    const intersect = doRangesIntersect(range1, range2);

    expect(intersect).toBe(true);
  });

  it("should throw errors for invalid ranges", () => {
    const range1: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T00:00:00"),
    };

    const range2: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T00:00:00"),
    };

    expect(() => {
      doRangesIntersect(range1, range2);
    }).toThrowError();
  });
});

describe("rangesEqual", () => {
  it("should return true for equal ranges", () => {
    const range1: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T04:00:00"),
    };

    const range2: Range = {
      startDate: DateTime.fromISO("2023-01-01T00:00:00"),
      endDate: DateTime.fromISO("2023-01-01T04:00:00"),
    };

    const equal = rangesEqual(range1, range2);

    expect(equal).toBe(true);
  });

  it("should return true for equal ranges with different timezones", () => {
    const range1 = rangeFromISO("2023-01-01T00:00:00Z", "2023-01-02T00:00:00");

    const range2 = rangeFromISO(
      "2023-01-01T00:00:00Z",
      "2023-01-01T16:00:00-08:00",
    );

    const equal = rangesEqual(range1, range2);

    expect(equal).toBe(true);
  });
});
