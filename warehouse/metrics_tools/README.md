# metrics_tools

This is a set of tools for sqlmesh to generate metrics based on our data. This
is NOT in the `metrics_mesh` directory because we actually don't want this to
live in that folder. The reason for this is because when sqlmesh loads python
environments into the state connection it attempts to serialize python and that
can make writing tools for it a little difficult. Particularly one of it's
serializers will attempt to store everything that is adjacent to a file that is
generating a model. So, in order to get around this we must instead ensure that
the `@model` decorator is called only within the `metrics_mesh` directory.
However all other orchestration should remain separate of that. Eventually what
we should do is instead override the `model` decorator with our own decorator
that ensures that sqlmesh uses an imported tool. This might not work for others
that use sqlmesh but it will work fine for us and our monorepo and our
deployment style with sqlmesh.
