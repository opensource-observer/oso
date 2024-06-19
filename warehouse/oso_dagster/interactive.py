import os
from IPython import embed

from dotenv import load_dotenv

load_dotenv()


print(os.path.abspath("."))
from .definitions import load_resources
from .factories import AssetFactoryResponse
from .assets import *
from dagster import build_asset_context, AssetCheckResult
from functools import reduce
from .factories.goldsky.checks import BlockchainCheckConfig
from .cbt import CBTResource


def main():
    asset_factories, asset_defs, resources = load_resources()
    embed(header="Interactive oso_dagster loader")


def run_full_checks(resources: dict, asset_factories: List[AssetFactoryResponse]):
    checks_to_run = reduce(lambda x, y: x + y.checks, asset_factories, [])
    config = BlockchainCheckConfig(full_refresh=True)
    responses: Dict[str, AssetCheckResult] = {}
    for check in checks_to_run:
        name = list(check.asset_and_check_keys)[0].name
        response = check(build_asset_context(), cbt=resources["cbt"], config=config)
        responses[name] = response

    for check_name, response in responses.items():
        if response.passed:
            print(f"{check_name}: PASSED")
            continue
        print(f"{check_name}: FAILED")
        print(f"    METADATA={response.metadata}")
    return responses


def find_missing_transactions(resources: dict):
    pass


if __name__ == "__main__":
    main()
