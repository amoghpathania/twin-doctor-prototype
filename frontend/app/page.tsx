"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { PERSONA_ROUTES, usePersona } from "@/components/PersonaContext";

export default function HomePage() {
  const { persona } = usePersona();
  const router = useRouter();

  useEffect(() => {
    router.replace(PERSONA_ROUTES[persona]);
  }, [persona, router]);

  return null;
}
