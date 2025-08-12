/**
 * Price visibility logic - determines which cards show prices vs "Check Price" buttons.
 * As specified in the PRP, ~10% of cards should show visible prices.
 */

/**
 * Determine if price should be visible for a given deal ID
 * Uses hash-based approach for consistent results
 */
export function shouldShowPrice(dealId: string): boolean {
  // Use hash of deal ID to determine visibility
  const hash = simpleHash(dealId);
  
  // Show price for ~10% of deals (hash ending in specific digits)
  return hash % 10 === 0;
}

/**
 * Simple hash function for consistent price visibility
 */
function simpleHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

/**
 * Custom hook for price visibility with local storage persistence
 */
export function usePriceVisibilityState() {
  const getVisibilityOverrides = (): Record<string, boolean> => {
    try {
      const stored = localStorage.getItem('priceVisibilityOverrides');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  };

  const setVisibilityOverride = (dealId: string, visible: boolean): void => {
    try {
      const overrides = getVisibilityOverrides();
      overrides[dealId] = visible;
      localStorage.setItem('priceVisibilityOverrides', JSON.stringify(overrides));
    } catch {
      // Silently fail if localStorage is not available
    }
  };

  const clearVisibilityOverrides = (): void => {
    try {
      localStorage.removeItem('priceVisibilityOverrides');
    } catch {
      // Silently fail if localStorage is not available
    }
  };

  const isPriceVisible = (dealId: string): boolean => {
    const overrides = getVisibilityOverrides();
    
    // Check for manual override first
    if (dealId in overrides) {
      return overrides[dealId];
    }
    
    // Use default hash-based logic
    return shouldShowPrice(dealId);
  };

  return {
    isPriceVisible,
    setVisibilityOverride,
    clearVisibilityOverrides,
  };
}

/**
 * Get price visibility statistics for debugging/admin
 */
export function getPriceVisibilityStats(dealIds: string[]): {
  total: number;
  visible: number;
  hidden: number;
  percentage: number;
} {
  const visible = dealIds.filter(shouldShowPrice).length;
  const total = dealIds.length;
  const hidden = total - visible;
  const percentage = total > 0 ? (visible / total) * 100 : 0;

  return {
    total,
    visible,
    hidden,
    percentage: Math.round(percentage * 10) / 10, // Round to 1 decimal
  };
}

/**
 * Batch update price visibility for multiple deals
 */
export function updateBatchPriceVisibility(
  dealIds: string[], 
  visiblePercentage: number = 10
): Record<string, boolean> {
  const visibilityMap: Record<string, boolean> = {};
  const targetVisible = Math.round((dealIds.length * visiblePercentage) / 100);
  
  // Sort deal IDs by hash to ensure consistent selection
  const sortedIds = dealIds
    .map(id => ({ id, hash: simpleHash(id) }))
    .sort((a, b) => a.hash - b.hash)
    .map(item => item.id);
  
  // Mark first N deals as visible based on target percentage
  sortedIds.forEach((id, index) => {
    visibilityMap[id] = index < targetVisible;
  });
  
  return visibilityMap;
}