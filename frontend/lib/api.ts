const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("trip_token") : null;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.detail || "Não foi possível concluir a ação",
    );
  }
  return response.status === 204 ? ({} as T) : response.json();
}
export async function login(email: string, password: string) {
  const result = await api<{ access_token: string; user: { name: string } }>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) },
  );
  localStorage.setItem("trip_token", result.access_token);
  localStorage.setItem("trip_user", JSON.stringify(result.user));
  return result;
}
export async function registerAccount(data: {
  name: string;
  email: string;
  phone?: string;
  password: string;
}) {
  const result = await api<{ access_token: string; user: { name: string } }>(
    "/auth/register",
    { method: "POST", body: JSON.stringify(data) },
  );
  localStorage.setItem("trip_token", result.access_token);
  localStorage.setItem("trip_user", JSON.stringify(result.user));
  return result;
}
export function logout() {
  localStorage.removeItem("trip_token");
  localStorage.removeItem("trip_user");
  location.href = "/login";
}
