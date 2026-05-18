"use client";

import { useEffect, useState } from "react";

interface Target {
  id: string;
  domain: string;
  scope: string[];
  tags: string[];
  created_at: string;
}

export default function TargetsPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newTarget, setNewTarget] = useState({ domain: "", tags: "" });

  useEffect(() => {
    fetch("/api/targets")
      .then((r) => r.json())
      .then(setTargets)
      .catch(() => {});
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch("/api/targets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        domain: newTarget.domain,
        tags: newTarget.tags.split(",").map(t => t.trim()).filter(Boolean),
        project_id: "00000000-0000-0000-0000-000000000000" // Default/Placeholder
      })
    });
    if (res.ok) {
      const added = await res.json();
      setTargets([...targets, added]);
      setShowAdd(false);
      setNewTarget({ domain: "", tags: "" });
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Targets</h1>
        <button 
          onClick={() => setShowAdd(true)}
          className="bg-apex-600 text-white px-4 py-2 rounded hover:bg-apex-700"
        >
          Add Target
        </button>
      </div>

      {showAdd && (
        <div className="bg-white rounded-lg shadow p-6 mb-8 border border-apex-100">
          <h2 className="text-lg font-semibold mb-4">Add New Target</h2>
          <form onSubmit={handleAdd} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Domain / URL</label>
              <input 
                type="text" 
                required
                className="mt-1 block w-full border rounded-md px-3 py-2"
                placeholder="example.com"
                value={newTarget.domain}
                onChange={e => setNewTarget({...newTarget, domain: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Tags (comma separated)</label>
              <input 
                type="text" 
                className="mt-1 block w-full border rounded-md px-3 py-2"
                placeholder="prod, external"
                value={newTarget.tags}
                onChange={e => setNewTarget({...newTarget, tags: e.target.value})}
              />
            </div>
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 text-slate-600">Cancel</button>
              <button type="submit" className="bg-apex-600 text-white px-4 py-2 rounded">Save Target</button>
            </div>
          </form>
        </div>
      )}

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
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    {t.tags.map(tag => (
                      <span key={tag} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{tag}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-500">
                  {new Date(t.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
            {targets.length === 0 && (
              <tr><td colSpan={3} className="px-4 py-8 text-center text-slate-400">No targets monitored</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
