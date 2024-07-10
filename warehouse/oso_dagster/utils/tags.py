from typing import Mapping


def add_tags(
    tags: Mapping[str, str], additional_tags: Mapping[str, str]
) -> Mapping[str, str]:
    new_tags = dict(tags)
    new_tags.update(additional_tags)
    return new_tags
