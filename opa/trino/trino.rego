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

current_schema_name := name if {
	name := input.action.resource.schema.schemaName
} else := name if {
	name := input.action.resource.table.schemaName
}

allow if {
	input.action.operation == "ExecuteQuery"
}

# Allow access for admin and sqlmesh users.
allow if {
	user in admin_users
}

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

# When trying to query a private replication
allow if {
	input.action.resource.catalog.name == "dynamic"
}

# Allow users to see the schema and tables inside the dynamic catalog
allow if {
	current_catalog_name == "dynamic"
	current_schema_name == "information_schema"
}

# Give permission only to the organization's schema
allow if {
	startswith(user, "jwt-")
	org_id := substring(user, count("jwt-"), -1)

	org_id # Ensure org_id is not empty

	current_catalog_name == "dynamic"
	current_schema_name == org_id
}
