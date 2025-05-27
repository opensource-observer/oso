package trino_test

import data.trino

test_admin_user_allowed if {
	trino.allow with input as {"context": {
		"identity": {"user": "admin"},
		"softwareStack": {"trinoVersion": "434"},
	}}
}

test_sqlmesh_user_allowed if {
	trino.allow with input as {"context": {
		"identity": {"user": "sqlmesh"},
		"softwareStack": {"trinoVersion": "434"},
	}}
}

test_allow_public_catalog_allowed if {
	trino.allow with input as {
		"context": {
			"identity": {"user": "jwt-some-id"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "iceberg",
				"schemaName": "example_schema",
				"tableName": "example_table",
			}},
		},
	}
}

test_allow_private_catalog_allowed if {
	trino.allow with input as {
		"context": {
			"identity": {"user": "jwt-some-id"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "some-id_catalog",
				"schemaName": "example_schema",
				"tableName": "example_table",
			}},
		},
	}
}

test_allow_private_catalog_denied if {
	not trino.allow with input as {
		"context": {
			"identity": {"user": "jwt-some-id"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "example_catalog",
				"schemaName": "example_schema",
				"tableName": "example_table",
			}},
		},
	}
}

test_allow_anonymous_denied if {
	not trino.allow with input as {"context": {
		"identity": {"user": ""},
		"softwareStack": {"trinoVersion": "434"},
	}}
}
