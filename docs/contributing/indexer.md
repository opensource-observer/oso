# Indexer Architecture

The indexer collects collection, project, and artifacts metadata while
continously updating events for artifacts on various dimensions. The
architecture is designed to handle a variety of data sources that allow OSO to
provide useful insights.

## Overview

The major components of the system are:

- Collector

At a high level the indexer has a Scheduler that periodically queues Jobs that
describe the "Collector". The Worker pulls jobs off the queue. executes a Collector
that encapsulates the logic required to retrieve events into a

### Scheduler

_This component does a little too much and is likely to change in the future_

The scheduler is the main entrypoint for a majority of the functions of the
indexer. It schedules collection jobs into a queue onto our Postgres DB. At the
moment the queue is not cleaned nor is it FIFO. Jobs are chosen (and can be
worked on by workers) at random.

### Collector

The collection of events and metadata is currently handled by what we call "Collectors". This
architecture is described here.
