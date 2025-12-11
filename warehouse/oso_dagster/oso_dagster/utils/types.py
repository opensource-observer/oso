from typing import Any, Callable

type ConfigCallable[T, **P] = Callable[P, T]


def unpack_config[Decorated, OriginalReturn, **Params](
    conf: ConfigCallable[OriginalReturn, Params],
) -> Callable[[Callable[[OriginalReturn], Decorated]], Callable[Params, Decorated]]:
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

        @unpack_config(FactoryConfig)
        def my_factory(config: FactoryConfig):
            # do something with the config
            return

        # Later on this function can be called like this:
        ex = my_factory(foo="foo")
        ex.show() # should output foo and bar
    """

    def _wrapper(f: Callable[[OriginalReturn], Decorated]):
        def _inner(*args: Params.args, **kwargs: Params.kwargs):
            config = conf(*args, **kwargs)
            return f(config)

        return _inner

    return _wrapper


def params_from[**P](c: Callable[P, Any]):
    def _decorator[R](f: Callable[..., R]) -> Callable[P, R]:
        def _wrapper(*args: P.args, **kwargs: P.kwargs):
            return f(*args, **kwargs)

        return _wrapper

    return _decorator
