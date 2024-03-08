import gc
import arrow
import os
import time
from .parse import DuneContractUsage, parse_dune_csv
from typing import List, Tuple, Union, TypeAlias, Optional, Generator


def collect():
    collected = gc.collect()
    print("GC ran: collected %d" % collected)

    time.sleep(0.5)

    collected = gc.collect()
    print("GC ran: collected %d" % collected)

    print("GC garbage %d" % len(gc.garbage))


def load_csvs_in_folder(folder_path: str) -> Generator[DuneContractUsage, None, None]:
    # Get a list of CSV files in the folder
    csv_files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]

    # Sort the CSV files lexicographically
    csv_files.sort()

    last_date: Optional[arrow.Arrow] = None
    last_file: Optional[str] = None

    queue: List[DuneContractUsage] = []

    thresholds = gc.get_threshold()
    print("Current thresholds:", thresholds)

    for filename in csv_files:
        queue = []
        csv_path = os.path.join(folder_path, filename)
        print("Loading %s" % csv_path)
        for usage_row in parse_dune_csv(csv_path):
            if not last_date:
                last_date = usage_row.date
                last_file = filename
            if last_date != usage_row.date:
                if last_file != filename:
                    if usage_row.date > last_date:
                        if len(queue) == 0:
                            raise Exception("Missing dates")
                        else:
                            print(
                                "Emptying queue for %s of %d items"
                                % (last_date, len(queue))
                            )
                            last_date = usage_row.date
                            last_file = filename
                            for r in queue:
                                yield r
                            # So if the consumer is slow currently the python sdk
                            # doesn't handle that well and runs out of memory. This
                            # sleep here allows the consumer to consume depending on
                            # the size of the queue we just enqueued
                            time.sleep(len(queue) / 5000)
                            queue.clear()
                    else:
                        continue
                else:
                    if usage_row.date < last_date:
                        raise Exception("Dates are out of order")
                    else:
                        print(
                            "Emptying queue for %s of %d items"
                            % (last_date, len(queue))
                        )
                        last_date = usage_row.date
                        last_file = filename
                        for r in queue:
                            yield r
                        # So if the consumer is slow currently the python sdk
                        # doesn't handle that well and runs out of memory. This
                        # sleep here allows the consumer to consume depending on
                        # the size of the queue we just enqueued
                        time.sleep(len(queue) / 5000)
                        queue.clear()
            queue.append(usage_row)


def run():
    import sys
    import time

    last_date = None
    for row in load_csvs_in_folder(sys.argv[1]):
        if not last_date:
            last_date = row.date
        if last_date != row.date:
            if last_date > row.date:
                raise Exception("something is wrong")
            last_date = row.date
            print(row.date)
