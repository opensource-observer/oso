from aioprometheus.collectors import Counter, Gauge, Histogram, Summary


class MetricsContainer:
    def __init__(self):
        self._counters = {}
        self._gauges = {}
        self._histograms = {}
        self._summaries = {}

    def gauge(self, name: str) -> Gauge:
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
        return self._histograms[name]

    def initialize_histogram(self, histogram: Histogram) -> Histogram:
        self._histograms[histogram.name] = histogram
        return histogram

    def summary(self, name: str) -> Summary:
        return self._summaries[name]

    def initialize_summary(self, summary: Summary) -> Summary:
        self._summaries[summary.name] = summary
        return summary
