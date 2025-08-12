/**
 * Tests for deal utility functions.
 * Tests price formatting, discount calculations, and data processing.
 */

import {
  formatPrice,
  formatPriceCompact,
  calculateDiscountPercent,
  calculateSavings,
  formatDateAdded,
  sortDeals,
  filterDealsByCategory,
  filterDealsByDiscount,
  getUniqueCategories,
  getFeaturedDeals,
  truncateText,
  getDealCardColor,
  hasSignificantDiscount,
  getDiscountBadgeColor,
  validateDeal,
  searchDeals
} from '../../utils/dealUtils';
import { Deal } from '../../types/Deal';

const mockDeals: Deal[] = [
  {
    id: 'deal1',
    title: 'Apple iPhone 13',
    imageUrl: 'https://example.com/iphone.jpg',
    price: 699.99,
    originalPrice: 899.99,
    discountPercent: 22,
    category: 'Electronics',
    description: 'Latest iPhone with amazing features',
    affiliateUrl: 'https://amazon.ca/dp/IPHONE13',
    featured: false,
    dateAdded: '2024-12-10T10:00:00Z',
    dataSource: 'PAAPI',
    asin: 'IPHONE13'
  },
  {
    id: 'deal2',
    title: 'Nike Running Shoes',
    imageUrl: 'https://example.com/shoes.jpg',
    price: 89.99,
    originalPrice: 149.99,
    discountPercent: 40,
    category: 'Clothing',
    description: 'Comfortable running shoes',
    affiliateUrl: 'https://amazon.ca/dp/NIKE123',
    featured: true,
    dateAdded: '2024-12-11T08:00:00Z',
    dataSource: 'SCRAPED',
    asin: 'NIKE123'
  },
  {
    id: 'deal3',
    title: 'Kitchen Knife Set',
    imageUrl: 'https://example.com/knives.jpg',
    price: 49.99,
    originalPrice: 99.99,
    discountPercent: 50,
    category: 'Home & Garden',
    description: 'Professional kitchen knives',
    affiliateUrl: 'https://amazon.ca/dp/KNIFE123',
    featured: true,
    dateAdded: '2024-12-09T15:30:00Z',
    dataSource: 'PAAPI',
    asin: 'KNIFE123'
  }
];

describe('Price Formatting Functions', () => {
  describe('formatPrice', () => {
    it('formats Canadian dollars correctly', () => {
      expect(formatPrice(29.99)).toBe('$29.99');
      expect(formatPrice(1299.50)).toBe('$1,299.50');
      expect(formatPrice(0)).toBe('$0.00');
    });
  });

  describe('formatPriceCompact', () => {
    it('formats prices without currency symbol', () => {
      expect(formatPriceCompact(29.99)).toBe('29.99');
      expect(formatPriceCompact(1299.50)).toBe('1299.50');
    });
  });

  describe('calculateDiscountPercent', () => {
    it('calculates discount percentage correctly', () => {
      expect(calculateDiscountPercent(100, 80)).toBe(20);
      expect(calculateDiscountPercent(50, 25)).toBe(50);
      expect(calculateDiscountPercent(99.99, 49.99)).toBe(50);
    });

    it('returns 0 for invalid inputs', () => {
      expect(calculateDiscountPercent(0, 10)).toBe(0);
      expect(calculateDiscountPercent(100, 0)).toBe(0);
      expect(calculateDiscountPercent(50, 60)).toBe(0); // Current price higher
    });
  });

  describe('calculateSavings', () => {
    it('calculates savings amount correctly', () => {
      expect(calculateSavings(100, 80)).toBe(20);
      expect(calculateSavings(99.99, 49.99)).toBe(50);
    });

    it('returns 0 for invalid inputs', () => {
      expect(calculateSavings(undefined, 50)).toBe(0);
      expect(calculateSavings(100, undefined)).toBe(0);
      expect(calculateSavings(50, 60)).toBe(0); // Current price higher
    });
  });
});

describe('Date Formatting Functions', () => {
  describe('formatDateAdded', () => {
    it('formats recent dates correctly', () => {
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 1000 * 60 * 60);
      const yesterday = new Date(now.getTime() - 1000 * 60 * 60 * 25);
      
      expect(formatDateAdded(oneHourAgo.toISOString())).toBe('1 hours ago');
      expect(formatDateAdded(yesterday.toISOString())).toBe('Yesterday');
    });

    it('handles invalid dates gracefully', () => {
      expect(formatDateAdded('invalid-date')).toBe('Recently');
      expect(formatDateAdded('')).toBe('Recently');
    });
  });
});

describe('Deal Filtering and Sorting Functions', () => {
  describe('sortDeals', () => {
    it('sorts by discount percentage descending', () => {
      const sorted = sortDeals(mockDeals, { field: 'discountPercent', direction: 'desc' });
      
      expect(sorted[0].discountPercent).toBe(50);
      expect(sorted[1].discountPercent).toBe(40);
      expect(sorted[2].discountPercent).toBe(22);
    });

    it('sorts by price ascending', () => {
      const sorted = sortDeals(mockDeals, { field: 'price', direction: 'asc' });
      
      expect(sorted[0].price).toBe(49.99);
      expect(sorted[1].price).toBe(89.99);
      expect(sorted[2].price).toBe(699.99);
    });

    it('sorts by title alphabetically', () => {
      const sorted = sortDeals(mockDeals, { field: 'title', direction: 'asc' });
      
      expect(sorted[0].title).toBe('Apple iPhone 13');
      expect(sorted[1].title).toBe('Kitchen Knife Set');
      expect(sorted[2].title).toBe('Nike Running Shoes');
    });
  });

  describe('filterDealsByCategory', () => {
    it('filters deals by category', () => {
      const electronics = filterDealsByCategory(mockDeals, 'Electronics');
      expect(electronics).toHaveLength(1);
      expect(electronics[0].category).toBe('Electronics');
    });

    it('returns all deals for "All" category', () => {
      const all = filterDealsByCategory(mockDeals, 'All');
      expect(all).toHaveLength(mockDeals.length);
    });

    it('returns empty array for non-existent category', () => {
      const nonExistent = filterDealsByCategory(mockDeals, 'NonExistentCategory');
      expect(nonExistent).toHaveLength(0);
    });
  });

  describe('filterDealsByDiscount', () => {
    it('filters deals by minimum discount', () => {
      const highDiscount = filterDealsByDiscount(mockDeals, 40);
      expect(highDiscount).toHaveLength(2); // 40% and 50% deals
    });

    it('returns empty array when no deals meet threshold', () => {
      const veryHighDiscount = filterDealsByDiscount(mockDeals, 60);
      expect(veryHighDiscount).toHaveLength(0);
    });
  });

  describe('getUniqueCategories', () => {
    it('returns unique categories with "All" first', () => {
      const categories = getUniqueCategories(mockDeals);
      
      expect(categories[0]).toBe('All');
      expect(categories).toContain('Electronics');
      expect(categories).toContain('Clothing');
      expect(categories).toContain('Home & Garden');
      expect(categories).toHaveLength(4); // All + 3 unique categories
    });
  });

  describe('getFeaturedDeals', () => {
    it('returns featured deals first', () => {
      const featured = getFeaturedDeals(mockDeals, 5);
      
      // Should include explicitly featured deals
      expect(featured.some(deal => deal.id === 'deal2')).toBe(true);
      expect(featured.some(deal => deal.id === 'deal3')).toBe(true);
    });

    it('respects limit parameter', () => {
      const featured = getFeaturedDeals(mockDeals, 1);
      expect(featured).toHaveLength(1);
    });
  });

  describe('searchDeals', () => {
    it('searches in title', () => {
      const results = searchDeals(mockDeals, 'iPhone');
      expect(results).toHaveLength(1);
      expect(results[0].title).toBe('Apple iPhone 13');
    });

    it('searches in description', () => {
      const results = searchDeals(mockDeals, 'comfortable');
      expect(results).toHaveLength(1);
      expect(results[0].title).toBe('Nike Running Shoes');
    });

    it('searches in category', () => {
      const results = searchDeals(mockDeals, 'electronics');
      expect(results).toHaveLength(1);
      expect(results[0].category).toBe('Electronics');
    });

    it('returns all deals for empty search term', () => {
      const results = searchDeals(mockDeals, '');
      expect(results).toHaveLength(mockDeals.length);
    });
  });
});

describe('Utility Functions', () => {
  describe('truncateText', () => {
    it('truncates long text with ellipsis', () => {
      const longText = 'This is a very long text that should be truncated';
      const truncated = truncateText(longText, 20);
      
      expect(truncated).toBe('This is a very lo...');
      expect(truncated).toHaveLength(20);
    });

    it('returns original text if under limit', () => {
      const shortText = 'Short text';
      const result = truncateText(shortText, 20);
      
      expect(result).toBe(shortText);
    });
  });

  describe('getDealCardColor', () => {
    it('returns correct color classes for rotation', () => {
      expect(getDealCardColor(0)).toBe('bg-pink-100 border-pink-200');
      expect(getDealCardColor(1)).toBe('bg-blue-100 border-blue-200');
      expect(getDealCardColor(2)).toBe('bg-yellow-100 border-yellow-200');
      expect(getDealCardColor(3)).toBe('bg-pink-100 border-pink-200'); // Cycles back
    });
  });

  describe('hasSignificantDiscount', () => {
    it('identifies significant discounts', () => {
      expect(hasSignificantDiscount(mockDeals[0], 20)).toBe(true); // 22% discount
      expect(hasSignificantDiscount(mockDeals[1], 30)).toBe(true); // 40% discount
      expect(hasSignificantDiscount(mockDeals[0], 30)).toBe(false); // 22% < 30%
    });

    it('handles deals without discount', () => {
      const noDeal = { ...mockDeals[0], discountPercent: undefined };
      expect(hasSignificantDiscount(noDeal, 20)).toBe(false);
    });
  });

  describe('getDiscountBadgeColor', () => {
    it('returns correct colors for discount ranges', () => {
      expect(getDiscountBadgeColor(60)).toBe('bg-red-600 text-white'); // High discount
      expect(getDiscountBadgeColor(40)).toBe('bg-red-500 text-white'); // Good discount
      expect(getDiscountBadgeColor(20)).toBe('bg-orange-500 text-white'); // Medium discount
      expect(getDiscountBadgeColor(10)).toBe('bg-gray-500 text-white'); // Low discount
    });
  });

  describe('validateDeal', () => {
    it('validates correct deal structure', () => {
      expect(validateDeal(mockDeals[0])).toBe(true);
    });

    it('rejects invalid deal structure', () => {
      const invalidDeal = {
        id: 'test',
        // Missing required fields
      };
      
      expect(validateDeal(invalidDeal)).toBe(false);
    });

    it('rejects deals with zero price', () => {
      const zeroPriceDeal = { ...mockDeals[0], price: 0 };
      expect(validateDeal(zeroPriceDeal)).toBe(false);
    });

    it('rejects deals with invalid data source', () => {
      const invalidSourceDeal = { ...mockDeals[0], dataSource: 'INVALID' };
      expect(validateDeal(invalidSourceDeal)).toBe(false);
    });
  });
});