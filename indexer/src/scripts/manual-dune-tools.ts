// Currently just a test file but if it gets committed that wasn't intentional
// but is also just fine
import { parse } from "csv";
import fs, { WriteStream } from "fs";
import { DateTime } from "luxon";
import { TimeSeriesLookupNormalizingUnit } from "../cacher/time-series.js";
import { handleError } from "../utils/error.js";
import { Argv } from "yargs";
import {
  Transform,
  TransformCallback,
  TransformOptions,
  Writable,
} from "stream";
import {
  parseDuneContractUsageCSVRow,
  DuneRawRow,
  transformDuneRawRowToUsageRows,
  DailyContractUsageRow,
  DailyContractUsageClient,
} from "../collectors/dune/daily-contract-usage/client.js";
import nodePath from "path";
import { DuneClient } from "@cowprotocol/ts-dune-client";
import { DuneCSVUploader } from "../collectors/dune/utils/csv-uploader.js";
import { DUNE_API_KEY, DUNE_CONTRACTS_TABLES_DIR } from "../config.js";
import { ProjectRepository } from "../db/project.js";
import { Artifact, ArtifactNamespace, ArtifactType } from "../index.js";
import { UniqueArray } from "../utils/array.js";
import { In } from "typeorm";

export type DuneUploadArgs = object;

export type DuneSplitUsageArgs = {
  path: string[];
  outputDir: string;
};

function rowToString(row: DailyContractUsageRow) {
  return `${row.date},${row.contractAddress},${row.userAddress || ""},${
    row.safeAddress || ""
  },${row.gasCostGwei},${row.txCount}\n`;
}

export class DuneDayExporter extends Writable {
  currentDay: DateTime | null;
  stream: WriteStream | null;
  outputDir: string;
  writtenLines: number;
  totalLines: number;

  constructor(outputDir: string, opts: TransformOptions) {
    super({ ...{ objectMode: true, writableObjectMode: true }, ...opts });
    this.currentDay = null;
    this.stream = null;
    this.outputDir = outputDir;
    this.writtenLines = 0;
    this.totalLines = 0;
  }

  _write(chunk: any, encoding: BufferEncoding, done: TransformCallback): void {
    const row = chunk as DailyContractUsageRow;
    const rowTime = DateTime.fromISO(row.date);
    if (!this.currentDay) {
      this.currentDay = rowTime;
      this.startNewStream(this.currentDay);
    }
    if (this.currentDay.toMillis() !== rowTime.toMillis()) {
      if (this.currentDay > rowTime) {
        console.log(
          `OUT OF ORDER ${this.currentDay.toISO()} > ${rowTime.toISO()}`,
        );
        throw new Error("data is not in chronological order");
      }

      if (this.stream) {
        const closingStream = this.stream;
        setImmediate(() => {
          closingStream.end(() => {
            this.currentDay = rowTime;
            this.startNewStream(this.currentDay);
            this.writeToStream(row);
            done();
          });
        });
      }
    } else {
      if (this.stream) {
        const tryWrite = () => {
          if (!this.writeToStream(row)) {
            return setImmediate(done);
          }
          done();
        };
        tryWrite();
      } else {
        done();
      }
    }
  }

  writeToStream(row: DailyContractUsageRow) {
    this.writtenLines += 1;
    if (this.writtenLines % 10 == 0) {
      console.log(
        `File[${this.currentDay?.toISODate()}]: ${this.writtenLines}`,
      );
    }
    return this.stream!.write(rowToString(row));
  }

  startNewStream(date: DateTime) {
    const pathToWrite = nodePath.join(
      this.outputDir,
      `${date.toISODate()}.csv`,
    );
    this.writtenLines = 0;
    console.log(`Starting a write to file ${pathToWrite}`);
    this.stream = fs.createWriteStream(pathToWrite);
  }

  _final(done: (error?: Error | null | undefined) => void): void {
    console.debug("Closing the day writer");
    if (this.stream) {
      const closingStream = this.stream;
      setImmediate(() => {
        closingStream.end(() => {
          done();
        });
      });
    } else {
      done();
    }
  }
}

export class DuneSplitRow extends Transform {
  queue: {
    callback: TransformCallback;
    rows: DailyContractUsageRow[];
  }[];
  contractsMap: Record<number, string>;

  constructor(contractsMap: Record<number, string>, opts: TransformOptions) {
    super({
      ...{
        objectMode: true,
        readableObjectMode: true,
        writableObjectMode: true,
      },
      ...opts,
    });
    this.queue = [];
    this.contractsMap = contractsMap;
  }

  _write(
    chunk: any,
    _encoding: BufferEncoding,
    callback: TransformCallback,
  ): void {
    // Queue things up
    const row = chunk as DuneRawRow;
    const rows = transformDuneRawRowToUsageRows(row, this.contractsMap);
    this.queue.push({ callback: callback, rows: rows });
    this.pushRows();
  }

  pushRows() {
    while (this.queue.length > 0) {
      // Get top most queue
      const innerQueue = this.queue[0];
      const next = innerQueue.rows.pop();

      if (!next) {
        this.queue.pop();
        return innerQueue.callback();
      }

      if (!this.push(next)) {
        return;
      }
    }
  }

  _read(_size: number): void {
    this.pushRows();
  }
}

class SafeAggregate {
  rows: [TransformCallback, DailyContractUsageRow][];

  constructor(first: [TransformCallback, DailyContractUsageRow]) {
    this.rows = [first];
  }

  aggregate(): [TransformCallback, DailyContractUsageRow] {
    const rows = this.rows;
    const callback: TransformCallback = (err, data) => {
      rows.forEach((r) => r[0](err, data));
    };
    return [
      callback,
      this.rows.slice(1).reduce<DailyContractUsageRow>((agg, curr) => {
        const row = curr[1];
        const gasCostBI = BigInt(agg.gasCostGwei) + BigInt(row.gasCostGwei);
        return {
          date: agg.date,
          contractAddress: agg.contractAddress,
          userAddress: agg.userAddress,
          safeAddress: agg.safeAddress,
          txCount: agg.txCount + row.txCount,
          gasCostGwei: gasCostBI.toString(10),
        };
      }, this.rows[0][1]),
    ];
  }

  add(row: [TransformCallback, DailyContractUsageRow]) {
    this.rows.push(row);
  }

  get count() {
    return this.rows.length;
  }
}

export class DuneSafeAggregate extends Transform {
  incomingDay: [TransformCallback, DailyContractUsageRow][];
  outgoingRows: [TransformCallback, DailyContractUsageRow][];
  currentDay: DateTime | null;
  safes: Record<string, SafeAggregate>;

  constructor(opts: TransformOptions) {
    super({
      ...{
        objectMode: true,
        readableObjectMode: true,
        writableObjectMode: true,
      },
      ...opts,
    });
    this.incomingDay = [];
    this.outgoingRows = [];
    this.currentDay = null;
    this.safes = {};
  }

  _write(
    chunk: any,
    encoding: BufferEncoding,
    callback: TransformCallback,
  ): void {
    // Queue things up
    const row = chunk as DailyContractUsageRow;
    const rowDay = DateTime.fromISO(row.date);

    if (!this.currentDay) {
      this.currentDay = rowDay;
    }

    if (!this.currentDay.equals(rowDay)) {
      if (this.currentDay > rowDay) {
        console.log("this is happening");
        throw new Error("the data being passed is out of order");
      }
      this.outgoingRows.push(...this.incomingDay);
      this.outgoingRows.push(...this.popSafes());
      this.incomingDay = [];
    }

    // for some reason safes weren't aggregated properly on dune. let's do that here
    if (row.safeAddress) {
      const address = row.safeAddress.toLowerCase();
      const agg = this.safes[address];
      if (agg) {
        agg.add([callback, row]);
      } else {
        this.safes[address] = new SafeAggregate([callback, row]);
      }
    } else {
      this.incomingDay.push([callback, row]);
    }
    this.pushRows();
    callback();
  }

  popSafes(): [TransformCallback, DailyContractUsageRow][] {
    const safes: [TransformCallback, DailyContractUsageRow][] = [];
    for (const addr in this.safes) {
      safes.push(this.safes[addr].aggregate());
    }
    this.safes = {};
    return safes;
  }

  pushRows() {
    while (this.outgoingRows.length > 0) {
      // Get top most queue
      const next = this.outgoingRows.pop();

      if (!next) {
        return;
      }
      const row = next[1];

      if (!this.push(row)) {
        return;
      }
    }
  }

  _read(_size: number): void {
    this.pushRows();
  }
}

export function duneCommandGroup(topYargs: Argv) {
  topYargs.command<DuneSplitUsageArgs>(
    "split-contract-usage",
    "Split the contract usage rows",
    (yargs) => {
      yargs
        .option("path", { type: "array", description: "the paths" })
        .option("output-dir", { type: "string" });
    },
    (args) => handleError(splitContractUsage(args)),
  );
  topYargs.command<DuneUploadArgs>(
    "upload-latest-contracts-table",
    "A way to manually upload the contracts table",
    (_yargs) => {},
    (args) => handleError(uploadLatestContractTable(args)),
  );
}

export async function uploadLatestContractTable(_args: DuneUploadArgs) {
  const dune = new DuneClient(DUNE_API_KEY);
  const client = new DailyContractUsageClient(
    dune,
    new DuneCSVUploader(DUNE_API_KEY),
    {
      tablesDirectoryPath: DUNE_CONTRACTS_TABLES_DIR,
    },
  );
  const projects = await ProjectRepository.find({
    relations: {
      artifacts: true,
    },
    where: {
      artifacts: {
        type: In([ArtifactType.CONTRACT_ADDRESS, ArtifactType.FACTORY_ADDRESS]),
        namespace: ArtifactNamespace.OPTIMISM,
      },
    },
  });
  const allArtifacts = projects.flatMap((p) => p.artifacts);

  const uniqueArtifacts = new UniqueArray((a: Artifact) => a.id);
  allArtifacts.forEach((a) => uniqueArtifacts.push(a));

  await client.uploadContractTable(
    uniqueArtifacts.items().map((c) => {
      return {
        id: c.id,
        address: c.name,
      };
    }),
  );
}

/**
 * Used to backfill data from any csv. Tells you where to query next (if that's
 * needed). Also tells you how many rows you're getting. It checks if the dates
 * are ordered. If they're not this will error. The data must be ordered and a
 * `time` field must be the first field. It will normalize on days by default
 * (this means the date it will give for you to continue from will be normalized
 * to the day/hour/month _before or on_ the second to last available date). This
 * command can be fed multiple paths and it will ensure that these csv files
 * maintain a continous set of results.
 */
export async function splitContractUsage(
  args: DuneSplitUsageArgs,
): Promise<void> {
  await csvTransformAndSplit(args.path[0], args.outputDir, 0, "day");
}

type ScanResult = {
  path: string;
  isContinuous: boolean;
  lastPeriodRows: string[][];
  lastPeriodDateTime: DateTime;
};

export async function csvTransformAndSplit(
  path: string,
  outputDir: string,
  _dateIndex: number,
  _normalizatingUnit: TimeSeriesLookupNormalizingUnit,
  _previousScanResult?: ScanResult,
): Promise<ScanResult> {
  //const writeStream = fs.createWriteStream(, { encoding: 'utf-8' });

  const contractsMap = await new Promise<Record<number, string>>(
    (resolve, reject) => {
      const map: Record<number, string> = {};
      fs.createReadStream(
        "/home/raven/contracts-da1aae77b853fc7c74038ee08eec441b10b89570-90-503188.csv",
      )
        .pipe(parse({ delimiter: ",", fromLine: 2 }))
        .on("data", (row) => {
          const id = parseInt(row[0], 10);
          const address = row[1];
          map[id] = address;
        })
        .on("end", () => {
          resolve(map);
        })
        .on("error", (err) => {
          reject(err);
        });
    },
  );

  console.log("here");
  console.log(path);

  let expectedRows = 0;

  return new Promise<ScanResult>((resolve, reject) => {
    fs.createReadStream(path)
      .pipe(parse({ delimiter: ",", fromLine: 2 }))
      .pipe(
        new Transform({
          objectMode: true,
          readableObjectMode: true,
          writableObjectMode: true,
          highWaterMark: 1,
          transform: (chunk: string[], _encoding, callback) => {
            const rawRow = parseDuneContractUsageCSVRow(chunk);
            expectedRows += rawRow.usage.length;
            callback(null, rawRow);
          },
        }),
      )
      .pipe(new DuneSplitRow(contractsMap, { highWaterMark: 1 }))
      .pipe(new DuneSafeAggregate({ highWaterMark: 1000000 }))
      .pipe(new DuneDayExporter(outputDir, { highWaterMark: 1000 }))
      .on("data", (t) => {
        console.log(t);
      })
      .on("error", (err) => {
        /* eslint-disable no-restricted-properties */
        console.error(err);
        reject(err);
      })
      .on("finish", () => {
        console.log(`EXPECTED ROWS: ${expectedRows}`);
        resolve({
          path: "",
          isContinuous: false,
          lastPeriodRows: [],
          lastPeriodDateTime: DateTime.now(),
        });
      });
    // .on('data', (rows: DailyContractUsageRow[]) => {
    //   if (rows.length === 0) {
    //     return;
    //   }
    //   const rowsTime = DateTime.fromSQL(rows[0].date);
    //   if (!currentTime) {
    //     currentTime = rowsTime;
    //   }

    //   if (rowsTime > currentTime!) {
    //     // Write this out to a file
    //     const filePath = nodePath.join(outputDir, `${currentTime.toISODate()}.csv`)
    //     const rowsToWrite = currentDayBuffer;
    //     const stream = fs.createWriteStream(filePath, { encoding: 'utf-8' });
    //     // Be a bad steward and write a lot. We will make one file a day
    //     currentDayBuffer = [];
    //   }
    //   currentDayBuffer.push(...rows)
    // })
    // .on('finish', () => {
    // })
  });
}
