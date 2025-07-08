# create a graph representing every table, and what tables it can join to
# write a traversal that finds all possible join paths between tables

# iterate through and build the prompts for all join paths
# need to build some way to get unique entities names to reference as well
# each join paths should also create unique prompts for the different types of NL queries
# store them as batches

# each step should involve validation after the fact as well

# 1. LLM generates SQL query that consists of joining all of the tables in the path (model should lean towards ordering in some priority so most relevant items come first + have a limit)
# 2. call pyoso on the SQL query with a limit to get initial results 
# 3. LLM defines a list of columns that represent the columns to retrieve entities from
# 4. for each entity, we randomly grab a row from the results in each specific column
# 5. LLM builds final query based on the query made in #1 and the entities retrieved in #4
# 6. now pass to LLM to generate all of the various NL queries based on the final query

# have to figure out a smart way to generate the different tone NL queries (it varies query to query)

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple

from oso_semantic.definition import Registry
from oso_semantic.register import register_oso_models

# Get models from registry
registry = Registry()
register_oso_models(registry)
models = registry.models

# Build relationships dictionary from the registry
def build_relationships_from_registry(models) -> Dict[Tuple[str, str], str | List[str]]:
    relationships: Dict[Tuple[str, str], str | List[str]] = {}
    
    for model_name, model in models.items():
        for relationship in model.relationships:
            ref_model_name = relationship.ref_model
            
            # Use the join keys - if single key, use string; if multiple, use list
            if len(relationship.source_foreign_key) == 1 and len(relationship.ref_key) == 1:
                join_key = relationship.source_foreign_key[0]
            else:
                join_key = relationship.source_foreign_key
            
            relationships[(model_name, ref_model_name)] = join_key
    
    return relationships

# Build schemas dictionary from the registry
def build_schemas_from_registry(models) -> Dict[str, Dict]:
    schemas = {}
    
    for model_name, model in models.items():
        schema = {
            "description": model.description.strip(),
            "table": model.table,
            "columns": {}
        }
        
        # Add dimensions (columns)
        for dimension in model.dimensions:
            schema["columns"][dimension.name] = {
                "description": dimension.description,
                "column_name": dimension.column_name
            }
        
        # Add measures
        for measure in model.measures:
            schema["columns"][measure.name] = {
                "description": measure.description,
                "query": measure.query
            }
        
        schemas[model_name] = schema
    
    return schemas

def build_graph(rels: Dict[Tuple[str, str], str | List[str]]
                ) -> Dict[str, List[str]]:
    g: Dict[str, List[str]] = defaultdict(list)
    for (a, b) in rels:
        g[a].append(b)
        g[b].append(a)   
    return g

def dfs(start: str, path: list[str], seen: Set[tuple[str, ...]], out: List[Tuple[str, ...]], graph: Dict[str, List[str]]):
    curr = tuple(path)
    if curr not in seen:
        seen.add(curr)
        out.append(curr)

    for next in graph[start]:
        if next not in path:
            dfs(next, path + [next], seen, out, graph)

def enumerate_join_paths(graph: Dict[str, List[str]]) -> List[Tuple[str, ...]]:
    paths, seen = [], set()
    for root in graph.keys():
        dfs(root, [root], seen, paths, graph)
    return paths

def valid_hop(a: str, b: str, relationships: Dict[Tuple[str, str], str | List[str]]) -> bool:
    return (a, b) in relationships or (b, a) in relationships

def validate_path(path: Tuple[str, ...], relationships: Dict[Tuple[str, str], str | List[str]]) -> bool:
    return all(valid_hop(path[i], path[i + 1], relationships) for i in range(len(path) - 1))
