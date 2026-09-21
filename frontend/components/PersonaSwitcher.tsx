"use client";

import { useRouter } from "next/navigation";
import { PERSONA_ROUTES, Persona, usePersona } from "@/components/PersonaContext";

const OPTIONS: { value: Persona; label: string }[] = [
  { value: "patient", label: "Patient" },
  { value: "doctor", label: "Doctor" },
  { value: "admin", label: "Admin" },
];

export function PersonaSwitcher() {
  const { persona, setPersona } = usePersona();
  const router = useRouter();

  function handleSelect(next: Persona) {
    setPersona(next);
    router.push(PERSONA_ROUTES[next]);
  }

  return (
    <div className="persona-switcher">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={option.value === persona ? "persona-option active" : "persona-option"}
          onClick={() => handleSelect(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
