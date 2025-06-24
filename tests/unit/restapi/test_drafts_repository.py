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
import datetime

import pytest

import dioptra.restapi.db.models as m
import dioptra.restapi.errors as e
from dioptra.restapi.db.models.constants import resource_lock_types, user_lock_types
from dioptra.restapi.db.repository.drafts import DraftType
from dioptra.restapi.db.repository.utils import DeletionPolicy


@pytest.fixture
def draft_content():
    """Some draft resource content (not valid for a draft modification)"""

    draft_content = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": None,
        "resource_snapshot_id": None,
        "base_resource_id": None,
    }

    return draft_content


@pytest.fixture
def draft_stuff(db, fake_data, draft_content):
    """
    Drafts are complicated to set up.  Need users, groups, resources,
    resource snapshots, before you can make drafts.  This fixture creates a
    bunch of stuff necessary to test drafts, persists it to the db, then
    returns a data structure containing the persisted objects.
    """

    alannah = m.User("alannah", "password", "alannah@example.org")
    alpha = m.User("alpha", "password", "alpha@example.org")
    abi = m.User("abi", "password", "abi@example.org")

    bear = m.User("bear", "password", "bear@example.org")
    bria = m.User("bria", "password", "bria@example.org")
    blaze = m.User("blaze", "password", "blaze@example.org")

    cyan = m.User("cyan", "password", "cyan@example.org")
    cydney = m.User("cydney", "password", "cydney@example.org")
    coty = m.User("coty", "password", "coty@example.org")

    dell = m.User("dell", "password", "dell@example.org")
    derick = m.User("derick", "password", "derick@example.org")
    dixon = m.User("dixon", "password", "dixon@example.org")

    groupa = m.Group("groupa", alannah)
    groupb = m.Group("groupb", bear)
    groupc = m.Group("groupc", cyan)
    groupd = m.Group("groupd", dell)

    groupa.members.extend(
        (
            m.GroupMember(
                True,
                True,
                True,
                True,
                alannah,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                alpha,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                abi,
            ),
        )
    )

    groupa.managers.append(m.GroupManager(True, True, alannah))

    groupb.members.extend(
        (
            m.GroupMember(
                True,
                True,
                True,
                True,
                bear,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                bria,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                blaze,
            ),
        )
    )

    groupb.managers.append(m.GroupManager(True, True, bear))

    groupc.members.extend(
        (
            m.GroupMember(
                True,
                True,
                True,
                True,
                cyan,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                cydney,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                coty,
            ),
        )
    )

    groupc.managers.append(m.GroupManager(True, True, cyan))

    groupd.members.extend(
        (
            m.GroupMember(
                True,
                True,
                True,
                True,
                dell,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                derick,
            ),
            m.GroupMember(
                True,
                True,
                True,
                True,
                dixon,
            ),
        )
    )

    groupd.managers.append(m.GroupManager(True, True, dell))

    # Make queue resources and snapshots.
    # queue creator, owner, timestamps.  Timestamps ought to be in
    # chronologically increasing order.
    queue_data = (
        (
            abi,
            groupa,
            "1997-10-30T06:13:07.335930Z",
            "1998-07-24T13:10:25.622395Z",
            "1999-07-24T07:28:49.168213Z",
        ),
        (
            blaze,
            groupb,
            "1997-11-21T06:17:44.809735Z",
            "1999-08-03T12:38:25.148233Z",
            "2002-01-22T01:51:43.734094Z",
        ),
        (
            coty,
            groupc,
            "1999-04-17T19:23:31.765042Z",
            "2008-09-27T06:48:28.009274Z",
            "2010-06-01T10:14:56.032274Z",
        ),
        (
            dixon,
            groupd,
            "2000-07-08T00:42:24.788532Z",
            "2002-04-24T22:36:16.889978Z",
            "2003-05-26T08:09:13.075871Z",
        ),
    )

    # all_queues will be a list of lists of queues, corresponding to the
    # timestamps above.  Each inner list has snaps of the same resource.
    all_queues = []
    for creator, owner, *creation_times in queue_data:
        first_q = fake_data.queue(creator, owner)
        first_q.resource.created_on = first_q.created_on = (
            datetime.datetime.fromisoformat(creation_times[0])
        )

        queues = [first_q]
        for snap_ts in creation_times[1:]:
            q = m.Queue(
                first_q.description, first_q.resource, first_q.creator, first_q.name
            )
            q.created_on = datetime.datetime.fromisoformat(snap_ts)
            queues.append(q)

        all_queues.append(queues)

    # gotta add all this junk to the db so it will have IDs we can use in the
    # drafts
    db.session.add_all((groupa, groupb, groupc, groupd))
    for qs in all_queues:
        db.session.add_all(qs)
    db.session.commit()

    # Now, we need some draft modifications of some of the above snapshots.
    # draft creator, snapshot being modified (creator must be in the same group
    # as the resource)
    draft_mod_data = (
        (alpha, all_queues[0][0]),
        (bria, all_queues[1][1]),
        (cydney, all_queues[2][2]),
        (derick, all_queues[3][0]),
    )

    draft_mods = []
    for creator, snap in draft_mod_data:
        data = draft_content.copy()
        data["resource_id"] = snap.resource_id
        data["resource_snapshot_id"] = snap.resource_snapshot_id
        draft_mod = m.DraftResource("queue", data, snap.resource.owner, creator)
        draft_mods.append(draft_mod)

    # Lastly, some draft resources
    # Just creators; the target_owners will be their groups
    draft_resource_data = (alannah, bear, cyan, dell)

    draft_resources = []
    for creator in draft_resource_data:
        draft_resource = m.DraftResource(
            "queue", draft_content, creator.group_memberships[0].group, creator
        )
        draft_resources.append(draft_resource)

    # An entry point is a legal parent resource to a queue.  We can use this
    # to test base_resource_id of drafts.  And of course, we refer to it by
    # ID, so we need to add and commit it so it has one.
    ep_res = m.Resource("entry_point", groupc)
    ep = m.EntryPoint("description", ep_res, cydney, "entrypoint", "task graph", [])
    db.session.add(ep)
    db.session.commit()

    # we need a pile of drafts created by a single person to test paging.  The
    # get_by_filters_paged() method searches by a single user at a time, so all
    # the drafts created above don't really amount to enough to test paging
    # with.  Draft resources are easiest to create en masse.  Use the above
    # entry point for their base_resource_id, for testing...
    for _ in range(10):
        data = draft_content.copy()
        data["base_resource_id"] = ep.resource_id
        draft_resource = m.DraftResource("queue", data, groupd, dell)
        draft_resources.append(draft_resource)

    # And add all our drafts
    db.session.add_all(draft_mods)
    db.session.add_all(draft_resources)
    db.session.commit()

    # Now we gotta return all this stuff in some big data structure for the
    # unit tests...
    fixture_data = {
        "alannah": alannah,
        "alpha": alpha,
        "abi": abi,

        "bear": bear,
        "bria": bria,
        "blaze": blaze,

        "cyan": cyan,
        "cydney": cydney,
        "coty": coty,

        "dell": dell,
        "derick": derick,
        "dixon": dixon,

        "groupa": groupa,
        "groupb": groupb,
        "groupc": groupc,
        "groupd": groupd,

        "queues": all_queues,
        "draft_mods": draft_mods,
        "draft_resources": draft_resources,
        "base_resource": ep,
    }

    return fixture_data


def test_drafts_create_draft_resource(db, drafts_repo, account, draft_content):

    draft = m.DraftResource(
        "queue",
        draft_content,
        account.group,
        account.user,
    )

    drafts_repo.create_draft_resource(draft)

    db.session.commit()


def test_drafts_create_draft_resource_group_not_exist(
    drafts_repo, account, draft_content
):

    group = m.Group("doesnt exist", account.user)

    draft = m.DraftResource(
        "queue",
        draft_content,
        group,
        account.user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_resource_user_not_exist(
    drafts_repo, account, draft_content
):

    user = m.User("user", "password", "user@example.org")

    draft = m.DraftResource(
        "queue",
        draft_content,
        account.group,
        user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_resource_user_not_in_group(
    db, drafts_repo, draft_content, fake_data
):
    acct1 = fake_data.account()
    acct2 = fake_data.account()

    db.session.add_all([acct1.user, acct1.group, acct2.user, acct2.group])
    db.session.commit()

    draft = m.DraftResource(
        "queue",
        draft_content,
        acct1.group,
        acct2.user,
    )

    with pytest.raises(e.UserNotInGroupError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_resource_already_exists(
    db,
    drafts_repo,
    account,
    draft_content,
):

    draft = m.DraftResource(
        "queue",
        draft_content,
        account.group,
        account.user,
    )

    drafts_repo.create_draft_resource(draft)

    db.session.commit()

    with pytest.raises(e.DraftAlreadyExistsError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_resource_base_not_exist(
    drafts_repo, account, draft_content
):

    draft_content["base_resource_id"] = 999999  # refers to non-existent resource

    draft = m.DraftResource(
        "queue",
        draft_content,
        account.group,
        account.user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_resource_base_deleted(
    db, drafts_repo, draft_stuff, draft_content
):
    base = draft_stuff["base_resource"]
    lock = m.ResourceLock(resource_lock_types.DELETE, base.resource)
    db.session.add(lock)
    db.session.commit()

    draft_content["base_resource_id"] = base.resource_id

    draft = m.DraftResource(
        "queue",
        draft_content,
        draft_stuff["groupb"],
        draft_stuff["bear"],
    )

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_resource_invalid_base_resource_type(
    db, drafts_repo, account, fake_data, draft_content
):

    exp = fake_data.experiment(account.user, account.group)
    db.session.add(exp)
    db.session.commit()

    # Parent of a queue can't be an experiment
    draft_content["base_resource_id"] = exp.resource_id

    draft = m.DraftResource(
        "queue",
        draft_content,
        account.group,
        account.user,
    )

    with pytest.raises(e.DraftBaseInvalidError):
        drafts_repo.create_draft_resource(draft)


def test_drafts_create_draft_modification(db, drafts_repo, fake_data, account):

    # Set up something to modify
    queue = fake_data.queue(account.user, account.group)

    db.session.add_all([account.user, account.group, queue])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        account.user,
    )

    drafts_repo.create_draft_modification(draft)
    db.session.commit()


def test_drafts_create_draft_modification_user_not_exist(
    db, drafts_repo, fake_data, account
):

    queue = fake_data.queue(account.user, account.group)

    db.session.add_all([account.user, account.group, queue])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    user = m.User("user", "password", "user@example.org")

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)

    user.user_id = 999999

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_group_not_exist(
    db, drafts_repo, fake_data, account
):

    queue = fake_data.queue(account.user, account.group)

    db.session.add_all([account.user, account.group, queue])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    user = m.User("user", "password", "user@example.org")
    group = m.Group("agroup", user)

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        group,
        account.user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)

    group.group_id = 999999

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_resource_not_exist(db, drafts_repo, account):
    db.session.add_all([account.user, account.group])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": None,
        "resource_snapshot_id": None,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        account.user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)

    draft.payload["resource_id"] = 999999
    draft.payload["resource_snapshot_id"] = 999999

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_resource_deleted(
    db, drafts_repo, fake_data, account
):
    queue = fake_data.queue(account.user, account.group)
    db.session.add_all([account.user, account.group, queue])
    db.session.commit()

    queue_delete_lock = m.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db.session.add(queue_delete_lock)
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        account.user,
    )

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_resource_snapshot_not_exist(
    db, drafts_repo, fake_data, account
):
    queue = fake_data.queue(account.user, account.group)
    db.session.add_all([account.user, account.group, queue])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": 999999,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        account.user,
    )

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_user_not_in_group(db, drafts_repo, fake_data):

    acct1 = fake_data.account()
    acct2 = fake_data.account()
    queue = fake_data.queue(acct1.user, acct1.group)

    db.session.add_all([acct1.user, acct1.group, acct2.user, acct2.group, queue])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        acct1.group,
        acct2.user,
    )

    with pytest.raises(e.UserNotInGroupError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_draft_already_exists(
    db, drafts_repo, fake_data, account
):

    queue = fake_data.queue(account.user, account.group)

    db.session.add_all([account.user, account.group, queue])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        account.user,
    )

    drafts_repo.create_draft_modification(draft)
    db.session.commit()

    with pytest.raises(e.DraftAlreadyExistsError):
        # Creating a second draft with the same settings should fail
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_owner_mismatch(db, drafts_repo, fake_data):

    acct1 = fake_data.account()
    acct2 = fake_data.account()

    queue = fake_data.queue(acct1.user, acct1.group)

    db.session.add_all(
        [
            acct1.user,
            acct1.group,
            acct2.user,
            acct2.group,
            queue,
        ]
    )
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        "resource_id": queue.resource_id,
        "resource_snapshot_id": queue.resource_snapshot_id,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        # This group owner does not match the owner of the queue which is
        # the subject of this draft modification.
        acct2.group,
        acct2.user,
    )

    with pytest.raises(e.DraftTargetOwnerMismatch):
        drafts_repo.create_draft_modification(draft)


def test_drafts_create_draft_modification_snapshot_id_mismatch(
    db, drafts_repo, fake_data, account
):

    queue1 = fake_data.queue(account.user, account.group)
    queue2 = fake_data.queue(account.user, account.group)

    db.session.add_all([queue1, queue2])
    db.session.commit()

    toplevel_data = {
        "resource_data": {
            "draft": "stuff",
            "number": 5,
        },
        # the resource_id and resource_snapshot_id don't match up
        "resource_id": queue1.resource_id,
        "resource_snapshot_id": queue2.resource_snapshot_id,
        "base_resource_id": None,
    }

    draft = m.DraftResource(
        "queue",
        toplevel_data,
        account.group,
        account.user,
    )

    with pytest.raises(e.DraftSnapshotIdInvalidError):
        drafts_repo.create_draft_modification(draft)


def test_drafts_get(db, drafts_repo, draft_stuff):

    draft = draft_stuff["draft_resources"][0]

    found_draft = drafts_repo.get(draft.draft_resource_id)
    assert found_draft is not None
    assert found_draft.draft_resource_id == draft.draft_resource_id

    found_draft = drafts_repo.get(draft.draft_resource_id, "job")
    assert found_draft is None

    found_draft = drafts_repo.get(draft.draft_resource_id, "queue", None)
    assert found_draft is not None
    assert found_draft.draft_resource_id == draft.draft_resource_id

    found_draft = drafts_repo.get(
        draft.draft_resource_id,
        "queue",
        draft.creator,
    )
    assert found_draft is not None
    assert found_draft.draft_resource_id == draft.draft_resource_id


def test_drafts_get_one(drafts_repo, draft_stuff):
    draft = draft_stuff["draft_resources"][0]

    found_draft = drafts_repo.get_one(draft.draft_resource_id)
    assert draft == found_draft


def test_drafts_get_one_not_exist(drafts_repo):
    with pytest.raises(e.DraftDoesNotExistError):
        drafts_repo.get_one(999999)


def test_drafts_get_user_not_exist(db, drafts_repo, draft_stuff):

    draft = draft_stuff["draft_mods"][0]

    user = m.User("user", "password", "user@example.org")

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.get(draft, None, user)

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.get(draft.draft_resource_id, "queue", 999999)


def test_drafts_get_user_deleted(db, drafts_repo, draft_stuff):

    # Add an extra user and delete it
    user = m.User("user", "password", "user@example.org")
    draft_stuff["groupa"].members.append(
        m.GroupMember(
            True,
            True,
            True,
            True,
            user,
        )
    )

    user_delete_lock = m.UserLock(user_lock_types.DELETE, user)

    db.session.add_all([user, user_delete_lock])
    db.session.commit()

    draft = draft_stuff["draft_resources"][0]

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.get(draft, None, user)

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.get(draft.draft_resource_id, "queue", user.user_id)


def test_drafts_get_resource(db, drafts_repo, draft_stuff):

    queue = draft_stuff["queues"][1][2]

    found_resource = drafts_repo.get_resource(
        queue.resource_id, DeletionPolicy.NOT_DELETED
    )
    assert found_resource is not None
    assert found_resource.resource_id == queue.resource_id

    found_resource = drafts_repo.get_resource(queue.resource_id, DeletionPolicy.ANY)
    assert found_resource is not None
    assert found_resource.resource_id == queue.resource_id

    found_resource = drafts_repo.get_resource(queue.resource_id, DeletionPolicy.DELETED)
    assert found_resource is None


def test_drafts_get_modification_by_user(drafts_repo, draft_stuff):

    queue = draft_stuff["queues"][1][1]
    draft = draft_stuff["draft_mods"][1]

    found_draft = drafts_repo.get_draft_modification_by_user(
        draft.creator,
        queue,
    )

    assert found_draft is not None
    assert found_draft.draft_resource_id == draft.draft_resource_id

    found_draft = drafts_repo.get_draft_modification_by_user(
        draft.creator.user_id,
        queue.resource_id,
    )

    assert found_draft is not None
    assert found_draft.draft_resource_id == draft.draft_resource_id


def test_drafts_get_modification_by_user_user_not_exist(
    drafts_repo, draft_stuff
):
    queue = draft_stuff["queues"][3][2]

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.get_draft_modification_by_user(
            999999,
            queue,
        )


def test_drafts_get_modification_by_user_user_deleted(
    db, drafts_repo, draft_stuff
):
    queue = draft_stuff["queues"][2][0]

    user2 = m.User("user2", "password", "user2@example.org")
    queue.resource.owner.members.append(
        m.GroupMember(
            True,
            True,
            True,
            True,
            user2,
        )
    )
    db.session.add(user2)
    db.session.commit()

    delete_lock = m.UserLock(user_lock_types.DELETE, user2)
    db.session.add(delete_lock)
    db.session.commit()

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.get_draft_modification_by_user(
            user2,
            queue,
        )


def test_drafts_get_modification_by_user_resource_not_exist(
    drafts_repo, draft_stuff
):
    draft = draft_stuff["draft_mods"][1]

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.get_draft_modification_by_user(
            draft.creator,
            999999,
        )


def test_drafts_get_modification_by_user_resource_deleted(
    db, drafts_repo, draft_stuff
):
    queue = draft_stuff["queues"][1][1]
    draft = draft_stuff["draft_mods"][1]

    delete_lock = m.ResourceLock(resource_lock_types.DELETE, queue.resource)
    db.session.add(delete_lock)
    db.session.commit()

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.get_draft_modification_by_user(
            draft.creator,
            queue,
        )


def test_drafts_get_modification_by_user_not_found(
    db, drafts_repo, draft_stuff
):
    queue = draft_stuff["queues"][0][0]

    user2 = m.User("user2", "password", "user2@example.org")
    queue.resource.owner.members.append(
        m.GroupMember(
            True,
            True,
            True,
            True,
            user2,
        )
    )
    db.session.add(user2)
    db.session.commit()

    found_draft = drafts_repo.get_draft_modification_by_user(user2, queue)
    assert found_draft is None


def test_drafts_get_num_draft_modifications(drafts_repo, draft_stuff):

    num = drafts_repo.get_num_draft_modifications(draft_stuff["queues"][0][0].resource)

    assert num == 1

    num = drafts_repo.get_num_draft_modifications(draft_stuff["queues"][0][0])

    assert num == 1

    num = drafts_repo.get_num_draft_modifications(
        draft_stuff["queues"][0][0].resource_id
    )

    assert num == 1


def test_drafts_get_num_draft_modifications_except(drafts_repo, draft_stuff):

    # alpha created the groupa draft mods, so excluding him, there should be
    # none found.
    num = drafts_repo.get_num_draft_modifications(
        draft_stuff["queues"][0][0].resource, except_user=draft_stuff["alpha"]
    )

    assert num == 0

    num = drafts_repo.get_num_draft_modifications(
        draft_stuff["queues"][0][0].resource, except_user=draft_stuff["alpha"].user_id
    )

    assert num == 0

    # excluding a different user, 1 should be found
    num = drafts_repo.get_num_draft_modifications(
        draft_stuff["queues"][0][0].resource, except_user=draft_stuff["dixon"]
    )

    assert num == 1

    num = drafts_repo.get_num_draft_modifications(
        draft_stuff["queues"][0][0].resource, except_user=draft_stuff["dixon"].user_id
    )

    assert num == 1


def test_drafts_get_by_filters_draft_type(drafts_repo, draft_stuff):

    # Alannah made a draft resource but Bria made a draft modification
    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.RESOURCE,
        "queue",
        draft_stuff["alannah"],
    )

    assert len(drafts) == 1
    assert num == 1

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.RESOURCE,
        "queue",
        draft_stuff["bria"],
    )

    assert len(drafts) == 0
    assert num == 0

    # Switching to looking for modifications, we should now not find any for
    # Alannah, but find one for Bria
    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.MODIFICATION,
        "queue",
        draft_stuff["alannah"],
    )

    assert len(drafts) == 0
    assert num == 0

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.MODIFICATION,
        "queue",
        draft_stuff["bria"],
    )

    assert len(drafts) == 1
    assert num == 1

    # with ANY, we should find both.
    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.ANY,
        "queue",
        draft_stuff["alannah"],
    )

    assert len(drafts) == 1
    assert num == 1

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.ANY,
        "queue",
        draft_stuff["bria"],
    )

    assert len(drafts) == 1
    assert num == 1


def test_drafts_get_by_filters_resource_type(drafts_repo, draft_stuff):

    # Same as one of the above queries which returned 1 result, but with
    # resource_type changed to "job".  This should return no results.
    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.RESOURCE, "job", draft_stuff["alannah"]
    )

    assert len(drafts) == 0
    assert num == 0


def test_drafts_get_by_filters_group(drafts_repo, draft_stuff):

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.RESOURCE,
        "queue",
        draft_stuff["alannah"],
        # be explicit about the group
        draft_stuff["groupa"],
    )

    assert len(drafts) == 1
    assert num == 1

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.RESOURCE,
        "queue",
        draft_stuff["alannah"],
        # alannah is not in this group
        draft_stuff["groupb"],
    )

    assert len(drafts) == 0
    assert num == 0


def test_drafts_get_by_filters_paging(drafts_repo, draft_stuff):

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.ANY,
        "queue",
        draft_stuff["dell"],
        None,
        None,
        0,
        4,
    )

    assert len(drafts) == 4
    assert num == 11

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.ANY,
        "queue",
        draft_stuff["dell"],
        None,
        None,
        8,
        4,
    )

    assert len(drafts) == 3
    assert num == 11


def test_drafts_get_by_filters_base_resource(drafts_repo, draft_stuff):

    drafts, num = drafts_repo.get_by_filters_paged(
        DraftType.ANY,
        "queue",
        draft_stuff["dell"],
        None,
        draft_stuff["base_resource"].resource_id,
    )

    assert len(drafts) == 10
    assert num == 10


def test_drafts_get_by_filters_base_resource_not_found(drafts_repo, draft_stuff):
    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.get_by_filters_paged(
            DraftType.ANY,
            "queue",
            draft_stuff["abi"],
            None,
            # bad base resource ID
            999999,
        )


def test_drafts_get_by_filters_base_resource_deleted(db, drafts_repo, draft_stuff):

    queue_resource = draft_stuff["queues"][0][0].resource

    delete_lock = m.ResourceLock(resource_lock_types.DELETE, queue_resource)
    db.session.add(delete_lock)
    db.session.commit()

    with pytest.raises(e.EntityDeletedError):
        drafts_repo.get_by_filters_paged(
            DraftType.ANY,
            "queue",
            draft_stuff["abi"],
            None,
            # deleted base resource ID
            queue_resource.resource_id,
        )


def test_drafts_update(db, drafts_repo, draft_stuff):

    draft = draft_stuff["draft_mods"][0]
    orig_ts = draft.last_modified_on

    drafts_repo.update(draft, {"draft": "updated", "number": 6})
    db.session.commit()

    assert draft.last_modified_on > orig_ts

    check_draft = drafts_repo.get(draft.draft_resource_id)
    assert check_draft.payload["resource_data"]["draft"] == "updated"


def test_drafts_update_not_exist(db, drafts_repo):

    with pytest.raises(e.DraftDoesNotExistError):
        drafts_repo.update(999999, {"draft": "updated", "number": 6})


def test_drafts_update_modification_snapshot(db, drafts_repo, draft_stuff):
    draft = draft_stuff["draft_mods"][0]
    queue = draft_stuff["queues"][0][1]

    updated_draft = drafts_repo.update(
        draft,
        {"draft": "updated", "number": 6},
        queue,
    )
    db.session.commit()

    assert updated_draft.payload["resource_snapshot_id"] == draft_stuff["queues"][0][1].resource_snapshot_id


def test_drafts_update_modification_snapshot_not_modification(db, drafts_repo, draft_stuff):
    # trying to update the resource_snapshot_id on a draft resource doesn't
    # make any sense.
    draft = draft_stuff["draft_resources"][0]
    queue = draft_stuff["queues"][0][1]

    with pytest.raises(e.DraftModificationRequiredError):
        drafts_repo.update(
            draft,
            {"draft": "updated", "number": 6},
            queue,
        )


def test_drafts_update_modification_snapshot_not_exist(db, drafts_repo, draft_stuff):
    draft = draft_stuff["draft_mods"][0]

    with pytest.raises(e.EntityDoesNotExistError):
        drafts_repo.update(
            draft,
            {"draft": "updated", "number": 6},
            999999,
        )


def test_drafts_update_modification_snapshot_wrong_resource(db, drafts_repo, draft_stuff):
    draft = draft_stuff["draft_mods"][0]
    # The above mod is of a different resource, so we aren't allowed to update
    # the snapshot to this one.
    queue = draft_stuff["queues"][1][0]

    with pytest.raises(e.DraftSnapshotIdInvalidError):
        drafts_repo.update(
            draft,
            {"draft": "updated", "number": 6},
            queue,
        )


def test_drafts_delete(drafts_repo, draft_stuff):

    draft_resource = draft_stuff["draft_resources"][0]
    drafts_repo.delete(draft_resource)

    check_draft = drafts_repo.get(draft_resource.draft_resource_id)
    assert check_draft is None

    draft_mod = draft_stuff["draft_mods"][0]
    drafts_repo.delete(draft_mod)

    check_draft = drafts_repo.get(draft_mod.draft_resource_id)
    assert check_draft is None

    # Try delete by ID
    draft_resource_id = draft_stuff["draft_resources"][1].draft_resource_id
    drafts_repo.delete(draft_resource_id)

    check_draft = drafts_repo.get(draft_resource_id)
    assert check_draft is None


def test_drafts_delete_not_found(drafts_repo, draft_stuff, draft_content):
    draft = m.DraftResource(
        "queue",
        draft_content,
        draft_stuff["groupa"],
        draft_stuff["abi"],
    )

    with pytest.raises(e.DraftDoesNotExistError):
        drafts_repo.delete(draft)

    # Try delete by ID
    with pytest.raises(e.DraftDoesNotExistError):
        drafts_repo.delete(999999)


def test_drafts_has_draft_modifications(drafts_repo, draft_stuff):

    snaps = [
        999998,
        draft_stuff["queues"][0][0].resource_id,
        draft_stuff["queues"][1][1].resource_id,
        999999,
    ]

    results = drafts_repo.has_draft_modifications(snaps)
    assert results == set(snaps[1:3])

    results = drafts_repo.has_draft_modifications([])
    assert results == set()


def test_drafts_has_draft_modifications_user(drafts_repo, draft_stuff):

    snaps = [
        999998,
        draft_stuff["queues"][0][0].resource_id,
        draft_stuff["queues"][1][1],
        999999,
    ]

    results = drafts_repo.has_draft_modifications(snaps, draft_stuff["bria"])
    assert results == {
        draft_stuff["queues"][1][1].resource_id,
    }

    results = drafts_repo.has_draft_modifications(snaps, draft_stuff["bria"].user_id)
    assert results == {draft_stuff["queues"][1][1].resource_id}


def test_drafts_has_draft_modification(drafts_repo, draft_stuff):

    result = drafts_repo.has_draft_modification(draft_stuff["queues"][2][2])

    assert result


def test_drafts_has_draft_modification_user(drafts_repo, draft_stuff):
    result = drafts_repo.has_draft_modification(
        draft_stuff["queues"][2][2], draft_stuff["cydney"]
    )

    assert result

    result = drafts_repo.has_draft_modification(
        draft_stuff["queues"][2][2], draft_stuff["derick"]
    )

    assert not result
