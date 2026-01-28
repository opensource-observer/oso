package trino

parse_user(user) := {"prefix": prefix, "org_name": org_name, "org_id": org_id} if {
	split_user := split(user, "-")
	prefix = split_user[0]
	org_name = split_user[1]
	org_id = split_user[2]
}

read_only_user(parsed_user) if {
	parsed_user.prefix == "ro"
}

public_catalogs := {"iceberg"}
admin_users := {"admin", "sqlmesh", "carl"}

# If the user is in the format `ro-<org_name>-<org_id>`, allow access if the catalog
# matches the org_name or if the catalog is "iceberg".
user := input.context.identity.user
parsed_user := parse_user(user)

# Determine the catalog name by checking potential paths
# If input.action.resource.catalog.name exists, use it.
# Else if input.action.resource.table.catalogName exists, use it.
# Otherwise, current_catalog_name will be undefined.
current_catalog_name := name if {
	name := input.action.resource.catalog.name
} else := name if {
	name := input.action.resource.table.catalogName
} else := name if {
	name := input.action.resource.schema.catalogName
}

current_schema_name := name if {
	name := input.action.resource.schema.schemaName
} else := name if {
	name := input.action.resource.table.schemaName
}

default is_org_catalog := false

is_org_catalog if {
	startswith(current_catalog_name, concat(
		"",
		[parsed_user.org_name, "__"],
	))
}

default is_org_schema := false

is_org_schema if {
	current_catalog_name == "user_shared"
	startswith(current_schema_name, concat(
		"",
		["org_", parsed_user.org_id],
	))
}

default is_public_catalog := false

is_public_catalog if {
	current_catalog_name in public_catalogs
}

allow if {
	input.action.operation == "ExecuteQuery"
}

# Allow access for admin and sqlmesh users.
allow if {
	user in admin_users
}

# Read user access to catalogs
allow if {
	read_only_user(parsed_user)

	parsed_user.org_id # Ensure org_name_id is not empty
	parsed_user.org_name # Ensure org_name_id is not empty
	current_catalog_name # Ensure current_catalog_name is not empty

	# Allow if catalog/schema belongs to the org or is a public catalog
	# Org catalogs are in the format: {org_name}__{name}
	# Org schemas are in the format: org_{org_id}__{dataset_id}
	some x in [
		is_org_catalog,
		is_org_schema,
		is_public_catalog,
	]
	x
}

# FOR BACKWARDS COMPATIBILITY ONLY
# When trying to query a private catalog
allow if {
	startswith(user, "jwt-")
	org_id := substring(user, count("jwt-"), -1)

	org_id # Ensure org_id is not empty
	current_catalog_name # Ensure current_catalog_name is not empty

	# Allow if catalog belongs to the org or is a public catalog
	is_org_catalog := startswith(current_catalog_name, concat("", [org_id, "__"]))
	is_public_catalog := current_catalog_name in public_catalogs

	some x in [
		is_org_catalog,
		is_public_catalog,
	]
	x
}