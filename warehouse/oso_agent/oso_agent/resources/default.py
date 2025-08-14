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

    def get_resources(self) -> dict[str, t.Any]:
        """Get all resources in the resolver."""
        return self._resources

    def validate_for_required_resources(
        self, resources_dict: dict[str, type]
    ) -> list[tuple[str, str]]:
        """Check if all resources in the dictionary are available in the resolver."""
        missing_resources: list[tuple[str, str]] = []
        for name, resource_type in resources_dict.items():
            if name not in self._resources:
                missing_resources.append(
                    (name, f"Resource '{name}' is missing from the resolver.")
                )
            elif not self._check_resource_type(self._resources[name], resource_type):
                missing_resources.append(
                    (
                        name,
                        f"Resource '{name}' is of type {type(self._resources[name])}, "
                        f"but should be {resource_type}.",
                    )
                )
        return missing_resources

    def _check_resource_type(self, resource: t.Any, expected_type: type) -> bool:
        """Check if a resource matches the expected type, handling subscripted generics."""
        try:
            # Handle subscripted generics like t.Callable[..., BaseModel]
            origin = t.get_origin(expected_type)
            if origin is not None:
                # For subscripted generics, check against the origin type
                return isinstance(resource, origin)
            else:
                # For regular types, use normal isinstance check
                return isinstance(resource, expected_type)
        except TypeError:
            # If isinstance check fails for any reason, assume it's valid
            # This is a fallback for complex type annotations
            return True

    def child_resolver(self, **additional_resources: t.Any) -> ResourceResolver:
        """Extend the resolver with additional resources."""
        kwargs = {**self._resources, **additional_resources}
        return DefaultResourceResolver.from_resources(**kwargs)

    def merge_resolver(self, other: ResourceResolver) -> ResourceResolver:
        """Merge another resolver's resources into this one."""
        merged_resources = {**self._resources, **other.get_resources()}
        return self.child_resolver(**merged_resources)
