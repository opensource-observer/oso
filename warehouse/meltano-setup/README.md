# Meltano Special Setup

Meltano has different enough major versions of dependencies that it _cannot_ be
used with many of the other things we're already using. Due to this, we have a
separate poetry setup here so that meltano installations can be done.

Additionally, you'll need to have python <= 3.10 which is different that most of
the repository.

## Setup

Assumes you setup pyenv

Do the following if you're at the root of the `oso` repository:

```bash
$ pyenv install 3.10.13
$ cd warehouse/meltano-setup
$ poetry install
$ poetry shell
```

Now `meltano` should be available to you:

```bash
$ meltano
```
