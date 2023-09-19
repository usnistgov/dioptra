allow(actor, action, resource) if
    has_permission(actor, action, resource);

has_permission(user: User, action: String, resource: PrototypeResource) if
    has_relation(user, "group_member", resource.owner) and
    resource.check_permission(user, action) and
    not resource.deleted;

has_permission(user: User, action: String, shared_resource: SharedPrototypeResource) if
    has_relation(user, "group_member", shared_resource.group) and
    shared_resource.check_permission(user, action) and
    not shared_resource.deleted;

has_relation(user: User, "group_member", group: Group) if
    group.check_membership(user);

has_relation(user: User, "group_creator", group: Group) if
    user.id = group.creator_id;

has_relation(user: User, "group_owner", group: Group) if
    user.id = group.owner_id;

has_relation(user: User, "resource_creator", resource: PrototypeResource) if
    user.id = resource.creator_id;

has_relation(group: Group, "resource_owner", resource: PrototypeResource) if
    group.id = resource.owner_id;

actor User {}
actor Group {
    relations = {
        group_member: User,
        group_creator: User,
        group_owner: User
    };
}
resource PrototypeResource {
    relations = {
        resource_creator: User,
        resource_owner: Group
    };
}
resource SharedPrototypeResource {}
