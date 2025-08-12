/**
 * Custom hook for loading and managing deals data.
 * Handles loading from /deals.json with error handling and retry logic.
 */

import { useState, useEffect, useCallback } from 'react';
import { Deal, DealsState } from '../types/Deal';
import { DATA_CONFIG, ERROR_MESSAGES } from '../utils/constants';
import { validateDeal } from '../utils/dealUtils';

interface UseDealOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function useDeals(options: UseDealOptions = {}) {
  const [state, setState] = useState<DealsState>({
    deals: [],
    loading: true,
    error: null,
    selectedDeal: null,
  });

  const loadDeals = useCallback(async (retryCount = 0): Promise<void> => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      const response = await fetch(DATA_CONFIG.DEALS_FILE_PATH);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to load deals`);
      }

      const data = await response.json();

      // Validate the data structure
      if (!Array.isArray(data)) {
        throw new Error('Invalid data format: expected array of deals');
      }

      // Validate and filter deals
      const validDeals: Deal[] = data
        .filter((item: any) => {
          if (!validateDeal(item)) {
            console.warn('Invalid deal data:', item);
            return false;
          }
          return true;
        })
        .map((item: any): Deal => ({
          ...item,
          // Ensure all required fields have default values
          discountPercent: item.discountPercent || undefined,
          originalPrice: item.originalPrice || undefined,
        }));

      setState(prev => ({
        ...prev,
        deals: validDeals,
        loading: false,
        error: null,
      }));

      console.log(`Loaded ${validDeals.length} valid deals`);

    } catch (error) {
      console.error('Error loading deals:', error);

      // Retry logic
      if (retryCount < DATA_CONFIG.MAX_RETRIES) {
        console.log(`Retrying... (${retryCount + 1}/${DATA_CONFIG.MAX_RETRIES})`);
        setTimeout(() => {
          loadDeals(retryCount + 1);
        }, DATA_CONFIG.RETRY_DELAY * (retryCount + 1));
        return;
      }

      // Set error state after max retries
      let errorMessage: string = ERROR_MESSAGES.LOAD_FAILED;
      
      if (error instanceof Error) {
        if (error.message.includes('404')) {
          errorMessage = ERROR_MESSAGES.NO_DEALS;
        } else if (error.message.includes('network') || error.name === 'TypeError') {
          errorMessage = ERROR_MESSAGES.NETWORK_ERROR;
        }
      }

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  // Auto-refresh setup
  useEffect(() => {
    if (!options.autoRefresh) return;

    const interval = setInterval(() => {
      loadDeals();
    }, options.refreshInterval || DATA_CONFIG.REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [loadDeals, options.autoRefresh, options.refreshInterval]);

  // Deal selection methods
  const selectDeal = useCallback((deal: Deal | null) => {
    setState(prev => ({ ...prev, selectedDeal: deal }));
  }, []);

  const clearSelection = useCallback(() => {
    setState(prev => ({ ...prev, selectedDeal: null }));
  }, []);

  // Manual refresh
  const refresh = useCallback(() => {
    loadDeals();
  }, [loadDeals]);

  return {
    ...state,
    selectDeal,
    clearSelection,
    refresh,
    isRefreshing: state.loading && state.deals.length > 0,
  };
}