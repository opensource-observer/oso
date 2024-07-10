from typing import Callable

type ConfigCallable[T, **P] = Callable[P, T]


def unpack_config[
    R, T, **P
](conf: ConfigCallable[T, P]) -> Callable[[Callable[[T], R]], Callable[P, R]]:
    """This decorator allows a short hand method to create a simple interface to
    a function such that all arguments and keyword arguments are derived from
    some kind of configuration callable. Generally this would be something like
    a dataclass that can be used to create factories, but any form of callable
    can be used. This is a convenience function mostly for better type
    annotations.

    Args:
        conf: The config callable

    Example:

        from dataclasses import dataclass

        @dataclass(kw_only=True)
        class FactoryConfig:
            foo: str
            bar: str = "bar"

        class Example:
            def __init__(self, foo: str, bar: str):
                self.foo = foo
                self.bar = bar

            def show(self):
                print(self.foo)
                print(self.bar)

        @config_function(FactoryConfig)
        def my_factory(config: FactoryConfig):
            # do something with the config
            return

        # Later on this function can be called like this:
        ex = my_factory(foo="foo")
        ex.show() # should output foo and bar
    """

    def _wrapper(f: Callable[[T], R]):
        def _inner(*args: P.args, **kwargs: P.kwargs):
            config = conf(*args, **kwargs)
            return f(config)

        return _inner

    return _wrapper
