import Image from "next/image";
import Link from "next/link";
import { copyFor, otherLocale, type Locale } from "@/lib/i18n";

/**
 * Application shell.
 *
 * Every offset here is logical (`inline-start`, `inline-end`, `ps`, `pe`), so
 * the same markup mirrors correctly in Hebrew without a second stylesheet.
 * The two things that deliberately do not mirror are the logos.
 */

function Nav({ locale }: { locale: Locale }) {
  const copy = copyFor(locale);
  const items = [
    { href: `/${locale}`, label: copy.overview },
    { href: `/${locale}/workspaces`, label: copy.workspaces },
    { href: `/${locale}/catalogue`, label: copy.catalogue },
    { href: `/${locale}/administration`, label: copy.administration },
  ];

  return (
    <nav aria-label={copy.overview} className="flex flex-col gap-1">
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="rounded-[var(--radius-sm)] px-3 py-2 text-[14px] text-[var(--color-charcoal)] transition-colors hover:bg-[var(--color-paper)]"
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

export function AppShell({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  const copy = copyFor(locale);
  const other = otherLocale(locale);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-[var(--color-ash)] bg-[var(--color-canvas)]">
        <div className="mx-auto flex w-full max-w-[var(--page-max-width)] items-center gap-4 px-6 py-4">
          <Link href={`/${locale}`} className="flex items-center gap-3">
            {/* Brand marks never mirror under RTL. */}
            <Image
              src="/brand/aione-horizontal.svg"
              alt={copy.productName}
              width={132}
              height={32}
              priority
            />
          </Link>

          <span className="ms-auto flex items-center gap-3">
            <Link
              href={`/${other}`}
              lang={other}
              className="rounded-[var(--radius-sm)] border border-[var(--color-ash)] px-3 py-1.5 text-[14px] hover:bg-[var(--color-paper)]"
            >
              {copy.languageSwitch}
            </Link>
          </span>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-[var(--page-max-width)] flex-1 gap-8 px-6 py-8">
        <aside className="hidden w-56 shrink-0 md:block">
          <Nav locale={locale} />
        </aside>

        <main id="main" className="min-w-0 flex-1">
          {children}
        </main>
      </div>

      <footer className="border-t border-[var(--color-ash)] bg-[var(--color-canvas)]">
        <div className="mx-auto flex w-full max-w-[var(--page-max-width)] flex-wrap items-center gap-4 px-6 py-6">
          <p className="text-[12px] text-[var(--color-steel)]">{copy.incrementNotice}</p>

          {/* Partner badge: full colour, unmodified, exempt from the logo
              desaturation rule, with the caption that names the relationship
              (DESIGN-SYSTEM.md §9.3). */}
          <div className="ms-auto flex items-center gap-3">
            <Image
              src="/brand/odoo-silver-partner.svg"
              alt={copy.partnerCaption}
              width={96}
              height={32}
              className="h-8 w-auto"
            />
            <span className="text-[12px] text-[var(--color-steel)]">{copy.partnerCaption}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
