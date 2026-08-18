import { revalidatePath } from "next/cache";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { submitAnswer, type InterviewQuestion } from "@/lib/domain-api";
import { copyFor, type Locale } from "@/lib/i18n";

/**
 * One question.
 *
 * A server action rather than client state: the answer is written through the
 * domain API on submit, so what is on screen and what is stored cannot drift,
 * and leaving the page loses nothing (Discovery §3.5).
 *
 * Every control has a persistent visible label. Placeholders are never labels
 * (DESIGN-SYSTEM.md §5.6).
 */
export function QuestionForm({
  locale,
  tenantId,
  runId,
  question,
  index,
  total,
}: {
  locale: Locale;
  tenantId: string;
  runId: string;
  question: InterviewQuestion;
  index: number;
  total: number;
}) {
  const copy = copyFor(locale);

  async function save(formData: FormData) {
    "use server";

    const raw = formData.getAll("value").map(String).filter((entry) => entry.length > 0);
    let value: unknown;

    switch (question.answerType) {
      case "multi_select":
        value = raw;
        break;
      case "single_select":
      case "short_text":
      case "long_narrative":
        value = raw[0] ?? "";
        break;
      case "ranked_list":
        // One item per line, order preserved: the ranking is the order given.
        value = (raw[0] ?? "").split("\n").map((line) => line.trim()).filter(Boolean);
        break;
      case "repeating_group": {
        const group: Record<string, string> = {};
        for (const option of question.options) {
          const entry = String(formData.get(`field:${option.value}`) ?? "").trim();
          if (entry) group[option.value] = entry;
        }
        value = group;
        break;
      }
      default:
        value = raw[0] ?? "";
    }

    await submitAnswer(tenantId, runId, question.questionKey, value);
    revalidatePath(`/${locale}/workspaces`, "layout");
  }

  const required = question.requiredPolicy !== "optional";
  const legendId = `${question.questionKey}-legend`;

  return (
    <Card>
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center gap-2 text-[12px] text-[var(--color-fog)]">
          <bdi dir="ltr">
            {copy.question} {index} / {total}
          </bdi>
          <bdi dir="ltr">{question.questionKey}</bdi>
          <span>{required ? copy.required : copy.optional}</span>
        </div>
        <CardTitle className="text-[20px] font-medium leading-[1.4]" id={legendId}>
          {question.prompt}
        </CardTitle>
        {question.helpText ? (
          <p className="text-[14px] text-[var(--color-steel)]">{question.helpText}</p>
        ) : null}
      </CardHeader>

      <CardContent>
        <form action={save} className="flex flex-col gap-5">
          {question.answerType === "multi_select" || question.answerType === "single_select" ? (
            <fieldset className="flex flex-col gap-2" aria-labelledby={legendId}>
              {question.options.map((option) => {
                const id = `${question.questionKey}-${option.value}`;
                const selected = Array.isArray(question.answer)
                  ? question.answer.includes(option.value)
                  : question.answer === option.value;
                return (
                  <label
                    key={option.value}
                    htmlFor={id}
                    className="flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--color-ash)] p-3 text-[16px] hover:bg-[var(--color-paper)]"
                  >
                    <input
                      id={id}
                      name="value"
                      value={option.value}
                      type={question.answerType === "multi_select" ? "checkbox" : "radio"}
                      defaultChecked={selected}
                      className="size-5 accent-[var(--color-action-fill)]"
                    />
                    {option.label}
                  </label>
                );
              })}
            </fieldset>
          ) : question.answerType === "repeating_group" ? (
            <div className="flex flex-col gap-3">
              {question.options.map((option) => {
                const id = `${question.questionKey}-${option.value}`;
                const existing =
                  typeof question.answer === "object" && question.answer !== null
                    ? String((question.answer as Record<string, unknown>)[option.value] ?? "")
                    : "";
                return (
                  <div key={option.value} className="flex flex-col gap-1">
                    <label htmlFor={id} className="text-[14px]">
                      {option.label}
                    </label>
                    <input
                      id={id}
                      name={`field:${option.value}`}
                      defaultValue={existing}
                      className="rounded-[var(--radius-xs)] border border-[var(--color-steel)] px-3 py-2 text-[16px]"
                    />
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              <label htmlFor={question.questionKey} className="sr-only">
                {question.prompt}
              </label>
              <textarea
                id={question.questionKey}
                name="value"
                rows={question.answerType === "long_narrative" ? 5 : 3}
                defaultValue={
                  Array.isArray(question.answer)
                    ? (question.answer as string[]).join("\n")
                    : String(question.answer ?? "")
                }
                className="rounded-[var(--radius-xs)] border border-[var(--color-steel)] px-3 py-2 text-[16px] leading-[1.6]"
              />
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit">{copy.save}</Button>
            {/* The engine records why a question is being asked; showing it
                means a customer never has to guess. */}
            <span className="text-[12px] text-[var(--color-fog)]">
              {copy.whyThisQuestion}: <bdi dir="ltr">{question.applicabilityReason}</bdi>
            </span>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
