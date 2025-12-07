# Async Worker

This is the async workers for the task queue that powers various things in the
system.

The async worker is a continous process that pulls tasks off a queue and assigns
them to worker functions that perform the actual work. This worker listens on
multiple GCP Pub/Sub topics for different types of tasks and routes them to the
appropriate worker processes. There are two main classes of tasks that the async
worker handles:

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

At this time, the async worker only supports trusted tasks. Untrusted task
support will be added in the future.
