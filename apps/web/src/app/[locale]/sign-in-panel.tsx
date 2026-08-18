import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { Button } from "@/components/ui/button";
import { DEV_SUBJECT_COOKIE } from "@/lib/domain-api";
import { copyFor, type Locale } from "@/lib/i18n";

/**
 * Local sign-in.
 *
 * This is a development affordance, not an authentication design. The domain
 * API only accepts a subject like this when AUTH_MODE=dev, which it refuses
 * unless APP_ENVIRONMENT=local — so this panel cannot become a way in on a
 * deployed environment even if it were left in place.
 *
 * The real flow arrives with the identity provider decision (ADR-014). What
 * is already true and will stay true: the cookie is httpOnly, the browser
 * never sees a token, and the tenant is never named by the client.
 */

// Matches scripts/seed_dev.py. Distinct from the subjects the test suites own,
// so running the tests does not sign the developer out of their fixture.
const TEST_SUBJECTS = [
  { subject: "auth|dev-manager", label: "Dana — Account Manager" },
  { subject: "auth|dev-lead", label: "Yossi — Team Lead" },
];

async function signIn(formData: FormData) {
  "use server";
  const subject = String(formData.get("subject") ?? "");
  const store = await cookies();
  store.set(DEV_SUBJECT_COOKIE, subject, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
  });
  revalidatePath("/", "layout");
}

async function signOut() {
  "use server";
  const store = await cookies();
  store.delete(DEV_SUBJECT_COOKIE);
  revalidatePath("/", "layout");
}

export function SignInPanel({ locale, signedIn }: { locale: Locale; signedIn: boolean }) {
  const copy = copyFor(locale);

  if (signedIn) {
    return (
      <form action={signOut}>
        <Button type="submit" variant="outline">
          {copy.signOut}
        </Button>
      </form>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-[14px] text-[var(--color-steel)]">{copy.chooseTestUser}</p>
      <div className="flex flex-wrap gap-2">
        {TEST_SUBJECTS.map((user) => (
          <form action={signIn} key={user.subject}>
            <input type="hidden" name="subject" value={user.subject} />
            <Button type="submit">
              {copy.signIn} — {user.label}
            </Button>
          </form>
        ))}
      </div>
    </div>
  );
}
