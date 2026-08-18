import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateBadge } from "@/components/state-badge";
import { getPrincipal, getServiceHealth } from "@/lib/domain-api";
import { copyFor, isLocale, type Locale } from "@/lib/i18n";
import { SignInPanel } from "./sign-in-panel";

export default async function OverviewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale = (isLocale(raw) ? raw : "he") as Locale;
  const copy = copyFor(locale);

  // Both calls go through the domain API. The web tier has no database access
  // of its own (ADR-014), so what renders here is exactly what the API's own
  // authorization allowed.
  const [healthy, principal] = await Promise.all([getServiceHealth(), getPrincipal()]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[30px] font-medium leading-[1.38]">{copy.overview}</h1>
        <StateBadge
          state={healthy ? "success" : "danger"}
          label={healthy ? copy.apiReachable : copy.apiUnreachable}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-[20px] font-medium">{copy.serviceHealth}</CardTitle>
        </CardHeader>
        <CardContent className="text-[14px] text-[var(--color-steel)]">
          {copy.identityResolvedServerSide}
        </CardContent>
      </Card>

      {principal.ok ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-[20px] font-medium">
              {copy.signedInAs} {principal.data.displayName}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-[14px] text-[var(--color-steel)]">
              <bdi>{principal.data.email}</bdi>
            </p>

            <div className="flex flex-col gap-2">
              <h2 className="text-[16px] font-medium">{copy.memberships}</h2>
              {principal.data.memberships.length === 0 ? (
                <p className="text-[14px] text-[var(--color-steel)]">{copy.noMemberships}</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {principal.data.memberships.map((membership) => (
                    <li
                      key={`${membership.tenantId}:${membership.roleKey}`}
                      className="flex flex-wrap items-center gap-3 rounded-[var(--radius-md)] border border-[var(--color-ash)] p-3"
                    >
                      <span className="text-[14px]">{membership.tenantName}</span>
                      <StateBadge state="info" label={membership.roleKey} />
                      {/* Identifiers are Latin inside Hebrew text: isolate the
                          run so trailing punctuation does not relocate. */}
                      <bdi className="ms-auto text-[12px] text-[var(--color-fog)]" dir="ltr">
                        {membership.tenantId}
                      </bdi>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <p className="text-[12px] text-[var(--color-fog)]">
              {copy.correlationId}:{" "}
              <bdi dir="ltr">{principal.data.correlationId}</bdi>
            </p>

            <SignInPanel locale={locale} signedIn />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-[20px] font-medium">{copy.notSignedIn}</CardTitle>
          </CardHeader>
          <CardContent>
            <SignInPanel locale={locale} signedIn={false} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
