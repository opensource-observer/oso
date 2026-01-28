# OSO Codegen Tooling

This directory contains tooling for python code generation. This includes:

- Generating `typing.Protocol` classes from existing class definitions.
- Generating testing fakes for classes that provide real data (assuming the
  responses are dataclasses, pydantic models, or typed dicts).

## Generating Protocols

To generate protocol classes for a given module, run the following command:

```bash
uv run oso-core-codegen protocol ${class_path} ${output_path}
```

Where `${class_path}` is the python module path in the form `package.module:ClassName`
and `${output_path}` is the file path to write the generated protocol class to.

## Generating Fakes

To generate fake classes for a given module, run the following command:

```bash
uv run oso-core-codegen fake ${class_path} ${output_path}
```

Where `${class_path}` is the python module path in the form `package.module:ClassName`
and `${output_path}` is the file path to write the generated fake class to.
