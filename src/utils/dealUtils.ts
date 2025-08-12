/**
 * Utility functions for deal data processing and formatting.
 * Handles price formatting, discount calculations, and data sorting.
 */

import { Deal, SortOptions } from '../types/Deal';

/**
 * Format price in Canadian dollars
 */
export function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price);
}

/**
 * Format price without currency symbol (for compact display)
 */
export function formatPriceCompact(price: number): string {
  return price.toFixed(2);
}

/**
 * Calculate discount percentage between original and current price
 */
export function calculateDiscountPercent(originalPrice: number, currentPrice: number): number {
  if (originalPrice <= 0 || currentPrice <= 0 || currentPrice >= originalPrice) {
    return 0;
  }
  
  return Math.round(((originalPrice - currentPrice) / originalPrice) * 100);
}

/**
 * Calculate savings amount in dollars
 */
export function calculateSavings(originalPrice?: number, currentPrice?: number): number {
  if (!originalPrice || !currentPrice || currentPrice >= originalPrice) {
    return 0;
  }
  
  return originalPrice - currentPrice;
}

/**
 * Format date for display (relative time)
 */
export function formatDateAdded(dateAdded: string): string {
  try {
    const date = new Date(dateAdded);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just added';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} hours ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-CA', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  } catch (error) {
    return 'Recently';
  }
}

/**
 * Sort deals based on provided options
 */
export function sortDeals(deals: Deal[], sortOptions: SortOptions): Deal[] {
  return [...deals].sort((a, b) => {
    let aValue: any;
    let bValue: any;
    
    switch (sortOptions.field) {
      case 'price':
        aValue = a.price;
        bValue = b.price;
        break;
      case 'discountPercent':
        aValue = a.discountPercent || 0;
        bValue = b.discountPercent || 0;
        break;
      case 'dateAdded':
        aValue = new Date(a.dateAdded).getTime();
        bValue = new Date(b.dateAdded).getTime();
        break;
      case 'title':
        aValue = a.title.toLowerCase();
        bValue = b.title.toLowerCase();
        break;
      default:
        return 0;
    }
    
    if (sortOptions.direction === 'desc') {
      return bValue > aValue ? 1 : bValue < aValue ? -1 : 0;
    } else {
      return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
    }
  });
}

/**
 * Filter deals based on category
 */
export function filterDealsByCategory(deals: Deal[], category: string): Deal[] {
  if (!category || category === 'All') {
    return deals;
  }
  
  return deals.filter(deal => deal.category === category);
}

/**
 * Filter deals by minimum discount percentage
 */
export function filterDealsByDiscount(deals: Deal[], minDiscount: number): Deal[] {
  return deals.filter(deal => (deal.discountPercent || 0) >= minDiscount);
}

/**
 * Get unique categories from deals
 */
export function getUniqueCategories(deals: Deal[]): string[] {
  const categories = new Set(deals.map(deal => deal.category));
  return ['All', ...Array.from(categories).sort()];
}

/**
 * Get featured deals (marked as featured or high discount)
 */
export function getFeaturedDeals(deals: Deal[], limit: number = 20): Deal[] {
  // First get explicitly featured deals
  const featured = deals.filter(deal => deal.featured);
  
  if (featured.length >= limit) {
    return featured.slice(0, limit);
  }
  
  // If not enough featured deals, add high-discount deals
  const nonFeatured = deals
    .filter(deal => !deal.featured)
    .filter(deal => (deal.discountPercent || 0) >= 30)
    .sort((a, b) => (b.discountPercent || 0) - (a.discountPercent || 0));
  
  return [...featured, ...nonFeatured].slice(0, limit);
}

/**
 * Truncate text to specified length
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Get color class for deal card background
 */
export function getDealCardColor(index: number): string {
  const colors = [
    'bg-pink-100 border-pink-200',
    'bg-blue-100 border-blue-200', 
    'bg-yellow-100 border-yellow-200'
  ];
  
  return colors[index % colors.length];
}

/**
 * Check if a deal has a significant discount
 */
export function hasSignificantDiscount(deal: Deal, threshold: number = 20): boolean {
  return (deal.discountPercent || 0) >= threshold;
}

/**
 * Get discount badge color based on percentage
 */
export function getDiscountBadgeColor(discountPercent: number): string {
  if (discountPercent >= 50) {
    return 'bg-red-600 text-white';
  } else if (discountPercent >= 30) {
    return 'bg-red-500 text-white';
  } else if (discountPercent >= 15) {
    return 'bg-orange-500 text-white';
  } else {
    return 'bg-gray-500 text-white';
  }
}

/**
 * Validate deal data structure
 */
export function validateDeal(deal: any): deal is Deal {
  return (
    typeof deal?.id === 'string' &&
    typeof deal?.title === 'string' &&
    typeof deal?.price === 'number' && deal.price > 0 &&
    typeof deal?.affiliateUrl === 'string' &&
    ['PAAPI', 'SCRAPED', 'FALLBACK'].includes(deal?.dataSource)
  );
}

/**
 * Search deals by title or description
 */
export function searchDeals(deals: Deal[], searchTerm: string): Deal[] {
  if (!searchTerm.trim()) {
    return deals;
  }
  
  const term = searchTerm.toLowerCase().trim();
  
  return deals.filter(deal => 
    deal.title.toLowerCase().includes(term) ||
    deal.description.toLowerCase().includes(term) ||
    deal.category.toLowerCase().includes(term)
  );
}