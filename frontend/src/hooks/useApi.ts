import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export function useDashboardSummary(symbol: string) {
  return useQuery({
    queryKey: ['dashboard', symbol],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/summary', { params: { symbol } });
      return data;
    },
    enabled: !!symbol,
  });
}
