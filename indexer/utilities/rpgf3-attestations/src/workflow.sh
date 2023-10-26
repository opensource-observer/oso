#!/bin/bash
python src/oss-directory.py
python src/fetch_from_eas.py
python src/analyze_apps.py
python src/reviewer.py
python ../address-indexers/src/address_tagging.py --csv data/ossd_reviewer.csv --address_col artifact --label_col type --chain optimism