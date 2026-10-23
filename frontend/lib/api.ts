export interface ServiceComponentStatus {
  status: "connected" | "disconnected" | "degraded";
  latency_ms: number | null;
  details: string | null;
  error: string | null;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  environment: string;
  version: string;
  timestamp: string;
  database: ServiceComponentStatus;
  queue: ServiceComponentStatus;
  meta: {
    app_name?: string;
    api_prefix?: string;
    [key: string]: unknown;
  };
}

export interface PingResponse {
  status: string;
  message: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Fetches comprehensive infrastructure health status from the backend API.
 * Real API call - no mocks.
 */
export async function fetchHealthStatus(signal?: AbortSignal): Promise<HealthResponse> {
  const url = `${API_BASE_URL}/api/v1/health`;
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
    cache: "no-store",
    signal,
  });

  if (!response.ok && response.status !== 503) {
    throw new Error(`API returned HTTP ${response.status}: ${response.statusText}`);
  }

  const data: HealthResponse = await response.json();
  return data;
}

/**
 * Lightweight liveness probe to verify connectivity.
 */
export async function fetchPing(signal?: AbortSignal): Promise<PingResponse> {
  const url = `${API_BASE_URL}/api/v1/ping`;
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(`Ping failed with HTTP ${response.status}`);
  }

  return response.json();
}
