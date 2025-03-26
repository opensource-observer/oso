# OSO dbt

See the root directory for installation information.

## dbt Development

Our datasets are public! If you'd like to use them directly as opposed to adding to our
dbt models, checkout [our docs!](https://docs.opensource.observer/docs/get-started/)

### Using the virtual environment

Once installation has completed you can enter the virtual environment.

```bash
$ source .venv/bin/activate
```

From here you should have dbt on your path.

```bash
$ which dbt
```

_This should return something like `opensource-observer/oso/.venv/bin/dbt`_

### Authenticating to bigquery

If you have write access to the dataset then you can connect to it by setting
the `opensource_observer` profile in `dbt`. Inside `~/.dbt/profiles.yml` (create
it if it isn't there), add the following:

```yaml
opensource_observer:
  outputs:
    production:
      type: bigquery
      dataset: oso
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 32
    playground:
      type: bigquery
      dataset: oso_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: opensource-observer
      threads: 32
  # By default we target the playground. it's less costly and also safer to write
  # there while developing
  target: playground
```

### Setting up VS Code

The [Power User for dbt core](https://marketplace.visualstudio.com/items?itemName=innoverio.vscode-dbt-power-user) extension is pretty helpful.

You'll need the path to your virtual environment, which you can get by running

```bash
echo 'import sys; print(sys.prefix)' | uv run -
```

Then in VS Code:

- Install the extension
- Open the command pallet, enter "Python: select interpreter"
- Select "Enter interpreter path..."
- Enter the path from the uv command above

Check that you have a little check mark next to "dbt" in the bottom bar.

### Running dbt

Once you've updated any models you can run dbt _within the virtual environment_ by simply calling:

```bash
$ dbt run
```

:::tip
Note: If you configured the dbt profile as shown in this document,
this `dbt run` will write to the `opensource-observer.oso_playground` dataset.
:::

It is likely best to target a specific model so things don't take so long on some of our materializations:

```
$ dbt run --select {name_of_the_model}
```
