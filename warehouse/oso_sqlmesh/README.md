# OSO sqlmesh pipeline

## Setup

You will need [DuckDB](https://duckdb.org/) on your machine.

Install using Homebrew (macOS/Linux):

```bash
brew install duckdb
```

Install using APT (Debian/Ubuntu):

```bash
sudo apt-get install duckdb
```

Make sure to set the following environment variables
in your .env file (at the root of the oso repo)

```
SQLMESH_DUCKDB_LOCAL_PATH=/tmp/oso.duckdb
```

Now install dependencies.

```bash
uv sync
source ../../.venv/bin/activate
```

## Run

Run sqlmesh with our test seed data:

```bash
oso local sqlmesh-test --duckdb plan dev --start '1 week' --end now
```

_Note, the command above uses a wrapper `oso local sqlmesh` that will
automatically use the correct `warehouse/oso_sqlmesh` directory. It can also be
used to run with a local trino (see below)._

Explore the data in DuckDB:

```bash
duckdb
```

or

```bash
duckdb /tmp/oso.duckdb
```

See the tables are loaded:

```bash
SHOW ALL TABLES;
```

Execute a sample query:

```sql
SELECT * FROM metrics__dev.metrics_v0 LIMIT 5;
```

## Testing

Compile against your local DuckDB copy by running:

```bash
sqlmesh plan dev
```

As this will run against everything in the dataset, you may want to pick a shorter date range (that you know has data in it), eg:

```bash
sqlmesh plan dev --start 2024-12-01 --end 2024-12-31
```

If a source that's in BigQuery is missing from DuckDB, check the [seed data](warehouse/metrics_tools/seed/schemas/).
You can add new models by creating a new file in `schemas` and adding a `BaseModel` class with the table schema and `SeedConfig` object, eg:

```python
seed = SeedConfig(
    catalog="bigquery",
    schema="farcaster",
    table="profiles",
    base=Profiles,
    rows=[
        Profiles(
            fid=1,
            last_updated_at=datetime.now() - timedelta(days=2),
            data={"username": "Alice"},
            custody_address="0x123",
        ),
        Profiles(
            fid=2,
            last_updated_at=datetime.now() - timedelta(days=1),
            data={"username": "Bob"},
            custody_address="0x456",
        ),
    ],
)
```

...and then reference the model in your sqlmesh code via `@oso_source('YOUR_MODEL')`.

Important: whenever you add a new source, you will need to re-initialize your local database.

## sqlmesh Wrapper

This is a convenience function for running sqlmesh locally. This is equivalent
to running this series of commands:

```bash
cd warehouse/oso_sqlmesh
sqlmesh [...any sqlmesh args... ]
```

So running:

```bash
oso local sqlmesh plan
```

Would be equivalent to

```bash
cd warehouse/oso_sqlmesh
sqlmesh plan
```

## Running sqlmesh on a local Trino with docker-compose

This is the recommended way to test on Trino.
This does take more resources than simply running with duckdb.
We suggest most testing during development on duckdb.
When you are ready to submit your pull request,
we suggest testing against this environment as a final setup
to make sure models properly run on Trino.

### Prerequisites

In addition to having the normal dev tools for running the repo, you will also need:

- [docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/install/)

### Running sqlmesh

Run sqlmesh with our test seed data:

```bash
oso local sqlmesh-test plan dev --start '1 week' --end now
```

This command will handle the docker containers and seed data initialization before
wrapping the sqlmesh call. All the containers will be deleted at the end.

### Debugging Trino / SQLMesh

You can expose your local Trino instance for debugging by running:

```bash
cd warehouse
docker compose up --wait
```

This will open up a web server to interact with Trino directly at
`http://127.0.0.1:8080`.

This is also a good way if you want to keep running sqlmesh on top of the same containers
instead of recreating them every time. To initialize the data you can run:

```bash
oso local run-seed
```

## Running sqlmesh on a local Trino with Kind

Be warned, running local trino with [kind](https://kind.sigs.k8s.io/)
requires running kubernetes on your machine.
This requires significantly more time and resources than using docker-compose.
Unless you are specifically debugging Trino+Kubernetes,
we recommend using the docker-compose setup above.

### Prerequisites

In addition to having the normal dev tools for running the repo, you will also need:

- [docker](https://www.docker.com/)
- [kind](https://kind.sigs.k8s.io/)

Please install these before continuing.

For debugging, you may also want to install:

- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [k9s](https://k9scli.io/topics/install/)

Make sure to set the following environment variables
in your .env file (at the root of the oso repo)

```
GOOGLE_PROJECT_ID=opensource-observer
SQLMESH_DUCKDB_LOCAL_PATH=/tmp/oso.duckdb
```

Make sure you've logged into Google Cloud on your terminal

```bash
gcloud auth application-default login
```

### Local Kubernetes Cluster Setup

To initialize the local Trino cluster on Kubernetes run:

```bash
oso ops cluster-setup
```

This can take a while so please be patient (~10 minutes), but it will generate a local
registry that is used when running the trino deployment with the metrics
calculation service deployed. This is to test that process works and to ensure
that the MCS has the proper version deployed. Eventually this can/will be used
to test the dagster deployment.

_Note: It will probably look like it's stuck at the `Build and publish docker
image to local registry` step._

Once everything is setup, things should be running in the kind cluster
`oso-local-test-cluster`. Normally, you'd need to ensure that you forward the
right ports so that you can access the cluster to run the sqlmesh jobs but the
convenience functions we created to run sqlmesh ensure that this is done
automatically. However, before running sqlmesh you will need to initialize the
data in trino.

You can check if Kind has started all your pods:

```bash
kubectl get pods --all-namespaces
kubectl get kustomizations --all-namespaces
```

It may take an additional ~10 minutes after `oso ops cluster-setup` for
all the pods to come online.
In particular, you are waiting for `local-trino-psql` to be in a
"Running" state before you can run the data initialization.

If you need to kill your Kind cluster and start over, you can run

```bash
kind delete cluster --name oso-local-test-cluster
```

### Initialize Trino Data

Much like running against a local duckdb the local trino can also be initialized
with on the CLI like so:

```bash
oso local initialize --local-trino -m 1000 -d 3
```

_Note: It's best not to load too much data into trino for local testing. It won't be as
fast as sqlmesh with duckdb locally._

Once initialized, trino will be configured to have the proper source data for
sqlmesh.

### Running `plan` or `run`

Finally, to run `sqlmesh plan` do this:

```bash
oso local sqlmesh --local-trino plan
```

The `--local-trino` option should be passed before any sqlmesh args. Otherwise,
you can call any command or use any flags from sqlmesh after the `sqlmesh`
keyword in the command invocation. So to call `sqlmesh run` you'd simply do:

```bash
oso local sqlmesh --local-trino run
```

### Changing branches or random logouts

Please note, you may periodically be logged out of the local kind cluster or you
will need to change branches that you'd like the cluster to use. Just run `oso
ops cluster-setup` again and it will properly update the local cluster. It could
take a few minutes for the cluster to synchronize to the declared configuration.

### Debugging Trino

You can expose your local Trino instance for debugging by running:

```bash
kubectl port-forward --namespace=local-trino service/local-trino-trino 8080:8080 --address 0.0.0.0
```

This will open up a web server to interact with Trino directly at
`http://127.0.0.1:8080`.
