import type { Metadata } from "next";
import "./globals.css";
import { SidebarNav } from "@/components/SidebarNav";
import { PersonaProvider } from "@/components/PersonaContext";
import { PersonaSwitcher } from "@/components/PersonaSwitcher";

export const metadata: Metadata = {
  title: "Doctor Digital Twin (Prototype)",
  description: "Synthetic prototype - not a real medical device.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PersonaProvider>
          <PersonaSwitcher />
          <div className="app-shell">
            <aside className="sidebar">
              <div className="sidebar-brand">
                <span className="sidebar-brand-mark">DT</span>
                Doctor Twin
              </div>
              <p className="sidebar-tagline">Synthetic prototype - not a medical device.</p>
              <SidebarNav />
            </aside>
            <div className="content">{children}</div>
          </div>
        </PersonaProvider>
      </body>
    </html>
  );
}
