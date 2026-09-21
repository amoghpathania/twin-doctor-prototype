"use client";

import type { RiskLevel } from "@/lib/api";

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return <span className={`badge ${risk}`}>{risk}</span>;
}
