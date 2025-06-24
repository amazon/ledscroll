"""Registry of animations."""

from inspect import signature
import json
import logging

import docstring_parser

log = logging.getLogger(__name__)


class AnimationRegistry:
    def __init__(self):
        self._animations = {}

    def _get_animation_params(self, animation):
        """Returns list of parameters"""

        res = []
        descriptions = {
            param.arg_name: param.description
            for param in docstring_parser.parse(animation.__init__.__doc__).params
        }
        for p in signature(animation.__init__).parameters.values():
            # TODO: move to PEP 484 class hints
            param = {}
            if "font" in p.name:
                param["type"] = "F"
            elif p.annotation == tuple[int, int, int]:
                param["type"] = "C"
            elif p.annotation == list[tuple[int, int, int]]:
                param["type"] = "A"
            elif p.annotation == int:
                param["type"] = "D"
            else:
                # skip unknown parameter type
                continue
            param["name"] = p.name
            param["default"] = str(p.default)
            param["description"] = descriptions.get(p.name)
            res.append(param)
        return res


    def register(self, name, description, factory_func):
        """Register a factory function."""
        self._animations[name] = {
            "description": description,
            "factory": factory_func,
            "params": self._get_animation_params(factory_func)
            }

    def get_description(self, name):
        return self._animations[name]["description"]

    def get_params(self, name):
        return self._animations[name]["params"]

    def get_type(self, name):
        return "T" if "text" in name else "B"

    def create_animation(self, name, *args, **kwargs):
        return self._animations[name]["factory"](*args, **kwargs)

    def get_animation_factory(self, name):
        return self._animations[name]["factory"]

    def list_animations(self):
        return self._animations.keys()


animation_registry = AnimationRegistry()
"""Registry of animations (module variable)."""

# def register_strategy(name):
#     def decorator(strategy_class):
#         animation_registry.register(name, strategy_class)
#         return strategy_class

#     return decorator


def register_strategy(name: str):
    """Register strategy class using name."""
    def decorator(strategy_class: type):
        def factory(*args, **kwargs):
            return strategy_class(*args, **kwargs)

        animation_registry.register(name, strategy_class.__doc__, strategy_class)
        return strategy_class

    return decorator
