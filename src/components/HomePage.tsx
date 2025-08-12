/**
 * Main homepage component with masonry grid layout for deal cards.
 * Implements responsive breakpoints, loading states, and error handling.
 */

import React, { useState, useMemo } from 'react';
import { Deal } from '../types/Deal';
import DealCard from './DealCard';
import { 
  sortDeals, 
  filterDealsByCategory, 
  filterDealsByDiscount, 
  getUniqueCategories,
  searchDeals 
} from '../utils/dealUtils';
import { SORT_OPTIONS, LOADING_MESSAGES, ERROR_MESSAGES } from '../utils/constants';

interface HomePageProps {
  deals: Deal[];
  onDealSelect: (deal: Deal) => void;
  loading?: boolean;
  error?: string | null;
}

export const HomePage: React.FC<HomePageProps> = ({ 
  deals, 
  onDealSelect, 
  loading = false, 
  error = null 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedSort, setSelectedSort] = useState('discountPercent-desc');
  const [minDiscount, setMinDiscount] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

  // Get unique categories for filter dropdown
  const categories = useMemo(() => getUniqueCategories(deals), [deals]);

  // Apply filters and sorting
  const filteredAndSortedDeals = useMemo(() => {
    let filtered = deals;

    // Apply search
    if (searchTerm.trim()) {
      filtered = searchDeals(filtered, searchTerm);
    }

    // Apply category filter
    filtered = filterDealsByCategory(filtered, selectedCategory);

    // Apply discount filter
    if (minDiscount > 0) {
      filtered = filterDealsByDiscount(filtered, minDiscount);
    }

    // Apply sorting
    const [field, direction] = selectedSort.split('-') as [string, 'asc' | 'desc'];
    filtered = sortDeals(filtered, { field: field as any, direction });

    return filtered;
  }, [deals, searchTerm, selectedCategory, selectedSort, minDiscount]);

  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  // Handle category change
  const handleCategoryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(event.target.value);
  };

  // Handle sort change
  const handleSortChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSort(event.target.value);
  };

  // Handle discount filter change
  const handleDiscountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setMinDiscount(Number(event.target.value));
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('');
    setSelectedCategory('All');
    setSelectedSort('discountPercent-desc');
    setMinDiscount(0);
  };

  // Loading state
  if (loading && deals.length === 0) {
    return (
      <main className="flex-1 p-4 lg:p-6" id="main-content">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">
              {LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)]}
            </p>
          </div>
          
          {/* Loading skeleton grid */}
          <div className="masonry masonry-sm sm:masonry-md lg:masonry-lg gap-4">
            {Array.from({ length: 12 }).map((_, index) => (
              <div key={index} className="masonry-item">
                <div className="bg-white rounded-lg shadow-md overflow-hidden animate-pulse">
                  <div className="aspect-square bg-gray-200"></div>
                  <div className="p-4 space-y-3">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    <div className="flex justify-between">
                      <div className="h-6 bg-gray-200 rounded w-20"></div>
                      <div className="h-8 bg-gray-200 rounded w-24"></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    );
  }

  // Error state
  if (error) {
    return (
      <main className="flex-1 p-4 lg:p-6" id="main-content">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Oops! Something went wrong</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="gradient-button"
            >
              Try Again
            </button>
          </div>
        </div>
      </main>
    );
  }

  // No deals state
  if (!loading && deals.length === 0) {
    return (
      <main className="flex-1 p-4 lg:p-6" id="main-content">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">🛍️</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No deals available</h2>
            <p className="text-gray-600">Check back later for amazing deals with real pricing!</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-4 lg:p-6" id="main-content">
      <div className="max-w-7xl mx-auto">
        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search deals..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="
                block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                placeholder-gray-500 text-sm
              "
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Filter Toggle Button (Mobile) */}
          <div className="sm:hidden">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="
                flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300
                hover:bg-gray-50 transition-colors duration-200
              "
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
              </svg>
              <span>Filters</span>
              <span className="text-sm text-gray-500">
                ({filteredAndSortedDeals.length})
              </span>
            </button>
          </div>

          {/* Filters Row */}
          <div className={`
            grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-center
            ${showFilters ? 'block' : 'hidden sm:grid'}
          `}>
            {/* Category Filter */}
            <div>
              <label htmlFor="category-select" className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                id="category-select"
                value={selectedCategory}
                onChange={handleCategoryChange}
                className="
                  block w-full px-3 py-2 border border-gray-300 rounded-lg
                  focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm
                "
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Filter */}
            <div>
              <label htmlFor="sort-select" className="block text-sm font-medium text-gray-700 mb-1">
                Sort by
              </label>
              <select
                id="sort-select"
                value={selectedSort}
                onChange={handleSortChange}
                className="
                  block w-full px-3 py-2 border border-gray-300 rounded-lg
                  focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm
                "
              >
                {SORT_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Discount Filter */}
            <div>
              <label htmlFor="discount-range" className="block text-sm font-medium text-gray-700 mb-1">
                Min Discount: {minDiscount}%
              </label>
              <input
                id="discount-range"
                type="range"
                min="0"
                max="80"
                step="10"
                value={minDiscount}
                onChange={handleDiscountChange}
                className="
                  block w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer
                  slider:bg-blue-600
                "
              />
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="
                  w-full sm:w-auto px-4 py-2 text-sm font-medium text-gray-700
                  bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200
                  focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
                "
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="flex items-center justify-between mb-6">
          <div className="text-sm text-gray-600">
            Showing <span className="font-medium">{filteredAndSortedDeals.length}</span> of{' '}
            <span className="font-medium">{deals.length}</span> deals
          </div>
          
          {loading && (
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              Updating...
            </div>
          )}
        </div>

        {/* Deal Cards Grid */}
        {filteredAndSortedDeals.length > 0 ? (
          <div className="masonry masonry-sm sm:masonry-md lg:masonry-lg gap-4">
            {filteredAndSortedDeals.map((deal, index) => (
              <DealCard
                key={deal.id}
                deal={deal}
                index={index}
                onClick={() => onDealSelect(deal)}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No deals found</h3>
            <p className="text-gray-500 mb-4">
              Try adjusting your search terms or filters to find more deals.
            </p>
            <button
              onClick={clearFilters}
              className="gradient-button"
            >
              Clear All Filters
            </button>
          </div>
        )}
      </div>
    </main>
  );
};

export default HomePage;