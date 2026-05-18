import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "APEX - SecAgents Dashboard",
  description: "Enterprise security operations dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <div className="flex">
          <aside className="w-64 min-h-screen bg-slate-900 text-white p-4">
            <h1 className="text-xl font-bold mb-8 text-apex-500">APEX</h1>
            <nav className="space-y-2">
              <Link href="/" className="block px-3 py-2 rounded hover:bg-slate-800">Dashboard</Link>
              <Link href="/workflows" className="block px-3 py-2 rounded hover:bg-slate-800">Workflows</Link>
              <Link href="/findings" className="block px-3 py-2 rounded hover:bg-slate-800">Findings</Link>
              <Link href="/reports" className="block px-3 py-2 rounded hover:bg-slate-800">Reports</Link>
              <Link href="/targets" className="block px-3 py-2 rounded hover:bg-slate-800">Targets</Link>
            </nav>
          </aside>
          <main className="flex-1 p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
