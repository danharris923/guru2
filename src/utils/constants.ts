/**
 * Application constants and configuration.
 * Centralized configuration for colors, breakpoints, and other settings.
 */

// Card background colors for rotation (as specified in PRP)
export const CARD_COLORS = [
  { bg: 'bg-pink-100', border: 'border-pink-200', hover: 'hover:bg-pink-200' },
  { bg: 'bg-blue-100', border: 'border-blue-200', hover: 'hover:bg-blue-200' },
  { bg: 'bg-yellow-100', border: 'border-yellow-200', hover: 'hover:bg-yellow-200' },
] as const;

// Discount thresholds for styling and features
export const DISCOUNT_THRESHOLDS = {
  SIGNIFICANT: 20, // Show discount badge
  HIGH: 40,       // Featured deal threshold
  PREMIUM: 60,    // Premium styling
} as const;

// Featured deals configuration
export const FEATURED_DEALS = {
  MAX_COUNT: 20,           // Maximum featured deals to show
  MIN_DISCOUNT: 40,        // Minimum discount for featured status
  SIDEBAR_COUNT: 15,       // Number of deals to show in sidebar
} as const;

// Price visibility configuration
export const PRICE_VISIBILITY = {
  VISIBLE_PERCENTAGE: 10,  // Percentage of cards showing prices
  STORAGE_KEY: 'priceVisibilityOverrides',
} as const;

// Layout breakpoints (matching Tailwind config)
export const BREAKPOINTS = {
  XS: 475,
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,
} as const;

// Animation durations (in milliseconds)
export const ANIMATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

// API and data configuration
export const DATA_CONFIG = {
  DEALS_FILE_PATH: '/deals.json',
  REFRESH_INTERVAL: 300000, // 5 minutes
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
} as const;

// Image configuration
export const IMAGE_CONFIG = {
  PLACEHOLDER: '/placeholder-image.jpg',
  LAZY_LOADING_THRESHOLD: 100, // pixels from viewport
  MAX_WIDTH: 800,
  QUALITY: 85,
} as const;

// Modal configuration
export const MODAL_CONFIG = {
  BACKDROP_BLUR: 'backdrop-blur-sm',
  ANIMATION_CLASS: 'animate-fade-in',
  CLOSE_ON_BACKDROP_CLICK: true,
} as const;

// Category colors for better visual distinction
export const CATEGORY_COLORS: Record<string, string> = {
  'Electronics': 'bg-blue-100 text-blue-800',
  'Home & Garden': 'bg-green-100 text-green-800', 
  'Clothing': 'bg-purple-100 text-purple-800',
  'Books': 'bg-orange-100 text-orange-800',
  'Toys & Games': 'bg-pink-100 text-pink-800',
  'Health & Beauty': 'bg-rose-100 text-rose-800',
  'Sports': 'bg-emerald-100 text-emerald-800',
  'General': 'bg-gray-100 text-gray-800',
} as const;

// Data source indicators
export const DATA_SOURCE_CONFIG = {
  PAAPI: {
    label: 'Amazon API',
    color: 'bg-green-100 text-green-800',
    icon: '✓',
  },
  SCRAPED: {
    label: 'Web Data',
    color: 'bg-blue-100 text-blue-800',
    icon: '◯',
  },
  FALLBACK: {
    label: 'Backup',
    color: 'bg-yellow-100 text-yellow-800',
    icon: '△',
  },
} as const;

// Sorting options for deals
export const SORT_OPTIONS = [
  { value: 'discountPercent-desc', label: 'Highest Discount' },
  { value: 'discountPercent-asc', label: 'Lowest Discount' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'dateAdded-desc', label: 'Newest First' },
  { value: 'dateAdded-asc', label: 'Oldest First' },
  { value: 'title-asc', label: 'Name: A to Z' },
  { value: 'title-desc', label: 'Name: Z to A' },
] as const;

// Loading states
export const LOADING_MESSAGES = [
  'Loading amazing deals...',
  'Fetching real Amazon prices...',
  'Finding the best discounts...',
  'Updating deal information...',
] as const;

// Error messages
export const ERROR_MESSAGES = {
  LOAD_FAILED: 'Failed to load deals. Please refresh the page.',
  NO_DEALS: 'No deals found. Please check back later.',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  PARSE_ERROR: 'Failed to process deal data.',
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  DEALS_LOADED: 'Deals loaded successfully!',
  DATA_REFRESHED: 'Deal data refreshed!',
} as const;

// Accessibility
export const A11Y = {
  SKIP_LINK_TARGET: 'main-content',
  FOCUS_VISIBLE_CLASS: 'focus-visible:ring-2 focus-visible:ring-blue-500',
  HIGH_CONTRAST_CLASS: 'high-contrast',
} as const;

// Performance
export const PERFORMANCE = {
  VIRTUAL_SCROLL_THRESHOLD: 100, // Enable virtual scrolling after N items
  DEBOUNCE_DELAY: 300,          // Debounce delay for search/filter
  IMAGE_INTERSECTION_THRESHOLD: 0.1, // Lazy loading threshold
} as const;