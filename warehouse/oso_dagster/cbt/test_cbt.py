from sqlmesh.core.dialect import parse_one

from .mesh import DictResolver, render_with_sqlmesh


def test_render_with_sqlmesh():
    resolver = DictResolver(
        {
            "table1": {
                "id": "integer",
                "name": "varchar",
            },
            "table2": {
                "id": "integer",
                "table1_id": "integer",
                "name": "varchar",
            },
        }
    )
    rendered = render_with_sqlmesh(
        """
    SELECT @STAR(table1, t) FROM @VAR('table')
    """,
        dialect="postgres",
        # schema_loader=LazySchema(resolver),
        schema_loader=resolver,
        variables={"table": "table1"},
    )
    assert rendered == parse_one(
        """
    SELECT 
        CAST("t"."id" AS INT) AS "id", 
        CAST("t"."name" AS VARCHAR) AS "name" 
    FROM "table1" AS "table1"
    """
    )
