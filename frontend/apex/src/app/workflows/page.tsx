"use client";

import { useApiQuery } from "@/hooks/useApiQuery";

interface Workflow {
  id: string;
  workflow_type: string;
  status: string;
  current_phase: string | null;
  started_at: string;
}

export default function WorkflowsPage() {
  const { data: workflows = [], isLoading, isError, error } = useApiQuery<Workflow[]>(
    ["workflows"],
    "/workflows"
  );

  const statusColor: Record<string, string> = {
    running: "bg-green-100 text-green-800",
    completed: "bg-blue-100 text-blue-800",
    failed: "bg-red-100 text-red-800",
    pending: "bg-yellow-100 text-yellow-800",
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Workflows</h1>
      </div>
      {isLoading && <p className="text-slate-500">Loading...</p>}
      {isError && <p className="text-red-500">Failed to load workflows: {error?.message}</p>}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">ID</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Type</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Status</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Phase</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Started</th>
            </tr>
          </thead>
          <tbody>
            {workflows.map((w) => (
              <tr key={w.id} className="border-b hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-sm">{w.id.slice(0, 8)}</td>
                <td className="px-4 py-3">{w.workflow_type}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor[w.status] || ""}`}>
                    {w.status}
                  </span>
                </td>
                <td className="px-4 py-3">{w.current_phase || "—"}</td>
                <td className="px-4 py-3 text-sm text-slate-500">
                  {w.started_at ? new Date(w.started_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
            {!isLoading && workflows.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">No workflows yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
