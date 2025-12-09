# Protobuf Definitions

The protobuf definitions for OSO. Much of these are for our internal
asynchronous job processing system. These definitions are used to serialize and
deserialize messages sent between the frontend services and the data warehouse.

## "RunRequest" Messages

RunRequest messages are used to request that a job be run. These messages
typically include all the information needed to run the job, such as parameters
or configuration options. Each of these messages has at least the field
`run_id`, which is a unique identifier for the requested run. This ID can be
used to track the status of the job and retrieve results later. The async
workers should write logs and results to the associated run based on the given
`run_id` by calling the appropriate endpoints on the frontend service.

## Generating code from .proto files

### Install protoc

You will need the protobuf compiler `protoc`. Installation is only supported for
linux and macos using the script provided in this directory. Additionally, you
_must_ specify the protoc version to install. For example, to install version
33.2, run (from the root of the repository):

```bash
bash ./lib/protobufs/install_bash.sh 33.2 ./lib/protobufs/.install
```

### Generate the code for python

From the root of the repository, run the following command to generate the
python protobuf code into the `lib/protobufs/python/osoprotobufs` directory:

```bash
./lib/protobufs/.install/bin/protoc --proto_path=./lib/protobufs/definitions --python_out=./lib/protobufs/python/osoprotobufs ./lib/protobufs/definitions/*.proto --plugin=protoc-gen-mypy=.venv/bin/protoc-gen-mypy --mypy_out=./lib/protobufs/python/osoprotobufs
```

### Generating for typescript

TBD
