"""Simple DB management helpers: create/drop schema and import existing JSON box data.

Usage:
  python backend/manage_db.py create   # creates tables
  python backend/manage_db.py import_boxes path/to/boxes.json
"""
import json
import os
import sys

from .models.sql_models import Base
from .repositories.sqlalchemy_repo import SQLAlchemyBoxesRepository

def create_db(db_url=None):
    repo = SQLAlchemyBoxesRepository(db_url=db_url)
    # engine and metadata already created in repo init
    print('Database initialized (file if using sqlite file).')

def import_boxes(json_path, db_url=None, user_id='local_user'):
    if not os.path.exists(json_path):
        raise FileNotFoundError(json_path)
    with open(json_path, 'r', encoding='utf-8') as f:
        arr = json.load(f)
    repo = SQLAlchemyBoxesRepository(db_url=db_url)
    # naive import: post each entry using repo's add_entry
    for e in arr:
        try:
            repo.add_entry(user_id, type('X', (), e))
        except Exception as ex:
            print('Failed to import entry', e, 'error', ex)
    print('Import complete')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: manage_db.py create|import_boxes <path>')
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'create':
        create_db()
    elif cmd == 'import_boxes' and len(sys.argv) >= 3:
        import_boxes(sys.argv[2])
    else:
        print('Unknown command')
