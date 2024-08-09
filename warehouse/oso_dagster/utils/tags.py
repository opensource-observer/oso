from typing import Mapping, Sequence


def add_tags(
    tags: Mapping[str, str], additional_tags: Mapping[str, str]
) -> Mapping[str, str]:
    new_tags = dict(tags)
    new_tags.update(additional_tags)
    return new_tags


def add_key_prefix_as_tag(
    tags: Mapping[str, str], key_prefix: Sequence[str] | str | None
):
    if key_prefix:
        return add_tags(
            tags, {"opensource.observer/group": key_prefix_to_group_name(key_prefix)}
        )
    return add_tags(tags, {})


def key_prefix_to_group_name(key_prefix: Sequence[str] | str):
    return key_prefix if isinstance(key_prefix, str) else "__".join(list(key_prefix))
