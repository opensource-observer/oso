import typing as t

from dagster import AssetSelection

experimental_tag = AssetSelection.tag("opensource.observer/experimental", "true")

partitioned_assets = AssetSelection.tag(
    "opensource.observer/extra", "partitioned-assets"
)

stable_source_tag = AssetSelection.tag("opensource.observer/source", "stable")

unstable_source_tag = AssetSelection.tag("opensource.observer/source", "unstable")

sbom_source_tag = AssetSelection.tag("opensource.observer/source", "sbom")

def add_tags(
    tags: t.Mapping[str, str], additional_tags: t.Mapping[str, str]
) -> t.Mapping[str, str]:
    new_tags = dict(tags)
    new_tags.update(additional_tags)
    return new_tags


def add_key_prefix_as_tag(
    tags: t.Mapping[str, t.Any], key_prefix: t.Sequence[str] | str | None
):
    if key_prefix:
        return add_tags(
            tags, {"opensource.observer/group": key_prefix_to_group_name(key_prefix)}
        )
    return add_tags(tags, {})


def key_prefix_to_group_name(key_prefix: t.Sequence[str] | str):
    return key_prefix if isinstance(key_prefix, str) else "__".join(list(key_prefix))
