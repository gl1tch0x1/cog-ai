import { useApiQuery } from "./useApiQuery";

export interface DashboardStats {
  active_workflows: number;
  total_findings: number;
  validated_findings: number;
  total_targets: number;
}

export function useDashboardStats() {
  return useApiQuery<DashboardStats>(["dashboard-stats"], "/dashboard/stats");
}
