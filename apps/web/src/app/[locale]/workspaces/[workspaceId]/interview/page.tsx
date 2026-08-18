import Link from "next/link";
import { notFound } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateBadge } from "@/components/state-badge";
import { QuestionForm } from "./question-form";
import {
  getInterview,
  getPrincipal,
  listAllWorkspaces,
  startInterview,
  type InterviewQuestion,
} from "@/lib/domain-api";
import { contractLocale, copyFor, isLocale, type Locale } from "@/lib/i18n";

/**
 * The interview.
 *
 * One question at a time (Discovery §3.2), progress by applicable questions
 * rather than a fixed count that branching has not settled (§3.4), and every
 * answer saved as it is given so the customer can leave and come back (§3.5).
 */
export default async function InterviewPage({
  params,
}: {
  params: Promise<{ locale: string; workspaceId: string }>;
}) {
  const { locale: raw, workspaceId } = await params;
  const locale = (isLocale(raw) ? raw : "he") as Locale;
  const copy = copyFor(locale);

  const principal = await getPrincipal();
  if (!principal.ok) return notFound();

  // Which tenant owns this workspace is a fact to look up, not a guess: the
  // caller may belong to several, and asking the wrong one returns nothing.
  const entries = await listAllWorkspaces(principal.data.memberships);
  const owning = entries.find((entry) => entry.workspace.id === workspaceId);
  if (!owning) return notFound();
  const tenantId = owning.tenantId;

  // Starting is idempotent: it resumes the run already in progress rather than
  // asking the customer for anything twice.
  const started = await startInterview(tenantId, workspaceId);
  if (!started.ok) return notFound();

  const plan = await getInterview(tenantId, started.data.run.id, contractLocale(locale));
  if (!plan.ok) return notFound();

  const { questions, progress, nextQuestionKey, runId, definitionVersion } = plan.data;
  const applicable = questions.filter((question) => question.applicable);
  const current: InterviewQuestion | undefined =
    applicable.find((question) => question.questionKey === nextQuestionKey) ??
    applicable.find((question) => !question.answered);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[30px] font-medium leading-[1.38]">{copy.interview}</h1>
        <StateBadge state="info" label={copy.modeLabel[plan.data.mode] ?? plan.data.mode} />
        <span className="ms-auto flex items-center gap-4">
          <Link
            href={`/${locale}/workspaces/${workspaceId}/review`}
            className="text-[14px] underline-offset-4 hover:underline"
          >
            {copy.review}
          </Link>
          <Link
            href={`/${locale}/workspaces`}
            className="text-[14px] underline-offset-4 hover:underline"
          >
            {copy.backToWorkspaces}
          </Link>
        </span>
      </div>

      {/* Progress by applicable questions. The denominator moves as branches
          open, which is honest: a hidden question was never asked. */}
      <div className="flex flex-col gap-2">
        <div className="flex items-baseline justify-between text-[14px]">
          <span>{copy.progressLabel}</span>
          <span className="text-[var(--color-steel)]">
            <bdi dir="ltr">
              {progress.answered} / {progress.applicable}
            </bdi>
          </span>
        </div>
        <div
          className="h-2 w-full overflow-hidden rounded-[var(--radius-pill)] bg-[var(--color-paper)]"
          role="progressbar"
          aria-valuenow={progress.percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={copy.progressLabel}
        >
          <div
            className="h-full bg-[var(--color-action-fill)] transition-[width] duration-200"
            style={{ inlineSize: `${progress.percent}%` }}
          />
        </div>
      </div>

      {current ? (
        <QuestionForm
          locale={locale}
          tenantId={tenantId}
          runId={runId}
          question={current}
          index={applicable.findIndex((q) => q.questionKey === current.questionKey) + 1}
          total={applicable.length}
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-[20px] font-medium">{copy.allAnswered}</CardTitle>
          </CardHeader>
        </Card>
      )}

      {/* Answered questions stay visible and editable: a customer who realises
          they misspoke should not have to ask someone to fix it. */}
      <section className="flex flex-col gap-3">
        <h2 className="text-[16px] font-medium">{copy.answeredEarlier}</h2>
        <ul className="flex flex-col gap-2">
          {applicable
            .filter((question) => question.answered && question.questionKey !== current?.questionKey)
            .map((question) => (
              <li
                key={question.questionKey}
                className="flex flex-wrap items-start gap-3 rounded-[var(--radius-md)] border border-[var(--color-ash)] p-3"
              >
                <bdi dir="ltr" className="text-[12px] text-[var(--color-fog)]">
                  {question.questionKey}
                </bdi>
                <span className="min-w-0 flex-1 text-[14px]">{question.prompt}</span>
                <span className="text-[14px] text-[var(--color-steel)]">
                  {formatAnswer(question)}
                </span>
              </li>
            ))}
        </ul>
      </section>

      <p className="text-[12px] text-[var(--color-fog)]">
        <bdi dir="ltr">
          {runId} · v{definitionVersion}
        </bdi>
      </p>
    </div>
  );
}

function formatAnswer(question: InterviewQuestion): string {
  const value = question.answer;
  if (Array.isArray(value)) {
    const labels = value.map(
      (item) => question.options.find((option) => option.value === item)?.label ?? String(item),
    );
    return labels.join(", ");
  }
  if (typeof value === "object" && value !== null) return JSON.stringify(value);
  const single = question.options.find((option) => option.value === value);
  return single?.label ?? String(value ?? "");
}
