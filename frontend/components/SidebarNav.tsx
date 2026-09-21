"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Persona, usePersona } from "@/components/PersonaContext";

const LINKS: { href: string; label: string; persona: Persona; icon: string }[] = [
  { href: "/intake", label: "Patient Intake", persona: "patient", icon: "\u{1F4AC}" },
  { href: "/dashboard", label: "Doctor Dashboard", persona: "doctor", icon: "\u{1FA7A}" },
  { href: "/admin", label: "Admin", persona: "admin", icon: "\u{1F9E0}" },
];

export function SidebarNav() {
  const pathname = usePathname();
  const { persona } = usePersona();
  const visibleLinks = LINKS.filter((link) => link.persona === persona);

  return (
    <nav className="sidebar-nav">
      {visibleLinks.map((link) => {
        const isActive = pathname?.startsWith(link.href);
        return (
          <Link key={link.href} href={link.href} className={isActive ? "active" : ""}>
            <span>
              {link.icon} {link.label}
            </span>
            <small>{link.persona}</small>
          </Link>
        );
      })}
    </nav>
  );
}
