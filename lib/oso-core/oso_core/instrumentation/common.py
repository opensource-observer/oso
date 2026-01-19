type LabelType = dict[str, str]


class MetricsLabler:
    """A simple way to share labels across different instrumentations"""

    def __init__(self):
        self._labels: LabelType = {}

    def add_labels(self, labels: LabelType):
        self._labels.update(labels)

    def set_labels(self, labels: LabelType):
        self._labels = labels

    def get_labels(self, append_oneoff_labels: LabelType | None = None) -> LabelType:
        """
        Get the current labels, optionally appending one-off labels
        that are not stored in the Labeler.
        """
        if append_oneoff_labels:
            combined_labels = self._labels.copy()
            combined_labels.update(append_oneoff_labels)
            return combined_labels
        return self._labels

    def copy(self) -> "MetricsLabler":
        new_labeler = MetricsLabler()
        new_labeler.set_labels(self._labels.copy())
        return new_labeler


class MetricsLabeler:
    """A context to manage labels for instrumentation. Meant to be used with
    timing or other context managers. This allows the user to add labels
    dynamically within the timed context."""

    def __init__(self, labeler: MetricsLabler | None = None):
        if labeler:
            self._labeler = labeler.copy()
        else:
            self._labeler = MetricsLabler()

    def add_labels(self, labels: LabelType):
        self._labeler.add_labels(labels)

    def set_labels(self, labels: LabelType):
        self._labeler.set_labels(labels)

    def get_labels(self, append_oneoff_labels: LabelType | None = None) -> LabelType:
        return self._labeler.get_labels(append_oneoff_labels=append_oneoff_labels)
