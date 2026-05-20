"use client";

import { useState } from "react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { useAuth } from "@/hooks/useAuth";
import { useMutation, useQueryClient } from "@tanstack/react-query";

interface Target {
  id: string;
  domain: string;
  scope: string[];
  tags: string[];
  created_at: string;
}

export default function TargetsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const { data: targets = [], isLoading, isError, error } = useApiQuery<Target[]>(["targets"], "/targets");
  const [showAdd, setShowAdd] = useState(false);
  const [newTarget, setNewTarget] = useState({ domain: "", tags: "" });

  const addMutation = useMutation({
    mutationFn: async (data: { domain: string; tags: string[] }) => {
      if (!token) throw new Error("Not authenticated");
      const res = await fetch("/api/targets", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...data, project_id: "00000000-0000-0000-0000-000000000001", scope: [] }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail?.[0]?.msg || body.detail || `Error ${res.status}`);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      setShowAdd(false);
      setNewTarget({ domain: "", tags: "" });
    },
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Targets</h1>
        <button onClick={() => setShowAdd(true)} className="bg-slate-900 text-white px-4 py-2 rounded hover:bg-slate-800">
          Add Target
        </button>
      </div>

      {showAdd && (
        <div className="bg-white rounded-lg shadow p-6 mb-8 border">
          <form onSubmit={(e) => { e.preventDefault(); addMutation.mutate({ domain: newTarget.domain, tags: newTarget.tags.split(",").map(t => t.trim()).filter(Boolean) }); }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Domain</label>
              <input type="text" required className="mt-1 block w-full border rounded-md px-3 py-2" placeholder="example.com" value={newTarget.domain} onChange={(e) => setNewTarget({ ...newTarget, domain: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Tags (comma separated)</label>
              <input type="text" className="mt-1 block w-full border rounded-md px-3 py-2" placeholder="prod, external" value={newTarget.tags} onChange={(e) => setNewTarget({ ...newTarget, tags: e.target.value })} />
            </div>
            {addMutation.isError && <p className="text-red-600 text-sm">{addMutation.error?.message}</p>}
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 text-slate-600">Cancel</button>
              <button type="submit" disabled={addMutation.isPending} className="bg-slate-900 text-white px-4 py-2 rounded disabled:opacity-50">
                {addMutation.isPending ? "Saving..." : "Save Target"}
              </button>
            </div>
          </form>
        </div>
      )}

      {isLoading && <p className="text-slate-500">Loading targets...</p>}
      {isError && <p className="text-red-500">Failed to load targets: {error?.message}</p>}
      {!isLoading && !isError && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="px-4 py-3 text-sm font-medium text-slate-600">Domain</th>
                <th className="px-4 py-3 text-sm font-medium text-slate-600">Tags</th>
                <th className="px-4 py-3 text-sm font-medium text-slate-600">Created</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((t) => (
                <tr key={t.id} className="border-b hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium">{t.domain}</td>
                  <td className="px-4 py-3"><div className="flex gap-1">{t.tags.map((tag) => <span key={tag} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{tag}</span>)}</div></td>
                  <td className="px-4 py-3 text-sm text-slate-500">{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {targets.length === 0 && <tr><td colSpan={3} className="px-4 py-8 text-center text-slate-400">No targets monitored</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
