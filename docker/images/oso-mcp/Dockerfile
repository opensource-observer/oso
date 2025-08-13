FROM python:3.12-alpine AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY uv.lock pyproject.toml ./
COPY warehouse/oso_mcp/ ./warehouse/oso_mcp/
COPY warehouse/pyoso/ ./warehouse/pyoso/

WORKDIR /app/warehouse/oso_mcp

RUN uv sync --frozen --no-dev

FROM python:3.12-alpine AS runtime

RUN addgroup -g 1001 -S oso && \
    adduser -S oso -u 1001 -G oso

RUN apk add --no-cache \
    ca-certificates \
    && rm -rf /var/cache/apk/*

ENV MCP_TRANSPORT=stdio

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY --from=builder /app/warehouse/oso_mcp/oso_mcp ./warehouse/oso_mcp/oso_mcp
COPY --from=builder /app/warehouse/oso_mcp/pyproject.toml ./warehouse/oso_mcp/
COPY --from=builder /app/warehouse/pyoso ./warehouse/pyoso

ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app/warehouse/oso_mcp

RUN chown -R oso:oso /app

USER oso

ENTRYPOINT ["oso_mcp"]

CMD ["serve"]
