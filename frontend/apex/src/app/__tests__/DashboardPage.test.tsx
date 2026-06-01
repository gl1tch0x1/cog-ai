import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import DashboardPage from '../page'
import { useDashboardStats } from '@/hooks/useDashboardStats'

// Mock the hook
vi.mock('@/hooks/useDashboardStats', () => ({
  useDashboardStats: vi.fn(),
}))

describe('DashboardPage', () => {
  it('renders loading state', () => {
    vi.mocked(useDashboardStats).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any)

    render(<DashboardPage />)
    expect(screen.getByText(/loading dashboard stats/i)).toBeInTheDocument()
  })

  it('renders error state', () => {
    vi.mocked(useDashboardStats).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as any)

    render(<DashboardPage />)
    expect(screen.getByText(/error loading dashboard stats/i)).toBeInTheDocument()
  })

  it('renders stats when loaded', () => {
    vi.mocked(useDashboardStats).mockReturnValue({
      data: {
        active_workflows: 5,
        total_findings: 10,
        validated_findings: 3,
        total_targets: 20,
      },
      isLoading: false,
      isError: false,
    } as any)

    render(<DashboardPage />)
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
    expect(screen.getByText('Active Workflows')).toBeInTheDocument()
  })
})
