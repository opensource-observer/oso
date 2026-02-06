package trino

parse_user(user) := {"prefix": prefix, "org_name": org_name, "org_id": org_id} if {
	split_user := split(user, "-")
	prefix = split_user[0]
	org_name = split_user[1]
	org_id = split_user[2]
}

read_user(parsed_user) if {
	some x in [
		parsed_user.prefix == "ro",
		parsed_user.prefix == "rw",
	]
	x
}

read_and_write_user(parsed_user) if {
	parsed_user.prefix == "rw"
}

public_catalogs := {"iceberg"}
admin_users := {"admin", "sqlmesh", "carl"}
read_operations := {
	"SelectFromColumns", "AccessCatalog", "FilterCatalogs", "FilterTables",
	"FilterColumns", "ShowSchemas", "FilterSchemas", "ShowTables",
	"ShowColumns",
}

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

default is_user_shared_access := false

is_user_shared_access if {
	current_catalog_name == "user_shared"
	not current_schema_name
}

is_user_shared_access if {
	current_catalog_name == "user_shared"
	current_schema_name == "information_schema"
}

default is_user_shared_schema := false

is_user_shared_schema if {
	current_catalog_name == "user_shared"
	startswith(
		current_schema_name,
		concat("", ["org_", parsed_user.org_id]),
	)
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
	read_user(parsed_user)

	parsed_user.org_id # Ensure org_name_id is not empty
	parsed_user.org_name # Ensure org_name_id is not empty
	current_catalog_name # Ensure current_catalog_name is not empty

	input.action.operation in read_operations # Only read actions allowed

	# Allow if catalog/schema belongs to the org or is a public catalog
	# Org catalogs are in the format: {org_name}__{name}
	# Org schemas are in the format: org_{org_id}__{dataset_id}
	some x in [
		is_org_catalog,
		is_user_shared_access,
		is_user_shared_schema,
		is_public_catalog,
	]
	x
}

# Write user access to catalogs.
# Write users can only write to the user_shared catalog within their org schema.
allow if {
	read_and_write_user(parsed_user)

	parsed_user.org_id # Ensure org_name_id is not empty
	parsed_user.org_name # Ensure org_name_id is not empty
	current_catalog_name # Ensure current_catalog_name is not empty

	# any action allowed

	is_user_shared_schema # Ensure schema belongs to the org
}

# For writes, we need to query the system catalog.
allow if {
	read_and_write_user(parsed_user)
	current_catalog_name == "system"
}
