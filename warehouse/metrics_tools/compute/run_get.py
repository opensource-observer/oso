# Testing script
from metrics_tools.compute import flight
import click
from datetime import datetime


@click.command()
@click.option("--batch-size", type=click.INT, default=1)
@click.option("--start", default="2024-01-01")
@click.option("--end")
def main(batch_size: int, start, end):
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    flight.run_get(batch_size=batch_size, start=start, end=end)


if __name__ == "__main__":
    main()
