# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode


from dioptra.restapi.db.models import Group, User


def test_uow_commit(uow):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    uow.group_repo.create(g2)
    uow.commit()

    check_user = uow.user_repo.get_by_name("user2")
    assert check_user


def test_uow_rollback(uow):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    uow.group_repo.create(g2)
    uow.rollback()

    uow.commit()  # should do nothing due to previous rollback
    check_user = uow.user_repo.get_by_name("user2")
    assert not check_user


def test_uow_contextmanager_commit(uow):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    with uow:
        uow.group_repo.create(g2)

    check_user = uow.user_repo.get_by_name("user2")
    assert check_user


def test_uow_contextmanager_rollback(uow):
    u2 = User("user2", "password2", "user2@example.org")
    g2 = Group("group2", u2)

    try:
        with uow:
            uow.group_repo.create(g2)
            # causes block exit via exception, and rollback
            raise Exception()
    except Exception:
        pass

    uow.commit()  # should do nothing due to previous rollback
    check_user = uow.user_repo.get_by_name("user2")
    assert not check_user
