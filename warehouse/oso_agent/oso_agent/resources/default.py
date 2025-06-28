import typing as t

from .types import ResourceResolver


class DefaultResourceResolver:
    """A resolver for resources in a workflow using a service locator pattern)."""

    @classmethod
    def from_resources(cls, **kwargs: t.Any) -> ResourceResolver:
        """Create a ResourceResolver from keyword arguments."""
        resolver = cls()
        for name, value in kwargs.items():
            resolver.add_resource(name, value)
        return resolver

    def __init__(self):
        self._resources: dict[str, t.Any] = {}

    def add_resource(self, name: str, resource: t.Any) -> None:
        self._resources[name] = resource

    def get_resource(self, name: str) -> t.Any:
        """Get a resource by name."""
        if name not in self._resources:
            raise KeyError(f"Resource '{name}' not found in resolver.")
        return self._resources[name]

    def validate_for_required_resources(
        self, resources_dict: dict[str, type]
    ) -> list[tuple[str, str]]:
        """Check if all resources in the dictionary are available in the resolver."""
        missing_resources: list[tuple[str, str]] = []
        for name, resource_type in resources_dict.items():
            if name not in self._resources:
                missing_resources.append((
                    name,
                    f"Resource '{name}' is missing from the resolver."
                ))
            elif not isinstance(self._resources[name], resource_type):
                missing_resources.append((
                    name,
                    f"Resource '{name}' is of type {type(self._resources[name])}, "
                    f"but should be {resource_type}.",
                ))
        return missing_resources
    
    def child_resolver(self, **additional_resources: t.Any) -> ResourceResolver:
        """Extend the resolver with additional resources."""
        kwargs = {**self._resources, **additional_resources}
        return DefaultResourceResolver.from_resources(**kwargs)