import logging

from aioprometheus.collectors import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)


class MetricsContainer:
    def __init__(self, allow_auto_init: bool = False):
        self._counters = {}
        self._gauges = {}
        self._histograms = {}
        self._summaries = {}
        self._allow_auto_init = allow_auto_init

    def gauge(self, name: str) -> Gauge:
        if name not in self._gauges and self._allow_auto_init:
            logger.warning(f"Gauge '{name}' not found. Initializing to zero.")
            self.initialize_gauge(
                Gauge(name, "Auto-initialized gauge. Please define properly."),
                0,
            )
        return self._gauges[name]

    def initialize_gauge(
        self,
        gauge: Gauge,
        initial_value: int = 0,
        initial_labels: dict | None = None,
    ) -> Gauge:
        self._gauges[gauge.name] = gauge
        if initial_labels is None:
            initial_labels = {}
        gauge.set(initial_labels, initial_value)
        return gauge

    def counter(self, name: str) -> Counter:
        if name not in self._counters and self._allow_auto_init:
            logger.warning(f"Counter '{name}' not found. Initializing to zero.")
            self.initialize_counter(
                Counter(name, "Auto-initialized counter. Please define properly."),
                0,
            )
        return self._counters[name]

    def initialize_counter(
        self,
        counter: Counter,
        initial_value: int = 0,
        initial_labels: dict | None = None,
    ) -> Counter:
        self._counters[counter.name] = counter
        if initial_labels is None:
            initial_labels = {}
        counter.set(initial_labels, initial_value)
        return counter

    def histogram(self, name: str) -> Histogram:
        if name not in self._histograms and self._allow_auto_init:
            logger.warning(
                f"Histogram '{name}' not found. Initializing with default buckets."
            )
            self.initialize_histogram(
                Histogram(
                    name,
                    "Auto-initialized histogram. Please define properly.",
                    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
                )
            )
        return self._histograms[name]

    def initialize_histogram(self, histogram: Histogram) -> Histogram:
        self._histograms[histogram.name] = histogram
        return histogram

    def summary(self, name: str) -> Summary:
        if name not in self._summaries and self._allow_auto_init:
            logger.warning(
                f"Summary '{name}' not found. Initializing with default settings."
            )
            self.initialize_summary(
                Summary(
                    name,
                    "Auto-initialized summary. Please define properly.",
                )
            )
        return self._summaries[name]

    def initialize_summary(self, summary: Summary) -> Summary:
        self._summaries[summary.name] = summary
        return summary
