FROM python:alpine3.22

RUN pip install --no-cache-dir uv
ENV MCP_TRANSPORT=stdio

WORKDIR /app
COPY warehouse/oso_mcp/ /app

RUN sed -i '/pyoso = { workspace = true }/d' pyproject.toml

RUN uv sync
ENV PATH="/app/.venv/bin:${PATH}"

ENTRYPOINT ["oso_mcp"]
CMD ["serve"]

