def test_repository_basic_operations(test_env):
    appmod = test_env
    repo = appmod.container.repo

    # user operations
    created = repo.ensure_user('repo_user')
    assert created is True
    u = repo.get_user('repo_user')
    assert u is not None and u.id == 'repo_user'

    # set password
    ok = repo.set_user_password('repo_user', 'hashed_pw')
    assert ok is True
    u = repo.get_user('repo_user')
    assert getattr(u, 'password_hash', None) == 'hashed_pw'

    # refresh token lifecycle
    repo.create_refresh_token('repo_user', 'rt1')
    rt = repo.get_refresh_token('rt1')
    assert rt is not None and rt.token == 'rt1'
    revoked = repo.revoke_refresh_token('rt1')
    assert revoked is True

    # box entries
    from backend.dto import BoxEntry
    entry = BoxEntry(name='Pikachu', sprite='pikachu.png', cp=500)
    box = repo.add_entry('repo_user', entry)
    assert isinstance(box, list) and len(box) >= 1

    # update entry
    updated = repo.update_entry('repo_user', 0, BoxEntry(name='Raichu', sprite='raichu.png', cp=1500))
    assert isinstance(updated, list)

    # remove entry
    removed, box_after = repo.remove_entry('repo_user', 0)
    assert removed.name in ('Raichu', 'Pikachu')
