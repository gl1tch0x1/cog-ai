"use client";

import React, { useEffect, useState } from "react";

interface Report {
  id: string;
  workflow_id: string;
  format: string;
  finding_count: number;
  created_at: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    fetch("/api/reports")
      .then((r) => r.json())
      .then(setReports)
      .catch(() => {});
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Reports</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">ID</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Format</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Findings</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Created</th>
              <th className="px-4 py-3 text-sm font-medium text-slate-600">Actions</th>
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
                <td className="px-4 py-3">
                  <a href={`/api/reports/${r.id}/download`} className="text-apex-600 hover:underline text-sm">
                    Download
                  </a>
                </td>
              </tr>
            ))}
            {reports.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">No reports yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
