

class LabelerContext:
    """A context to manage labels for instrumentation. Meant to be used with
    timing or other context managers. This allows the user to add labels
    dynamically within the timed context."""

    def __init__(self):
        self._labels: dict[str, str] = {}

    def add_labels(self, labels: dict[str, str]):
        self._labels.update(labels)

    def set_labels(self, labels: dict[str, str]):
        self._labels = labels

    def get_labels(self) -> dict[str, str]:
        return self._labels
