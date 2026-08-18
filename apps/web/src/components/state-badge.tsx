/**
 * State badge.
 *
 * Colour never carries the meaning on its own (MVP §20.3, IS 5568 criterion
 * 1.4.1). Every badge renders a tint, a shape that differs per state, and a
 * text label — so the state survives greyscale printing, colour-vision
 * differences and a screen reader.
 */

type State = "success" | "caution" | "danger" | "info" | "neutral";

const TOKENS: Record<State, { tint: string; border: string; ink: string; glyph: string }> = {
  success: {
    tint: "var(--color-state-success-tint)",
    border: "var(--color-state-success-border)",
    ink: "var(--color-state-success-ink)",
    glyph: "✓",
  },
  caution: {
    tint: "var(--color-state-caution-tint)",
    border: "var(--color-state-caution-border)",
    ink: "var(--color-state-caution-ink)",
    glyph: "▲",
  },
  danger: {
    tint: "var(--color-state-danger-tint)",
    border: "var(--color-state-danger-border)",
    ink: "var(--color-state-danger-ink)",
    glyph: "■",
  },
  info: {
    tint: "var(--color-state-info-tint)",
    border: "var(--color-state-info-border)",
    ink: "var(--color-state-info-ink)",
    glyph: "●",
  },
  neutral: {
    tint: "var(--color-state-neutral-tint)",
    border: "var(--color-state-neutral-border)",
    ink: "var(--color-state-neutral-ink)",
    glyph: "–",
  },
};

export function StateBadge({ state, label }: { state: State; label: string }) {
  const token = TOKENS[state];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-[var(--radius-pill)] border px-2.5 py-1 text-[12px]"
      style={{
        background: token.tint,
        borderColor: token.border,
        // Charcoal on every tint is 14.7:1 or better; the ink colours the
        // glyph only, where it is decoration beside a real label.
        color: "var(--color-charcoal)",
      }}
    >
      <span aria-hidden="true" style={{ color: token.ink }}>
        {token.glyph}
      </span>
      {label}
    </span>
  );
}
