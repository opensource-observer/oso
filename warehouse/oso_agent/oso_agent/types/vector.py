import abc
import typing as t

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import BaseNode


class MultiVectorStoreIndexProtocol(t.Protocol):
    """A protocol for retrieving context from multiple vector stores. Generally,
    each vector store is for a different table."""

    def has_index(self, index_name: str) -> bool:
        """Check if the index exists in the vector store."""
        ...

    def get_index(self, index_name: str) -> VectorStoreIndex:
        """Get the vector store index by name."""
        ...

    def as_retrievers(self, index_names: t.Optional[list[str]] = None) -> dict[str, BaseRetriever]:
        """Get the vector store indices as retrievers."""
        ...

    async def create_index_from_nodes(self, index_name: str, node: list[BaseNode]) -> VectorStoreIndex:
        """Create a new index in the vector store."""
        ...



class MultiVectorStoreIndex(abc.ABC):
    """A base class that implements the MultiVectorStoreIndexProtocol
    for managing multiple vector store indices."""

    def __init__(self):
        self.indices: dict[str, VectorStoreIndex] = {}

    def has_index(self, index_name: str) -> bool:
        """Check if the index exists in the vector store."""
        return index_name in self.indices
    
    def get_index(self, index_name: str) -> VectorStoreIndex:
        """Get the vector store index by name."""
        if not self.has_index(index_name):
            raise ValueError(f"Index '{index_name}' does not exist.")
        return self.indices[index_name]
    
    def as_retrievers(self, index_names: t.Optional[list[str]] = None) -> dict[str, BaseRetriever]:
        """Get the vector store indices as retrievers."""
        if index_names is None:
            return {name: index.as_retriever() for name, index in self.indices.items()}
        
        for name in index_names:
            if not self.has_index(name):
                raise ValueError(f"Index '{name}' does not exist.")
        return {name: self.get_index(name).as_retriever() for name in index_names}
    
    @abc.abstractmethod
    async def create_index_from_nodes(self, index_name: str, nodes: list[BaseNode]) -> VectorStoreIndex:
        """Create a new index in the vector store."""
        raise NotImplementedError("Subclasses must implement this method.")
    

