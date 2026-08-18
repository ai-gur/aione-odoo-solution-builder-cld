import type { Metadata } from "next";
import { notFound } from "next/navigation";
import "../globals.css";
import { AppShell } from "@/components/app-shell";
import { DEFAULT_LOCALE, LOCALES, copyFor, directionOf, isLocale } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "AIOne Odoo Solution Builder",
  description:
    "Business discovery, Odoo Enterprise 19 blueprints and validated sandbox provisioning.",
};

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const direction = directionOf(locale);
  const copy = copyFor(locale);

  return (
    // lang and dir on the document, not on a wrapper: assistive technology and
    // the bidirectional algorithm both key off the document, and WCAG 3.1.1
    // asks for the page language specifically.
    <html lang={locale} dir={direction} suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <a href="#main" className="skip-link">
          {copy.skipToContent}
        </a>
        <AppShell locale={locale}>{children}</AppShell>
      </body>
    </html>
  );
}

export const dynamicParams = false;
export { DEFAULT_LOCALE };
