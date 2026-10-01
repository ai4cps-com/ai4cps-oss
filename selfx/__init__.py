"""Backward-compatible import namespace for :mod:`ai4cps`."""

import importlib
import importlib.abc
import importlib.util
import sys

import ai4cps


class _AliasLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        target = "ai4cps" + module.__name__[len("selfx"):]
        # Import under the canonical name so module state and class identities
        # are shared, and canonical import metadata stays intact.
        sys.modules[module.__name__] = importlib.import_module(target)


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith("selfx."):
            return None
        canonical_name = "ai4cps" + fullname[len("selfx"):]
        canonical_spec = importlib.util.find_spec(canonical_name)
        if canonical_spec is None:
            raise ModuleNotFoundError(f"No module named {fullname!r}", name=fullname)
        return importlib.util.spec_from_loader(
            fullname,
            _AliasLoader(),
            is_package=canonical_spec.submodule_search_locations is not None,
        )


# Resolve legacy submodules lazily, before Python can load their source a
# second time under the old name.
sys.meta_path.insert(0, _AliasFinder())
sys.modules[__name__] = ai4cps
