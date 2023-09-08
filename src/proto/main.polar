actor User {}

resource Dioptra_Resource {
  permissions = ["create","read", "update", "delete", "share-read", "share-write"];
  roles = ["reader", "writer", "share-reader", "share-writer"];

  relations = { owner: Group, shared_with: Group};
  #relations = { owner: Group, shared_with: Group, shared_with_writer: Group};

  #base level permissions
  "read" if "reader" on "owner";
  
  "update" if "writer" on "owner";
  "create" if "writer" on "owner";

  "share-read" if "share-reader" on "owner";
  "share-write" if "share-writer" on "owner";
  #"delete" if "owner";

  #sharing perms, sharing with the whole group and defaulting to group perms
  "read" if "reader" on "shared_with";
  "update" if "writer" on "shared_with";

  # #sharing perms, sharing with the whole group but only with a certain role
  # "read" if "reader" on "shared_with";
  # "update" if "writer" on "shared_with_writer";
}

resource Group {
  permissions = ["create","read", "update", "delete", "share-read",
    "share-write", "revoke-read", "revoke-write"];
  
  roles = ["admin", "reader", "writer", "share-reader", "share-writer"];

  #base level permissions
  "read" if "reader";
  "create" if "writer";
  "update" if "writer";
  
  #sharing permisions
  "share-read" if "share-reader";
  "share-write" if "share-writer";

  #basic inheritance
  "delete" if "admin";
  "reader" if "admin";
  "writer" if "admin";
 
  "share-reader" if "admin";
  "share-writer" if "admin";
}

has_relation(group: Group, "owner", resource: Dioptra_Resource) if
    group = resource.owner;

has_relation(group: Group, "shared_with", resource: Dioptra_Resource) if
    group in resource.shared_with;
  
# has_relation(group: Group, "shared_with_writer", resource: Dioptra_Resource) if
#     group in resource.shared_with_writer;

# This rule tells Oso how to fetch roles for a repository
has_role(actor: User, role_name: String, resource: Dioptra_Resource) if
  role in actor.roles and
  role_name = role.name and
  resource = role.resource;

has_role(actor: User, role_name: String, group: Group) if
  role in actor.roles and
  role_name = role.name and
  group = role.resource;

#public resource
has_permission(_actor: User, "read", resource: Dioptra_Resource) if
  resource.is_public;

allow(actor, action, resource) if
  has_permission(actor, action, resource);

# This might allow for getting the owning group whenever passing a resouce
# has_role(actor:User,role_name: String, resource: Dioptra_Resource ) if
#   user in resource.owner.shared_with and
#   role in actor.roles and
#   role_name = role.name and
#   group=role.resource



