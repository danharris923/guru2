/**
 * Sidebar component showing featured deals.
 * Desktop only - hidden on mobile as specified in PRP.
 * Shows top 20 deals with highest discounts in compact layout.
 */

import React, { useState } from 'react';
import { Deal } from '../types/Deal';
import { formatPrice, getDiscountBadgeColor, truncateText } from '../utils/dealUtils';
import { FEATURED_DEALS } from '../utils/constants';

interface SidebarProps {
  deals: Deal[];
  onDealSelect: (deal: Deal) => void;
  selectedDeal?: Deal | null;
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  deals, 
  onDealSelect, 
  selectedDeal,
  className = '' 
}) => {
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  // Get featured deals sorted by discount
  const featuredDeals = deals
    .filter(deal => deal.featured || (deal.discountPercent && deal.discountPercent >= FEATURED_DEALS.MIN_DISCOUNT))
    .sort((a, b) => (b.discountPercent || 0) - (a.discountPercent || 0))
    .slice(0, FEATURED_DEALS.SIDEBAR_COUNT);

  const handleImageError = (dealId: string) => {
    setImageErrors(prev => {
      const newSet = new Set(prev);
      newSet.add(dealId);
      return newSet;
    });
  };

  const handleDealClick = (deal: Deal) => {
    onDealSelect(deal);
  };

  const handleKeyDown = (event: React.KeyboardEvent, deal: Deal) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onDealSelect(deal);
    }
  };

  if (featuredDeals.length === 0) {
    return (
      <aside className={`hidden lg:block ${className}`}>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Featured Deals</h2>
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p>No featured deals available</p>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className={`hidden lg:block ${className}`}>
      <div className="bg-white rounded-lg shadow-sm border">
        {/* Header */}
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Featured Deals</h2>
          <p className="text-sm text-gray-600 mt-1">
            Top {featuredDeals.length} deals with best discounts
          </p>
        </div>

        {/* Featured Deals List */}
        <div className="divide-y max-h-96 overflow-y-auto custom-scrollbar">
          {featuredDeals.map((deal, index) => (
            <div
              key={deal.id}
              className={`
                p-4 hover:bg-gray-50 transition-colors duration-200 cursor-pointer
                focus:outline-none focus:bg-gray-50 focus:ring-2 focus:ring-inset focus:ring-blue-500
                ${selectedDeal?.id === deal.id ? 'bg-blue-50 border-r-4 border-blue-500' : ''}
              `}
              onClick={() => handleDealClick(deal)}
              onKeyDown={(e) => handleKeyDown(e, deal)}
              tabIndex={0}
              role="button"
              aria-label={`View details for ${deal.title}`}
            >
              <div className="flex gap-3">
                {/* Compact Image */}
                <div className="flex-shrink-0">
                  {!imageErrors.has(deal.id) ? (
                    <img
                      src={deal.imageUrl}
                      alt={deal.title}
                      className="w-16 h-16 rounded-lg object-cover bg-gray-100"
                      onError={() => handleImageError(deal.id)}
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                      <span className="text-gray-400 text-lg">📦</span>
                    </div>
                  )}
                </div>

                {/* Deal Info */}
                <div className="flex-1 min-w-0">
                  {/* Title */}
                  <h3 className="text-sm font-medium text-gray-900 truncate-2 mb-1">
                    {truncateText(deal.title, 60)}
                  </h3>

                  {/* Price and Discount */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-green-600">
                        {formatPrice(deal.price)}
                      </span>
                      {deal.originalPrice && deal.originalPrice > deal.price && (
                        <span className="text-xs text-gray-500 line-through">
                          {formatPrice(deal.originalPrice)}
                        </span>
                      )}
                    </div>
                    
                    {deal.discountPercent && deal.discountPercent >= 20 && (
                      <span className={`
                        inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium
                        ${getDiscountBadgeColor(deal.discountPercent)}
                      `}>
                        -{deal.discountPercent}%
                      </span>
                    )}
                  </div>

                  {/* Category and Ranking */}
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 truncate">
                      {deal.category}
                    </span>
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-purple-600 font-medium">#{index + 1}</span>
                      {deal.featured && (
                        <span className="text-xs">⭐</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 bg-gray-50 border-t">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Real Amazon pricing</span>
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
              <span>Live data</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar Stats */}
      <div className="mt-4 bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Deal Stats</h3>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Featured Deals:</span>
            <span className="font-medium text-purple-600">{featuredDeals.length}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Avg. Discount:</span>
            <span className="font-medium text-green-600">
              {Math.round(
                featuredDeals.reduce((acc, deal) => acc + (deal.discountPercent || 0), 0) / 
                featuredDeals.length
              )}%
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Best Deal:</span>
            <span className="font-medium text-red-600">
              -{featuredDeals[0]?.discountPercent || 0}%
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
        <h3 className="text-sm font-medium mb-2">💡 Pro Tip</h3>
        <p className="text-xs opacity-90">
          Click any featured deal for full details and direct Amazon shopping link.
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;