import Link from "next/link";
import { revalidatePath } from "next/cache";
import { notFound } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateBadge } from "@/components/state-badge";
import {
  getDerived,
  getInterview,
  getPrincipal,
  listAllWorkspaces,
  normaliseInterview,
  startInterview,
  type InterviewQuestion,
} from "@/lib/domain-api";
import { contractLocale, copyFor, isLocale, type Locale } from "@/lib/i18n";

/**
 * Discovery review.
 *
 * The surface where a consultant decides whether the system understood the
 * business. Every conclusion is shown beside the answer it came from, because
 * a requirement whose origin you cannot see is a requirement you cannot
 * usefully review (Discovery §19).
 */

const CONFIDENCE_TONE = {
  green: "success",
  amber: "caution",
  red: "danger",
} as const;

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ locale: string; workspaceId: string }>;
}) {
  const { locale: raw, workspaceId } = await params;
  const locale = (isLocale(raw) ? raw : "he") as Locale;
  const copy = copyFor(locale);
  const contract = contractLocale(locale);

  const principal = await getPrincipal();
  if (!principal.ok) return notFound();

  const entries = await listAllWorkspaces(principal.data.memberships);
  const owning = entries.find((entry) => entry.workspace.id === workspaceId);
  if (!owning) return notFound();
  const tenantId = owning.tenantId;

  const started = await startInterview(tenantId, workspaceId);
  if (!started.ok) return notFound();
  const runId = started.data.run.id;

  const [derived, plan] = await Promise.all([
    getDerived(tenantId, runId),
    getInterview(tenantId, runId, contract),
  ]);
  if (!derived.ok || !plan.ok) return notFound();

  // Source answers, so a conclusion can be shown next to what produced it.
  const answers = new Map<string, InterviewQuestion>(
    plan.data.questions.map((question) => [question.questionKey, question]),
  );

  async function recalculate() {
    "use server";
    await normaliseInterview(tenantId, runId);
    revalidatePath(`/${locale}/workspaces/${workspaceId}/review`);
  }

  const { facts, requirements, openQuestions, blockingCount } = derived.data;
  const empty = facts.length + requirements.length + openQuestions.length === 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[30px] font-medium leading-[1.38]">{copy.review}</h1>
        {blockingCount > 0 ? (
          <StateBadge state="danger" label={`${copy.blocking}: ${blockingCount}`} />
        ) : null}
        <Link
          href={`/${locale}/workspaces/${workspaceId}/interview`}
          className="ms-auto text-[14px] underline-offset-4 hover:underline"
        >
          {copy.toInterview}
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <p className="min-w-0 flex-1 text-[14px] text-[var(--color-steel)]">{copy.reviewIntro}</p>
        <form action={recalculate}>
          <Button type="submit" variant="outline">
            {copy.recalculate}
          </Button>
        </form>
      </div>

      {empty ? (
        <Card>
          <CardContent className="py-8 text-[14px] text-[var(--color-steel)]">
            {copy.noneYet}
          </CardContent>
        </Card>
      ) : null}

      {/* Blocking items first: they are what prevents approval, so they should
          not be at the bottom of a long page. */}
      {openQuestions.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-[20px] font-medium">{copy.openQuestions}</h2>
          <ul className="flex flex-col gap-3">
            {openQuestions.map((item) => (
              <li key={item.topic_key}>
                <Card>
                  <CardContent className="flex flex-col gap-3 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <StateBadge
                        state={item.blocking ? "danger" : "caution"}
                        label={item.blocking ? copy.blocking : copy.advisory}
                      />
                      {item.owner_role ? (
                        <span className="text-[12px] text-[var(--color-steel)]">
                          {copy.ownerLabel}: {item.owner_role}
                        </span>
                      ) : null}
                      <bdi dir="ltr" className="ms-auto text-[12px] text-[var(--color-fog)]">
                        {item.topic_key}
                      </bdi>
                    </div>
                    <p className="text-[16px]">{item.question[contract]}</p>
                    <Provenance
                      keys={item.source_question_keys}
                      answers={answers}
                      copy={copy}
                    />
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {requirements.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-[20px] font-medium">{copy.requirements}</h2>
          <ul className="flex flex-col gap-3">
            {requirements.map((requirement) => (
              <li key={requirement.requirement_ref}>
                <Card>
                  <CardHeader className="gap-2 pb-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <bdi dir="ltr" className="text-[12px] text-[var(--color-fog)]">
                        {requirement.requirement_ref}
                      </bdi>
                      <StateBadge
                        state="neutral"
                        label={copy.priorityLabel[requirement.priority] ?? requirement.priority}
                      />
                      <StateBadge
                        state={CONFIDENCE_TONE[requirement.confidence]}
                        label={copy.confidenceLabel[requirement.confidence]}
                      />
                    </div>
                    <CardTitle className="text-[16px] font-medium leading-[1.5]">
                      {requirement.statement[contract]}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-3">
                    {requirement.rationale[contract] ? (
                      <p className="text-[14px] text-[var(--color-steel)]">
                        {requirement.rationale[contract]}
                      </p>
                    ) : null}

                    {requirement.acceptance_criteria.length > 0 ? (
                      <div className="flex flex-col gap-1">
                        <h3 className="text-[14px] font-medium">{copy.acceptance}</h3>
                        <ul className="flex list-disc flex-col gap-1 ps-5 text-[14px] text-[var(--color-steel)]">
                          {requirement.acceptance_criteria.map((criterion, index) => (
                            <li key={index}>{criterion[contract]}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}

                    <Provenance
                      keys={requirement.source_question_keys}
                      answers={answers}
                      copy={copy}
                    />
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {facts.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-[20px] font-medium">{copy.facts}</h2>
          <ul className="flex flex-col gap-2">
            {facts.map((fact) => (
              <li
                key={fact.fact_key}
                className="flex flex-wrap items-center gap-3 rounded-[var(--radius-md)] border border-[var(--color-ash)] p-3"
              >
                <bdi dir="ltr" className="text-[12px] text-[var(--color-fog)]">
                  {fact.fact_key}
                </bdi>
                <span className="text-[14px]">{formatValue(fact.value)}</span>
                {/* Confirmed and inferred look different on purpose: one is
                    what the customer said, the other is what we concluded. */}
                <span className="ms-auto flex items-center gap-2">
                  <StateBadge
                    state={fact.verification_state === "confirmed" ? "success" : "neutral"}
                    label={copy.verificationLabel[fact.verification_state] ?? fact.verification_state}
                  />
                  <StateBadge
                    state={CONFIDENCE_TONE[fact.confidence]}
                    label={copy.confidenceLabel[fact.confidence]}
                  />
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function Provenance({
  keys,
  answers,
  copy,
}: {
  keys: string[];
  answers: Map<string, InterviewQuestion>;
  copy: ReturnType<typeof copyFor>;
}) {
  if (keys.length === 0) return null;
  return (
    <div className="flex flex-col gap-1 rounded-[var(--radius-md)] bg-[var(--color-paper)] p-3">
      <span className="text-[12px] text-[var(--color-steel)]">{copy.basedOn}</span>
      {keys.map((key) => {
        const question = answers.get(key);
        return (
          <p key={key} className="text-[13px]">
            <bdi dir="ltr" className="text-[var(--color-fog)]">
              {key}
            </bdi>{" "}
            {question ? question.prompt : null}
            {question?.answered ? (
              <>
                {" — "}
                <span className="text-[var(--color-steel)]">{formatValue(question.answer)}</span>
              </>
            ) : null}
          </p>
        );
      })}
    </div>
  );
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "✓" : "✗";
  if (value !== null && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, entry]) => `${key}: ${entry}`)
      .join(" · ");
  }
  return String(value ?? "");
}
