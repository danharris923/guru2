/**
 * TypeScript interfaces for deal data.
 * Must match the Python Deal model structure for data pipeline compatibility.
 */

export interface Deal {
  id: string;
  title: string;
  imageUrl: string;
  price: number;
  originalPrice?: number;
  discountPercent?: number;
  category: string;
  description: string;
  affiliateUrl: string;
  featured: boolean;
  dateAdded: string; // ISO format
  dataSource: 'PAAPI' | 'SCRAPED' | 'FALLBACK';
  asin: string;
}

export interface DealsState {
  deals: Deal[];
  loading: boolean;
  error: string | null;
  selectedDeal: Deal | null;
}

export interface DealCardProps {
  deal: Deal;
  onClick: () => void;
  showPrice?: boolean;
}

export interface DealModalProps {
  deal: Deal | null;
  isOpen: boolean;
  onClose: () => void;
}

export interface FilterOptions {
  category?: string;
  minDiscount?: number;
  priceRange?: {
    min: number;
    max: number;
  };
  dataSource?: Deal['dataSource'];
}

export interface SortOptions {
  field: 'price' | 'discountPercent' | 'dateAdded' | 'title';
  direction: 'asc' | 'desc';
}

// Utility type for component props
export type DealDisplayProps = Pick<Deal, 'title' | 'price' | 'originalPrice' | 'discountPercent' | 'imageUrl'>;

// Type guards
export function isDeal(obj: any): obj is Deal {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.title === 'string' &&
    typeof obj.imageUrl === 'string' &&
    typeof obj.price === 'number' &&
    typeof obj.category === 'string' &&
    typeof obj.description === 'string' &&
    typeof obj.affiliateUrl === 'string' &&
    typeof obj.featured === 'boolean' &&
    typeof obj.dateAdded === 'string' &&
    ['PAAPI', 'SCRAPED', 'FALLBACK'].includes(obj.dataSource) &&
    typeof obj.asin === 'string'
  );
}

export function isDealsArray(obj: any): obj is Deal[] {
  return Array.isArray(obj) && obj.every(isDeal);
}