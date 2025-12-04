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
