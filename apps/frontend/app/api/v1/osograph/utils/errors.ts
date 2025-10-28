import { GraphQLError } from "graphql";

export enum ErrorCode {
  UNAUTHENTICATED = "UNAUTHENTICATED",
  FORBIDDEN = "FORBIDDEN",
  UNAUTHORIZED = "UNAUTHORIZED",

  BAD_USER_INPUT = "BAD_USER_INPUT",
  VALIDATION_ERROR = "VALIDATION_ERROR",
  NOT_FOUND = "NOT_FOUND",
  CONFLICT = "CONFLICT",
  ALREADY_EXISTS = "ALREADY_EXISTS",

  INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR",
  DATABASE_ERROR = "DATABASE_ERROR",
  EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR",
}

const USER_FRIENDLY_MESSAGES: Record<ErrorCode, string> = {
  [ErrorCode.UNAUTHENTICATED]:
    "Authentication required. Please sign in to continue.",
  [ErrorCode.FORBIDDEN]:
    "Access denied. You don't have permission to perform this action.",
  [ErrorCode.UNAUTHORIZED]:
    "Access denied. You don't have permission to access this resource.",
  [ErrorCode.BAD_USER_INPUT]:
    "Invalid input. Please check your data and try again.",
  [ErrorCode.VALIDATION_ERROR]:
    "Validation failed. Please check the provided information and try again.",
  [ErrorCode.NOT_FOUND]: "Not found. The requested resource does not exist.",
  [ErrorCode.CONFLICT]:
    "Conflict. This action cannot be completed due to a conflict with existing data.",
  [ErrorCode.ALREADY_EXISTS]:
    "Already exists. The resource you're trying to create already exists.",
  [ErrorCode.INTERNAL_SERVER_ERROR]:
    "Server error. Something went wrong on our end. Please try again later.",
  [ErrorCode.DATABASE_ERROR]:
    "Database error. We're experiencing technical difficulties. Please try again later.",
  [ErrorCode.EXTERNAL_SERVICE_ERROR]:
    "Service unavailable. An external service is currently unavailable. Please try again later.",
};

export interface ErrorExtensions extends Record<string, unknown> {
  code: ErrorCode;
  userMessage: string;
  rawErrorMessage?: string;
  field?: string;
  validationErrors?: Array<{
    path: string[];
    message: string;
  }>;
  metadata?: Record<string, unknown>;
}

export function createError(
  code: ErrorCode,
  rawErrorMessage?: string,
  extensions?: Partial<Omit<ErrorExtensions, "code" | "userMessage">>,
): GraphQLError {
  const userMessage = USER_FRIENDLY_MESSAGES[code];

  return new GraphQLError(userMessage, {
    extensions: {
      code,
      userMessage,
      rawErrorMessage,
      ...extensions,
    } as ErrorExtensions,
  });
}

export const AuthenticationErrors = {
  notAuthenticated: () =>
    createError(ErrorCode.UNAUTHENTICATED, "User is not authenticated"),

  notAuthorized: () => createError(ErrorCode.FORBIDDEN, "User not authorized"),

  invalidToken: () =>
    createError(ErrorCode.UNAUTHENTICATED, "Invalid authentication token"),
} as const;

export const ResourceErrors = {
  notFound: (resource: string, identifier?: string) =>
    createError(
      ErrorCode.NOT_FOUND,
      identifier
        ? `${resource} not found: ${identifier}`
        : `${resource} not found`,
    ),

  alreadyExists: (resource: string, identifier?: string) =>
    createError(
      ErrorCode.ALREADY_EXISTS,
      identifier
        ? `${resource} already exists: ${identifier}`
        : `${resource} already exists`,
    ),

  conflict: (message: string) => createError(ErrorCode.CONFLICT, message),
} as const;

export const ValidationErrors = {
  invalidInput: (field?: string, details?: string) =>
    createError(ErrorCode.BAD_USER_INPUT, details, { field }),

  validationFailed: (
    errors: Array<{ path: string[]; message: string }>,
    rawErrorMessage?: string,
  ) =>
    createError(ErrorCode.VALIDATION_ERROR, rawErrorMessage, {
      validationErrors: errors,
    }),

  missingField: (field: string) =>
    createError(ErrorCode.BAD_USER_INPUT, `Required field missing: ${field}`, {
      field,
    }),
} as const;

export const ServerErrors = {
  internal: (rawErrorMessage?: string) =>
    createError(ErrorCode.INTERNAL_SERVER_ERROR, rawErrorMessage),

  database: (rawErrorMessage?: string) =>
    createError(ErrorCode.DATABASE_ERROR, rawErrorMessage),

  externalService: (rawErrorMessage?: string) =>
    createError(ErrorCode.EXTERNAL_SERVICE_ERROR, rawErrorMessage),

  storage: (rawErrorMessage?: string) =>
    createError(ErrorCode.EXTERNAL_SERVICE_ERROR, rawErrorMessage),
} as const;

export const OrganizationErrors = {
  notMember: () =>
    createError(ErrorCode.FORBIDDEN, "User is not a member of organization"),

  notFound: () => createError(ErrorCode.NOT_FOUND, "Organization not found"),

  cannotRemoveSelf: () =>
    createError(
      ErrorCode.BAD_USER_INPUT,
      "Cannot remove yourself from organization",
    ),
} as const;

export const InvitationErrors = {
  notFound: () => createError(ErrorCode.NOT_FOUND, "Invitation not found"),

  alreadyAccepted: () =>
    createError(ErrorCode.CONFLICT, "Invitation has already been accepted", {
      metadata: { status: "accepted" },
    }),

  expired: () =>
    createError(ErrorCode.CONFLICT, "Invitation has expired", {
      metadata: { status: "expired" },
    }),

  revoked: () =>
    createError(ErrorCode.CONFLICT, "Invitation has been revoked", {
      metadata: { status: "revoked" },
    }),

  alreadyExists: () =>
    createError(
      ErrorCode.ALREADY_EXISTS,
      "An active invitation already exists",
    ),

  wrongRecipient: () =>
    createError(
      ErrorCode.FORBIDDEN,
      "This invitation was sent to a different email address",
    ),

  cannotInviteSelf: () =>
    createError(
      ErrorCode.BAD_USER_INPUT,
      "Cannot invite yourself to organization",
    ),
} as const;

export const UserErrors = {
  notFound: () => createError(ErrorCode.NOT_FOUND, "User not found"),

  profileNotFound: () =>
    createError(ErrorCode.NOT_FOUND, "User profile not found"),

  emailNotFound: () =>
    createError(ErrorCode.BAD_USER_INPUT, "User email not found"),

  noFieldsToUpdate: () =>
    createError(ErrorCode.BAD_USER_INPUT, "No fields provided to update"),
} as const;

export const NotebookErrors = {
  notFound: () => createError(ErrorCode.NOT_FOUND, "Notebook not found"),
} as const;
