import { MessageCircle } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type Size = "md" | "lg";

type Props = {
  prefill: string;
  children?: ReactNode;
  className?: string;
  size?: Size;
};

/** Número E.164 sem + (ex.: 5531999999999). Definir em NEXT_PUBLIC_WHATSAPP_NUMBER. */
function resolveWhatsAppNumber(): string {
  const raw = (process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "").replace(/\D/g, "");
  return raw.length >= 10 ? raw : "";
}

export function SalesWhatsAppButton({ prefill, children, className, size = "md" }: Props) {
  const number = resolveWhatsAppNumber();
  const text = encodeURIComponent(prefill);
  const href = number
    ? `https://wa.me/${number}?text=${text}`
    : `https://wa.me/?text=${text}`;

  const sizeCls =
    size === "lg"
      ? "px-5 py-3 text-sm gap-2.5"
      : "px-4 py-2.5 text-[13px] gap-2";

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "inline-flex items-center justify-center rounded-xl border border-emerald-500/35",
        "bg-emerald-500/15 font-semibold tracking-wide text-emerald-100",
        "hover:bg-emerald-500/25 hover:border-emerald-400/50 transition-colors",
        sizeCls,
        className
      )}
    >
      <MessageCircle className={size === "lg" ? "h-4 w-4 shrink-0" : "h-3.5 w-3.5 shrink-0"} aria-hidden />
      {children ?? "Falar no WhatsApp"}
    </a>
  );
}
