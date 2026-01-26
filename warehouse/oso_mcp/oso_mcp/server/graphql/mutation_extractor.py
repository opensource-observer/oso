"""Extract mutation definitions from GraphQL schema."""

import typing as t

from graphql import GraphQLInputObjectType, GraphQLObjectType, GraphQLSchema

from .pydantic_generator import PydanticModelGenerator
from .types import MutationFilter, MutationInfo


class MutationExtractor:
    """Extract mutation definitions from parsed GraphQL schema."""

    def extract_mutations(
        self,
        schema: GraphQLSchema,
        model_generator: PydanticModelGenerator,
        filters: list[MutationFilter] | None = None,
    ) -> t.List[MutationInfo]:
        """Extract all mutations and generate their Pydantic models.

        Args:
            schema: GraphQL schema
            model_generator: Pydantic model generator
            filters: Optional list of MutationFilter to filter out mutations
        Returns:
            List of mutation information
        """
        mutations = []
        mutation_type = self._get_mutation_type(schema)

        if not mutation_type:
            return mutations

        for field_name, field in mutation_type.fields.items():
            # Get mutation description
            description = field.description or ""

            # Get input type (should be a single argument called 'input')
            input_arg = field.args.get("input")
            if not input_arg:
                # Skip mutations without input argument
                continue

            input_type = input_arg.type
            # Unwrap NonNull if present
            if hasattr(input_type, "of_type"):
                input_type = input_type.of_type

            if not isinstance(input_type, GraphQLInputObjectType):
                # Skip if input is not an input object type
                continue

            # Generate Pydantic model for input
            input_model = model_generator.generate_input_model(input_type)

            # Get return type (payload)
            return_type = field.type
            # Unwrap NonNull if present
            if hasattr(return_type, "of_type"):
                return_type = return_type.of_type

            if not isinstance(return_type, GraphQLObjectType):
                # Skip if return type is not an object type
                continue

            # Generate Pydantic model for payload
            payload_model = model_generator.generate_payload_model(return_type)

            # Extract top-level payload fields
            payload_fields = self._extract_payload_fields(return_type)

            mutation_info = MutationInfo(
                name=field_name,
                description=description,
                input_model=input_model,
                payload_model=payload_model,
                payload_fields=payload_fields,
                graphql_input_type_name=input_type.name,
            )

            # Apply filters if any
            if filters:
                if any(f.should_ignore(mutation_info) for f in filters):
                    continue
            mutations.append(mutation_info)

        return mutations

    def _get_mutation_type(
        self, schema: GraphQLSchema
    ) -> t.Optional[GraphQLObjectType]:
        """Get the Mutation type from schema.

        Args:
            schema: GraphQL schema

        Returns:
            Mutation type or None if not present
        """
        return schema.mutation_type

    def _extract_payload_fields(self, payload_type: GraphQLObjectType) -> t.List[str]:
        """Get top-level and one level deep fields from payload type.

        Args:
            payload_type: GraphQL object type for mutation payload

        Returns:
            List of field names
        """
        return list(payload_type.fields.keys())
