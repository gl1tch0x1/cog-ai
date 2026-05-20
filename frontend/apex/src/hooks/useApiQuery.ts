import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { useAuth } from "./useAuth";

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

/**
 * Authenticated API query hook with 401 interception and token expiry check.
 */
export function useApiQuery<T>(
  key: string[],
  path: string,
  options?: Omit<UseQueryOptions<T>, "queryKey" | "queryFn">
) {
  const { token, logout } = useAuth();

  // Pre-check: if token is expired, logout immediately
  const valid = !!token && !isTokenExpired(token);

  return useQuery<T>({
    queryKey: key,
    enabled: valid,
    queryFn: async () => {
      if (!token || isTokenExpired(token)) {
        logout();
        throw new Error("Token expired");
      }
      const res = await fetch(`/api${path}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        logout();
        throw new Error("Unauthorized");
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `API error ${res.status}`);
      }
      return res.json();
    },
    retry: (count, error) => {
      // Don't retry auth errors
      if (error?.message === "Unauthorized" || error?.message === "Token expired") return false;
      return count < 2;
    },
    ...options,
  });
}
