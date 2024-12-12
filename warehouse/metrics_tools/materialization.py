import typing as t

# argument typing: strongly recommended but optional best practice
from sqlmesh import CustomMaterialization  # required
from sqlmesh import Model


class ExportReferenceMaterialization(CustomMaterialization):
    NAME = "export_reference"

    # def create(
    #     self,
    #     table_name: str,
    #     model: Model,
    #     is_table_deployable: bool,
    #     render_kwargs: t.Dict[str, t.Any],
    #     **kwargs: t.Any,
    # ) -> None:
    #     # Custom table/view creation logic.
    #     # Likely uses `self.adapter` methods like `create_table`, `create_view`, or `ctas`.
    #     print("I JUST GOT CALLED BRO")
    #     pass

    def insert(
        self,
        table_name: str,  # ": str" is optional argument typing
        query_or_df: t.Any,
        model: Model,
        is_first_insert: bool,
        **kwargs: t.Any,
    ) -> None:
        print("I JUST GOT CALLED TO INSERT BROHERIM")
        print(f"KWARGS: {kwargs}")

        print(type(query_or_df))

    def delete(self, name: str, **kwargs: t.Any) -> None:
        # Custom table/view deletion logic.
        # Likely uses `self.adapter` methods like `drop_table` or `drop_view`.
        print("I JUST GOT CALLED BRO2")
        pass
