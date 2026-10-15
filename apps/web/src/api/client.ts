export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}
export async function request<T>(
  token: string,
  path: string,
  body?: unknown,
  blob = false,
  method = body === undefined ? "GET" : "POST",
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const result = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      typeof result?.error?.code === "string"
        ? result.error.code
        : "request_failed",
      typeof result?.error?.message === "string"
        ? result.error.message
        : `Request failed (${response.status})`,
    );
  }
  return blob
    ? (response.blob() as Promise<T>)
    : (response.json() as Promise<T>);
}
