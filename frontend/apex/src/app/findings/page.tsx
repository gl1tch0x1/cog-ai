"use client";

import { useState } from "react";
import { useApiQuery } from "@/hooks/useApiQuery";

interface Finding {
  id: string;
  title: string;
  severity: string;
  cwe: string | null;
  cvss: number | null;
  validated: boolean;
}

export default function FindingsPage() {
  const [filter, setFilter] = useState("");
  const params = filter ? `?severity=${filter}` : "";
  const { data: findings = [], isLoading, isError, error } = useApiQuery<Finding[]>(
    ["findings", filter],
    `/findings${params}`
  );

  const severityColor: Record<string, string> = {
    critical: "bg-red-600 text-white",
    high: "bg-orange-500 text-white",
    medium: "bg-yellow-500 text-black",
    low: "bg-blue-400 text-white",
    info: "bg-slate-400 text-white",
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Findings</h1>
        <select
          className="border rounded px-3 py-2"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      {isLoading && <p className="text-slate-500">Loading...</p>}
      {isError && <p className="text-red-500">Failed to load findings: {error?.message}</p>}
      <div className="space-y-3">
        {findings.map((f) => (
          <div key={f.id} className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
            <div>
              <h3 className="font-medium">{f.title}</h3>
              <p className="text-sm text-slate-500">
                {f.cwe && `CWE: ${f.cwe}`} {f.cvss && `• CVSS: ${f.cvss}`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {f.validated && <span className="text-green-600 text-sm font-medium">✓ Validated</span>}
              <span className={`px-2 py-1 rounded text-xs font-bold ${severityColor[f.severity] || "bg-slate-400 text-white"}`}>
                {(f.severity ?? "unknown").toUpperCase()}
              </span>
            </div>
          </div>
        ))}
        {!isLoading && findings.length === 0 && (
          <p className="text-center text-slate-400 py-8">No findings yet</p>
        )}
      </div>
    </div>
  );
}
