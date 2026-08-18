/**
 * Server-only client for the domain API.
 *
 * ADR-014: the web tier holds a session and nothing else. It has no database
 * connection string, no service-role key and no storage credential. Every
 * piece of data on a page comes through this module, which runs only on the
 * server — the `server-only` import makes an accidental client import a build
 * error rather than a leak.
 */

import "server-only";
import { cookies } from "next/headers";

export const DEV_SUBJECT_COOKIE = "aione_dev_subject";

const API_BASE = process.env.DOMAIN_API_BASE_URL ?? "http://localhost:8000";

export type Membership = {
  tenantId: string;
  tenantName: string;
  roleKey: string;
};

export type Principal = {
  userId: string;
  email: string;
  displayName: string;
  memberships: Membership[];
  correlationId: string;
};

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; reason: "unauthenticated" | "unreachable" | "error" };

async function authorizationHeader(): Promise<Record<string, string>> {
  // Increment 0 runs the domain API in AUTH_MODE=dev, where the bearer value
  // is the subject. The cookie is httpOnly and set only by the local sign-in
  // action; the real credential arrives with the identity provider decision.
  const store = await cookies();
  const subject = store.get(DEV_SUBJECT_COOKIE)?.value;
  return subject ? { Authorization: `Bearer ${subject}` } : {};
}

async function request<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { Accept: "application/json", ...(await authorizationHeader()) },
      cache: "no-store",
    });

    if (response.status === 401) return { ok: false, status: 401, reason: "unauthenticated" };
    if (!response.ok) return { ok: false, status: response.status, reason: "error" };

    return { ok: true, data: (await response.json()) as T };
  } catch {
    // A failed fetch is reported as unreachable rather than thrown, so the
    // shell can render a degraded state instead of an error page. The reason
    // never carries the upstream detail, which may name internal hosts.
    return { ok: false, status: 0, reason: "unreachable" };
  }
}

async function send<T>(
  path: string,
  method: "POST",
  body: unknown,
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(await authorizationHeader()),
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    if (response.status === 401) return { ok: false, status: 401, reason: "unauthenticated" };
    if (!response.ok) return { ok: false, status: response.status, reason: "error" };

    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, status: 0, reason: "unreachable" };
  }
}

export function getPrincipal(): Promise<ApiResult<Principal>> {
  return request<Principal>("/v1/me");
}

export async function getServiceHealth(): Promise<boolean> {
  const result = await request<{ status: string }>("/health");
  return result.ok && result.data.status === "ok";
}

export type Workspace = {
  id: string;
  customer_id: string;
  customer_name: string;
  name: string;
  state: string;
  primary_locale: string;
  discovery_mode: string | null;
  member_count: number;
  created_at: string;
};

export function listWorkspaces(tenantId: string): Promise<ApiResult<{ workspaces: Workspace[] }>> {
  return request(`/v1/tenants/${tenantId}/workspaces`);
}

/**
 * Workspaces across every tenant the caller belongs to.
 *
 * A person may hold membership of more than one tenant — an AIOne consultant
 * who also works with a partner organisation, for instance — and picking the
 * first membership would silently hide the rest of their work. Each result
 * carries its tenant, because every later call needs it.
 */
export async function listAllWorkspaces(
  memberships: Membership[],
): Promise<{ tenantId: string; tenantName: string; workspace: Workspace }[]> {
  const tenants = [...new Map(memberships.map((m) => [m.tenantId, m])).values()];
  const results = await Promise.all(
    tenants.map(async (membership) => {
      const result = await listWorkspaces(membership.tenantId);
      return result.ok
        ? result.data.workspaces.map((workspace) => ({
            tenantId: membership.tenantId,
            tenantName: membership.tenantName,
            workspace,
          }))
        : [];
    }),
  );
  return results.flat();
}

export type InterviewQuestion = {
  questionKey: string;
  domain: string;
  answerType: string;
  requiredPolicy: string;
  prompt: string;
  helpText: string | null;
  options: { value: string; label: string }[];
  applicable: boolean;
  applicabilityReason: string;
  answered: boolean;
  answer: unknown;
};

export type InterviewPlan = {
  runId: string;
  mode: string;
  definitionVersion: number;
  state: string;
  questions: InterviewQuestion[];
  progress: {
    applicable: number;
    answered: number;
    percent: number;
    outstandingRequired: string[];
    readyForReview: boolean;
  };
  nextQuestionKey: string | null;
};

export function startInterview(
  tenantId: string,
  workspaceId: string,
): Promise<ApiResult<{ run: { id: string; resumed: boolean } }>> {
  return send(`/v1/tenants/${tenantId}/workspaces/${workspaceId}/interviews`, "POST", {
    mode: "quick_start",
  });
}

export function getInterview(
  tenantId: string,
  runId: string,
  locale: "he_IL" | "en_US",
): Promise<ApiResult<InterviewPlan>> {
  return request(`/v1/tenants/${tenantId}/interviews/${runId}?locale=${locale}`);
}

export function submitAnswer(
  tenantId: string,
  runId: string,
  questionKey: string,
  value: unknown,
): Promise<ApiResult<unknown>> {
  return send(`/v1/tenants/${tenantId}/interviews/${runId}/answers`, "POST", {
    questionKey,
    value,
  });
}
