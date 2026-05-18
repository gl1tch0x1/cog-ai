export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard title="Active Workflows" value="3" color="blue" />
        <StatCard title="Total Findings" value="47" color="red" />
        <StatCard title="Validated" value="32" color="green" />
        <StatCard title="Targets" value="8" color="purple" />
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
        <p className="text-slate-500">No recent activity.</p>
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    blue: "border-blue-500 text-blue-700",
    red: "border-red-500 text-red-700",
    green: "border-green-500 text-green-700",
    purple: "border-purple-500 text-purple-700",
  };
  return (
    <div className={`bg-white rounded-lg shadow p-4 border-l-4 ${colors[color]}`}>
      <p className="text-sm text-slate-500">{title}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}
