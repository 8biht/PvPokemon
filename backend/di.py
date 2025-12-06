"""
Dependency container / composition root for PvPokemon backend.
Provides a single place to instantiate Config, repository, service, pokedex and projections.
This helps keep wiring in one module and improves testability.
"""
from typing import Any
import os

from .config import get_config
from .repo_factory import get_repository
from .pokemon import Pokedex
from .services import BoxService


class Container:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.cfg = get_config()
        # repository factory uses cfg to decide implementation
        self.repo = get_repository(self.data_dir)
        # load pokedex from file if present
        pokedex_path = os.path.join(os.path.dirname(__file__), 'data', 'pokedex.json')
        self.pokedex = Pokedex.from_file(pokedex_path)
        # create the service using repository, assets dir and pokedex
        self.service = BoxService(self.repo, self.cfg.ASSETS_DIR, pokedex=self.pokedex)


def build_container(data_dir: str) -> Container:
    """Create and return a Container instance wired for the current app.

    Keep instantiation here rather than spread across modules so tests can
    create lightweight containers with test doubles.
    """
    return Container(data_dir)
