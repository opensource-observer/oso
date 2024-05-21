#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ -f "${DIR}/../.recce/recce_state_file/recce_state.json" ]; then
    echo "Launching the Recce server in review mode. The Recce state file is found."
    cp ${DIR}/../.recce/recce_state_file/recce_state.json recce_state.json
    recce server --review recce_state.json
else
    echo "Launching the Recce server."
    recce server
fi