/**
 * Individual deal card component with responsive design and price display logic.
 * Implements color rotation, lazy loading, and price visibility as specified in PRP.
 */

import React, { useState } from 'react';
import { Deal } from '../types/Deal';
import { 
  formatPrice, 
  getDealCardColor, 
  hasSignificantDiscount, 
  getDiscountBadgeColor,
  truncateText 
} from '../utils/dealUtils';
import { shouldShowPrice } from '../utils/priceVisibility';
import { CARD_COLORS, DISCOUNT_THRESHOLDS } from '../utils/constants';

interface DealCardProps {
  deal: Deal;
  onClick: () => void;
  index: number;
  showPrice?: boolean;
}

export const DealCard: React.FC<DealCardProps> = ({ 
  deal, 
  onClick, 
  index,
  showPrice: overrideShowPrice 
}) => {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Determine if price should be visible
  const shouldShowPriceValue = overrideShowPrice ?? shouldShowPrice(deal.id);

  // Get card colors based on rotation
  const colorConfig = CARD_COLORS[index % CARD_COLORS.length];

  // Handle image error
  const handleImageError = () => {
    setImageError(true);
  };

  // Handle image load
  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  // Handle card click
  const handleClick = () => {
    onClick();
  };

  // Handle keyboard interaction
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={`
        ${colorConfig.bg} ${colorConfig.border} ${colorConfig.hover}
        deal-card masonry-item
        border rounded-lg shadow-md cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        group relative overflow-hidden
      `}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${deal.title}`}
    >
      {/* Featured deal glow effect */}
      {deal.featured && (
        <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-500 to-purple-500 rounded-lg blur opacity-20 group-hover:opacity-40 transition duration-300" />
      )}
      
      <div className="relative">
        {/* Product Image */}
        <div className="relative overflow-hidden rounded-t-lg bg-white">
          {!imageLoaded && !imageError && (
            <div className="image-placeholder aspect-square animate-pulse bg-gray-200 flex items-center justify-center">
              <span className="text-gray-400 text-2xl">📷</span>
            </div>
          )}
          
          {!imageError ? (
            <img
              src={deal.imageUrl}
              alt={deal.title}
              loading="lazy"
              className={`
                w-full h-auto rounded-t-lg transition-opacity duration-300
                ${imageLoaded ? 'opacity-100' : 'opacity-0'}
              `}
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          ) : (
            <div className="aspect-square bg-gray-100 flex items-center justify-center text-gray-500">
              <span className="text-4xl">🖼️</span>
              <span className="sr-only">Image not available</span>
            </div>
          )}

          {/* Data source indicator */}
          <div className="absolute top-2 right-2">
            <span 
              className={`
                inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                ${deal.dataSource === 'PAAPI' ? 'data-source-paapi' : 
                  deal.dataSource === 'SCRAPED' ? 'data-source-scraped' : 
                  'data-source-fallback'}
              `}
              title={`Data source: ${deal.dataSource}`}
            >
              {deal.dataSource === 'PAAPI' ? '✓' : 
               deal.dataSource === 'SCRAPED' ? '◯' : '△'}
            </span>
          </div>

          {/* Discount badge for significant discounts */}
          {deal.discountPercent && deal.discountPercent >= DISCOUNT_THRESHOLDS.SIGNIFICANT && (
            <div className="absolute top-2 left-2">
              <span 
                className={`
                  discount-badge ${getDiscountBadgeColor(deal.discountPercent)}
                  animate-pulse-slow
                `}
              >
                {deal.discountPercent}% OFF
              </span>
            </div>
          )}
        </div>

        {/* Card Content */}
        <div className="p-4 space-y-3">
          {/* Product Title */}
          <h3 className="font-semibold text-gray-800 truncate-2 group-hover:text-gray-900 transition-colors">
            {truncateText(deal.title, 80)}
          </h3>

          {/* Category */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
              {deal.category}
            </span>
            {deal.featured && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gold-100 text-gold-800">
                ⭐ Featured
              </span>
            )}
          </div>

          {/* Price Display or Check Price Button */}
          <div className="flex items-center justify-between">
            {shouldShowPriceValue ? (
              <div className="flex items-center gap-2">
                <span className="price-current">
                  {formatPrice(deal.price)}
                </span>
                {deal.originalPrice && deal.originalPrice > deal.price && (
                  <span className="price-original">
                    {formatPrice(deal.originalPrice)}
                  </span>
                )}
              </div>
            ) : (
              <button
                className="
                  bg-blue-500 hover:bg-blue-600 text-white 
                  px-4 py-2 rounded-lg text-sm font-medium
                  transition-colors duration-200
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                "
                onClick={(e) => {
                  e.stopPropagation();
                  onClick();
                }}
              >
                Check Price
              </button>
            )}

            {/* Savings amount */}
            {deal.originalPrice && deal.originalPrice > deal.price && (
              <div className="text-right">
                <span className="text-green-600 text-sm font-medium">
                  Save {formatPrice(deal.originalPrice - deal.price)}
                </span>
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              ASIN: {deal.asin}
            </span>
            <button
              className="
                text-blue-600 hover:text-blue-800 text-sm font-medium
                transition-colors duration-200
              "
              onClick={(e) => {
                e.stopPropagation();
                window.open(deal.affiliateUrl, '_blank', 'noopener,noreferrer');
              }}
              aria-label={`Shop ${deal.title} on Amazon`}
            >
              Shop Now →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DealCard;