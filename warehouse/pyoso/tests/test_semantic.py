import unittest

from pyoso.semantic import SemanticTableResponse, map_to_semantic_table_response


class TestMapToSemanticTableResponse(unittest.TestCase):

    def test_basic_table_mapping(self):
        """Test mapping a basic table with name and description only."""
        table_data = {"name": "users", "description": "User information table"}

        result = map_to_semantic_table_response(table_data)

        self.assertEqual(result.name, "users")
        self.assertEqual(result.description, "User information table")
        self.assertEqual(len(result.columns), 0)
        self.assertEqual(len(result.relationships), 0)

    def test_complete_table_with_columns_and_relationships(self):
        """Test mapping a complete table with both columns and relationships."""
        table_data = {
            "name": "orders",
            "description": "Customer order information",
            "columns": [
                {"name": "id", "type": "bigint", "description": "Order ID"},
                {
                    "name": "user_id",
                    "type": "bigint",
                    "description": "Foreign key to users table",
                },
            ],
            "relationships": [
                {
                    "sourceColumn": "user_id",
                    "targetTable": "users",
                    "targetColumn": "id",
                }
            ],
        }

        result = map_to_semantic_table_response(table_data)

        self.assertEqual(result.name, "orders")
        self.assertEqual(result.description, "Customer order information")

        # Check columns
        self.assertEqual(len(result.columns), 2)
        self.assertEqual(result.columns[0].name, "id")
        self.assertEqual(result.columns[0].type, "bigint")
        self.assertEqual(result.columns[0].description, "Order ID")

        self.assertEqual(result.columns[1].name, "user_id")
        self.assertEqual(result.columns[1].type, "bigint")
        self.assertEqual(result.columns[1].description, "Foreign key to users table")

        # Check relationships
        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0].source_column, "user_id")
        self.assertEqual(result.relationships[0].target_table, "users")
        self.assertEqual(result.relationships[0].target_column, "id")

    def test_missing_optional_fields(self):
        """Test mapping with missing optional fields defaults to empty strings."""
        table_data = {
            "name": "table",
            "columns": [
                {"name": "id"},  # Missing type and description (optional)
                {"name": "status", "type": "varchar"},  # Missing description (optional)
            ],
        }

        result = map_to_semantic_table_response(table_data)

        # Missing table fields default to empty strings
        self.assertEqual(result.name, "table")
        self.assertEqual(result.description, "")

        # Check columns with missing optional fields default to empty strings
        self.assertEqual(len(result.columns), 2)
        self.assertEqual(result.columns[0].name, "id")
        self.assertEqual(result.columns[0].type, "")
        self.assertEqual(result.columns[0].description, "")

        self.assertEqual(result.columns[1].name, "status")
        self.assertEqual(result.columns[1].type, "varchar")
        self.assertEqual(result.columns[1].description, "")

        # No relationships in this test since all relationship fields are required
        self.assertEqual(len(result.relationships), 0)

    def test_required_fields_validation(self):
        """Test that required fields raise AssertionError when missing."""
        # Test missing table name (required)
        with self.assertRaises(AssertionError) as context:
            map_to_semantic_table_response(
                {
                    "columns": [{"name": "id", "type": "varchar"}]
                    # Missing required table name
                }
            )
        self.assertIn("Table name is required", str(context.exception))

        # Test missing column name (required)
        with self.assertRaises(AssertionError) as context:
            map_to_semantic_table_response(
                {
                    "name": "table",
                    "columns": [{"type": "varchar"}],  # Missing required column name
                }
            )
        self.assertIn("Column name is required", str(context.exception))

        # Test missing relationship source_column (required)
        with self.assertRaises(AssertionError) as context:
            map_to_semantic_table_response(
                {
                    "name": "table",
                    "relationships": [
                        {
                            "targetTable": "users",
                            "targetColumn": "id",
                            # Missing required source_column
                        }
                    ],
                }
            )
        self.assertIn(
            "Source column, target table and target column are required",
            str(context.exception),
        )

        # Test missing relationship target_table (required)
        with self.assertRaises(AssertionError) as context:
            map_to_semantic_table_response(
                {
                    "name": "table",
                    "relationships": [
                        {
                            "sourceColumn": "user_id",
                            "targetColumn": "id",
                            # Missing required target_table
                        }
                    ],
                }
            )
        self.assertIn(
            "Source column, target table and target column are required",
            str(context.exception),
        )

        # Test missing relationship target_column (required)
        with self.assertRaises(AssertionError) as context:
            map_to_semantic_table_response(
                {
                    "name": "table",
                    "relationships": [
                        {
                            "sourceColumn": "user_id",
                            "targetTable": "users",
                            # Missing required target_column
                        }
                    ],
                }
            )
        self.assertIn(
            "Source column, target table and target column are required",
            str(context.exception),
        )

    def test_return_type_and_structure(self):
        """Test that the function returns the correct type and handles minimal data."""
        # Test return type
        result = map_to_semantic_table_response({"name": "test"})
        self.assertIsInstance(result, SemanticTableResponse)
        self.assertIsInstance(result.columns, list)
        self.assertIsInstance(result.relationships, list)

        # Test minimal data (just required name field)
        minimal_result = map_to_semantic_table_response({"name": "minimal_table"})
        self.assertEqual(minimal_result.name, "minimal_table")
        self.assertEqual(minimal_result.description, "")
        self.assertEqual(len(minimal_result.columns), 0)
        self.assertEqual(len(minimal_result.relationships), 0)
