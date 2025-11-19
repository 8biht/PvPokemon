import pytest

from backend.repositories.sqlalchemy_repo import SQLAlchemyBoxesRepository
from backend.services import BoxService


def test_add_and_get_box_in_memory():
    repo = SQLAlchemyBoxesRepository(db_url='sqlite:///:memory:')
    service = BoxService(repo, assets_dir='.', pokedex=None)
    # use an http sprite to bypass local asset checks
    box = service.add_to_box('test_user', name='Test', sprite='http://example/s.png', cp=100, quick_move=None, charge_moves=['X'])
    assert isinstance(box, list)
    res = service.get_box('test_user')
    assert len(res) == 1
    assert res[0]['cp'] == 100
