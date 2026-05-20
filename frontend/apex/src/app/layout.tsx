"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import "./globals.css";
import Providers from "./Providers";
import { useAuth } from "@/hooks/useAuth";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <Providers>
          <AuthGate>{children}</AuthGate>
        </Providers>
      </body>
    </html>
  );
}

function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const authenticated = isAuthenticated();

  useEffect(() => {
    if (!authenticated && pathname !== "/login") {
      router.replace("/login");
    }
  }, [authenticated, pathname, router]);

  if (pathname === "/login") return <>{children}</>;
  if (!authenticated) return null;

  return (
    <div className="flex">
      <aside className="w-64 min-h-screen bg-slate-900 text-white p-4 flex flex-col" role="navigation" aria-label="Main navigation">
        <h1 className="text-xl font-bold mb-8 text-apex-500" aria-label="SecAgent APEX Dashboard">APEX</h1>
        <nav className="flex-1 space-y-2" aria-label="Primary">
          <NavLink href="/" label="Dashboard" current={pathname} />
          <NavLink href="/workflows" label="Workflows" current={pathname} />
          <NavLink href="/findings" label="Findings" current={pathname} />
          <NavLink href="/reports" label="Reports" current={pathname} />
          <NavLink href="/targets" label="Targets" current={pathname} />
        </nav>
        <button
          onClick={() => { logout(); router.push("/login"); }}
          className="mt-auto block w-full text-left px-3 py-2 rounded hover:bg-red-900 text-red-400"
          aria-label="Sign out"
        >
          Logout
        </button>
      </aside>
      <main className="flex-1 p-8" role="main" aria-label="Page content">{children}</main>
    </div>
  );
}

function NavLink({ href, label, current }: { href: string; label: string; current: string }) {
  const active = current === href;
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`block px-3 py-2 rounded ${active ? "bg-slate-800 text-white" : "hover:bg-slate-800 text-slate-300"}`}
    >
      {label}
    </Link>
  );
}
