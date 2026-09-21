"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Persona = "patient" | "doctor" | "admin";

const STORAGE_KEY = "twin-persona";

export const PERSONA_ROUTES: Record<Persona, string> = {
  patient: "/intake",
  doctor: "/dashboard",
  admin: "/admin",
};

interface PersonaContextValue {
  persona: Persona;
  setPersona: (persona: Persona) => void;
}

const PersonaContext = createContext<PersonaContextValue | null>(null);

export function PersonaProvider({ children }: { children: React.ReactNode }) {
  // Patient is the app's primary/default view.
  const [persona, setPersonaState] = useState<Persona>("patient");

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY) as Persona | null;
    if (stored === "patient" || stored === "doctor" || stored === "admin") {
      setPersonaState(stored);
    }
  }, []);

  function setPersona(next: Persona) {
    setPersonaState(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }

  return <PersonaContext.Provider value={{ persona, setPersona }}>{children}</PersonaContext.Provider>;
}

export function usePersona(): PersonaContextValue {
  const ctx = useContext(PersonaContext);
  if (!ctx) throw new Error("usePersona must be used within a PersonaProvider");
  return ctx;
}
