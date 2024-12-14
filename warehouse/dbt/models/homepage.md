{% docs __overview__ %}

# Open Source Observer dbt Reference

![Open Source Observer](https://avatars.githubusercontent.com/u/145079657?s=200&v=4)

Welcome to the reference documentation for the
OSO dbt data pipeline.

## Navigation

You can use the Project and Database navigation tabs on the left side of the window to explore the models in your project.

You can click the blue icon on the bottom-right corner of the page to view the lineage graph of your models.

On model pages, you'll see the immediate parents and children of the model you're exploring. By clicking the Expand button at the top-right of this lineage pane, you'll be able to see all of the models that are used to build, or are built from, the model you're exploring.

Once expanded, you'll be able to use the --select and --exclude model selection syntax to filter the models in the graph. For more information on model selection, check out the dbt docs.

Note that you can also right-click on models to interactively filter and explore the graph.

## More information

- [Website](https://www.opensource.observer/)
- [Documentation](https://docs.opensource.observer/)
- [Technical architecture](https://docs.opensource.observer/docs/references/architecture)
- [GitHub repo](https://github.com/opensource-observer/oso)
- [Dagster dashboard](https://dagster.opensource.observer/)

{% enddocs %}
