# Testing script
from metrics_tools.compute import flight
import click


@click.command()
@click.option("--batch-size", type=click.INT, default=1)
def main(batch_size: int):
    flight.get(batch_size=batch_size)


if __name__ == "__main__":
    main()
