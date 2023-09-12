import yaml


class MyDumper(yaml.Dumper):
    """Custom Dumper for YAML to control formatting."""
    
    def __init__(self, *args, **kwargs):
        super(MyDumper, self).__init__(*args, **kwargs)
        self.add_representer(QuotedString, quoted_string_representer)

    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)


class QuotedString(str):
    """Custom string class to force quotes around the string in YAML output."""
    pass


def quoted_string_representer(dumper, data):
    """Representer for QuotedString."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')


def traverse_and_quote(data, key_to_quote):
    """Recursively traverse data to quote specific keys."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == key_to_quote and isinstance(value, str):
                data[key] = QuotedString(value)
            else:
                traverse_and_quote(value, key_to_quote)
    elif isinstance(data, list):
        for item in data:
            traverse_and_quote(item, key_to_quote)


def dump(yaml_dict, outpath):
        """Dump YAML data to a file with custom formatting."""
        traverse_and_quote(yaml_dict, 'address')
        formatters = dict(default_flow_style=False, sort_keys=False, indent=2)
        with open(outpath, 'w') as outfile:
            yaml.dump(yaml_dict, outfile, Dumper=MyDumper, **formatters)
