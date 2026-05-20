"use client";

import { useApiQuery } from "@/hooks/useApiQuery";

interface Report {
  id: string;
  workflow_id: string;
  format: string;
  finding_count: number;
  created_at: string;
}

export default function ReportsPage() {
  const { data: reports = [], isLoading } = useApiQuery<Report[]>(["reports"], "/reports");

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Reports</h1>
      {isLoading && <p className="text-slate-500">Loading...</p>}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">ID</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Format</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Findings</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Created</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <tr key={r.id} className="border-b hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-sm">{r.id.slice(0, 8)}</td>
                <td className="px-4 py-3 uppercase text-sm">{r.format}</td>
                <td className="px-4 py-3">{r.finding_count}</td>
                <td className="px-4 py-3 text-sm text-slate-500">
                  {new Date(r.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {!isLoading && reports.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-400">No reports yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
