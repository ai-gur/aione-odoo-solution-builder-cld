import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateBadge } from "@/components/state-badge";
import { getPrincipal, listAllWorkspaces } from "@/lib/domain-api";
import { copyFor, contractLocale, isLocale, type Locale } from "@/lib/i18n";

/** Workspace states that mean the engagement is still being delivered. */
const IN_DELIVERY = new Set([
  "proposed", "discovering", "clarification_required", "designing",
  "blueprint_review", "approved_for_sandbox", "provisioning", "sandbox_active",
  "customer_review",
]);

function stateTone(state: string): "success" | "caution" | "danger" | "info" | "neutral" {
  if (state === "validation_failed" || state === "revision_required") return "danger";
  if (state === "clarification_required" || state === "suspended") return "caution";
  if (state === "accepted" || state === "operating") return "success";
  if (IN_DELIVERY.has(state)) return "info";
  return "neutral";
}

export default async function WorkspacesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale = (isLocale(raw) ? raw : "he") as Locale;
  const copy = copyFor(locale);

  const principal = await getPrincipal();
  if (!principal.ok) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-[20px] font-medium">{copy.notSignedIn}</CardTitle>
        </CardHeader>
        <CardContent>
          <Link href={`/${locale}`} className="text-[14px] underline">
            {copy.signIn}
          </Link>
        </CardContent>
      </Card>
    );
  }

  const entries = await listAllWorkspaces(principal.data.memberships);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-[30px] font-medium leading-[1.38]">{copy.workspaces}</h1>

      {entries.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-[14px] text-[var(--color-steel)]">
            {copy.noWorkspaces}
          </CardContent>
        </Card>
      ) : (
        <ul className="flex flex-col gap-3">
          {entries.map(({ workspace, tenantName }) => (
            <li key={workspace.id}>
              <Card>
                <CardContent className="flex flex-wrap items-center gap-4 p-4">
                  <div className="flex min-w-0 flex-col gap-1">
                    <Link
                      href={`/${locale}/workspaces/${workspace.id}/interview`}
                      className="text-[16px] font-medium underline-offset-4 hover:underline"
                    >
                      {workspace.name}
                    </Link>
                    <span className="text-[14px] text-[var(--color-steel)]">
                      {workspace.customer_name} · {tenantName}
                    </span>
                  </div>

                  <Link
                    href={`/${locale}/workspaces/${workspace.id}/review`}
                    className="ms-auto text-[14px] underline-offset-4 hover:underline"
                  >
                    {copy.review}
                  </Link>
                  <div className="flex flex-wrap items-center gap-2">
                    {workspace.discovery_mode ? (
                      <StateBadge state="neutral" label={copy.modeLabel[workspace.discovery_mode]} />
                    ) : null}
                    <StateBadge
                      state={stateTone(workspace.state)}
                      label={copy.stateLabel[workspace.state] ?? workspace.state}
                    />
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <p className="text-[12px] text-[var(--color-fog)]">
        {copy.localeNotice} <bdi dir="ltr">{contractLocale(locale)}</bdi>
      </p>
    </div>
  );
}
