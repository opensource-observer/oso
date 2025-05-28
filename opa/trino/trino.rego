package trino

public_catalogs := {"iceberg"}
admin_users := {"admin", "sqlmesh", "carl"}

# If the user is in the format `jwt-<org_id>`, allow access if the catalog matches the org_id
# or if the catalog is "iceberg".
user := input.context.identity.user

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

allow if {
	input.action.operation == "ExecuteQuery"
}

allow if {
	startswith(user, "jwt-")
	org_id := substring(user, count("jwt-"), -1)

	org_id # Ensure org_id is not empty
	current_catalog_name # Ensure current_catalog_name is not empty

	# Allow if catalog belongs to the org or is a public catalog
	is_org_catalog := startswith(current_catalog_name, org_id)
	is_public_catalog := current_catalog_name in public_catalogs

	some x in [
		is_org_catalog,
		is_public_catalog,
	]
	x
}

# Allow access for admin and sqlmesh users.
allow if {
	user in admin_users
}
