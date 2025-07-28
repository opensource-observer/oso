## Development Practices

- Start with minimal, lean implementations focused on proof-of-concept
- Prefer extending existing patterns over implementing from scratch
- Use defensive programming for data validation and external API calls
- Include structured logging with appropriate levels (debug, info, warn, error)
- Create focused, single-purpose functions and classes
- Use type hints and docstrings for public interfaces
- Write tests for data transformations and business logic
- Follow existing code patterns and architectural decisions
- Use `uv` for Python package management
- Prefer SQLMesh SQL models for data transformations over custom Python scripts

## Python & Data Engineering

- Use pandas for data manipulation when appropriate
- Follow PEP 8 style guidelines
- Use dataclasses or Pydantic models for structured data
- Implement proper error handling for database connections and API calls
- Use environment variables for configuration
- Validate data schemas at boundaries (API inputs/outputs, file imports)
- Write integration tests for database queries and external service calls

## Git Operations

- Use `git restore <filename>` to discard working directory changes
- Use `git reset --soft HEAD~1` to undo last commit while keeping changes staged
- Always create feature branches from `main` branch
- Write descriptive commit messages following conventional commits format
- Run tests and linting before committing changes

## External Resources & APIs

- Validate external API responses and handle rate limiting
- Use environment variables for API keys and sensitive configuration
- Implement retry logic with exponential backoff for external calls
- Cache external API responses when appropriate
- Document API dependencies and required permissions

## Communication & Documentation

- Use clear, technical language appropriate for data engineering context
- Include code examples in explanations when helpful
- Reference specific file paths and line numbers when discussing code
- Ask for clarification on data requirements and business logic
- Document data models, transformations, and API interfaces
- Use markdown formatting for structured responses
