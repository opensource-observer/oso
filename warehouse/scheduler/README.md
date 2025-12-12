# OSO Scheduler

The custom scheduler system for data assets in OSO. It is powered by workers
that process a task queue to materialize user defined models, data ingestion,
and other assets.

The scheduler workers are continuous processes that pull tasks off a queue and
assign them to worker functions that perform the actual work. This worker
listens on multiple GCP Pub/Sub topics for different types of tasks and routes
them to the appropriate worker processes. There are two main classes of tasks
that the workers handle:

1. Trusted tasks: These are tasks that are considered safe to run inside the
   main application environment. They have access to the full application context
   and can interact with the database and other services directly.
2. Untrusted tasks: These are tasks that are potentially unsafe to run inside
   the main application environment. They are intended for execution in some
   kind of isolated enviroment. We will need various strategies to handle this
   isolation. For example:
   - Pyodide for running untrusted Python code in WASM
   - Special ephemeral k8s service accounts with limited permissions and
     environment.

At this time, the workers only support trusted tasks. Untrusted task support
will be added in the future.

## Running the scheduler's workers

The primary implementation of the worker's work queue is through gcp pub/sub. As
such, to run the workers locally, you will need to have the gcp pub/sub emulator
running. You will need to make sure this is installed and running before
starting the workers. See the [GCP Pub/Sub Emulator
documentation](https://cloud.google.com/pubsub/docs/emulator) for instructions
on how to set this up.

Once setup, you can run the emulator with the following command (if you didn't
already based on the docs linked above):

```bash
gcloud beta emulators pubsub start --project=oso-local-test
```

Ensure that you set the following environment variables are set in the `.env`
file (located wherever you call the script from):

```bash
PUBSUB_EMULATOR_HOST=localhost:8085
SCHEDULER_GCP_PROJECT_ID=oso-local-test
SCHEDULER_OSO_API_URL=http://localhost:3000/api/v1/osograph
```

## Generating Python GraphQL client code

From inside the `warehouse/scheduler` directory, run:

```bash
uv run ariadne-codegen
```

## Running the workers

At the moment, a single worker process can only handle a single queue at a time.
To run a worker for a specific queue, use the following command from anywhere in
the repo.

```bash
uv run scheduler run <name-of-queue>
```

## Publishing fake messages to the queues

The scheduler includes a utility to publish fake messages to the queues for
testing purposes. To use this utility, run the following command from anywhere in
the repo:

```bash
uv run scheduler testing publish <name-of-fake-message>
```

The final argument is actually not an option but instead supposed to be a
subcommand. You can add new fake messages publishers within the
`warehouse/scheduler/scheduler/config.py` file by adding new subcommands to the
`Publish` config model.
