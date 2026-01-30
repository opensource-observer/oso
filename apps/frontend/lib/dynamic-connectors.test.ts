import { validateDynamicConnector } from "@/lib/dynamic-connectors";

describe("validateDynamicConnector", () => {
  it("validates a valid postgres connector", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__postgres_db",
        "postgresql",
        {
          "connection-url": "jdbc:postgresql://localhost:5432/mydb",
          "connection-user": "user",
        },
        {
          "connection-password": "password123",
        },
        "myorg",
      ),
    ).not.toThrow();
  });

  it("validates a valid gsheets connector", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__sheets",
        "gsheets",
        {
          "metadata-sheet-id": "abc123",
        },
        {
          "credentials-key": "key123",
        },
        "myorg",
      ),
    ).not.toThrow();
  });

  it("validates a valid bigquery connector", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__bq",
        "bigquery",
        {
          "project-id": "my-project",
        },
        {
          "credentials-key": "key123",
        },
        "myorg",
      ),
    ).not.toThrow();
  });

  it("throws error for invalid connector type", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__invalid",
        "invalid-type" as any,
        {},
        {},
        "myorg",
      ),
    ).toThrow("Invalid connector type");
  });

  it("throws error when connector name does not start with org name", () => {
    expect(() =>
      validateDynamicConnector(
        "wrongorg__postgres",
        "postgresql",
        {
          "connection-url": "jdbc:postgresql://localhost:5432/mydb",
          "connection-user": "user",
        },
        {
          "connection-password": "password123",
        },
        "myorg",
      ),
    ).toThrow("Connector name must start with the organization name");
  });

  it("throws error for missing required config fields", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__postgres",
        "postgresql",
        {
          "connection-user": "user",
        },
        {
          "connection-password": "password123",
        },
        "myorg",
      ),
    ).toThrow("Missing required config fields");
  });

  it("throws error for missing required credentials fields", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__postgres",
        "postgresql",
        {
          "connection-url": "jdbc:postgresql://localhost:5432/mydb",
          "connection-user": "user",
        },
        {},
        "myorg",
      ),
    ).toThrow("Missing required credentials fields");
  });

  it("throws error when config value contains single quotes", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__postgres",
        "postgresql",
        {
          "connection-url": "jdbc:postgresql://localhost:5432/my'db",
          "connection-user": "user",
        },
        {
          "connection-password": "password123",
        },
        "myorg",
      ),
    ).toThrow("contains invalid characters (quotes)");
  });

  it("throws error when config value contains double quotes", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__postgres",
        "postgresql",
        {
          "connection-url": 'jdbc:postgresql://localhost:5432/my"db',
          "connection-user": "user",
        },
        {
          "connection-password": "password123",
        },
        "myorg",
      ),
    ).toThrow("contains invalid characters (quotes)");
  });

  it("throws error when credentials value contains backticks", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__postgres",
        "postgresql",
        {
          "connection-url": "jdbc:postgresql://localhost:5432/mydb",
          "connection-user": "user",
        },
        {
          "connection-password": "pass`word",
        },
        "myorg",
      ),
    ).toThrow("contains invalid characters (quotes)");
  });

  it("throws error when credentials value contains single quotes", () => {
    expect(() =>
      validateDynamicConnector(
        "myorg__gsheets",
        "gsheets",
        {
          "metadata-sheet-id": "abc123",
        },
        {
          "credentials-key": "key'123",
        },
        "myorg",
      ),
    ).toThrow("contains invalid characters (quotes)");
  });
});
