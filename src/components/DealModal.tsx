/**
 * Deal modal component for displaying full deal details.
 * Responsive: full-screen on mobile, sidebar on desktop as specified in PRP.
 */

import React, { useState, useEffect } from 'react';
import { Deal } from '../types/Deal';
import { 
  formatPrice, 
  formatDateAdded, 
  getDiscountBadgeColor,
  calculateSavings 
} from '../utils/dealUtils';
import { DATA_SOURCE_CONFIG, CATEGORY_COLORS } from '../utils/constants';

interface DealModalProps {
  deal: Deal | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DealModal: React.FC<DealModalProps> = ({ deal, isOpen, onClose }) => {
  const [imageError, setImageError] = useState(false);

  // Reset image error when deal changes
  useEffect(() => {
    setImageError(false);
  }, [deal]);

  // Close on escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Handle backdrop click
  const handleBackdropClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  // Handle shop now click
  const handleShopNow = () => {
    if (deal) {
      window.open(deal.affiliateUrl, '_blank', 'noopener,noreferrer');
    }
  };

  if (!isOpen || !deal) return null;

  const savings = calculateSavings(deal.originalPrice, deal.price);
  const dataSourceConfig = DATA_SOURCE_CONFIG[deal.dataSource];
  const categoryColor = CATEGORY_COLORS[deal.category] || CATEGORY_COLORS['General'];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm transition-opacity"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />

      {/* Modal Container */}
      <div className="flex min-h-full items-center justify-center p-4 sm:p-0">
        {/* Mobile: Full screen modal */}
        <div className="block sm:hidden w-full h-full">
          <div className="glass-modal w-full h-full rounded-none overflow-y-auto animate-slide-up">
            {/* Mobile Header */}
            <div className="sticky top-0 bg-white bg-opacity-90 backdrop-blur-sm border-b p-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 truncate">
                Deal Details
              </h2>
              <button
                onClick={onClose}
                className="
                  p-2 rounded-lg hover:bg-gray-100 transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                "
                aria-label="Close modal"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Mobile Content */}
            <div className="p-4 pb-20">
              <DealModalContent 
                deal={deal} 
                imageError={imageError}
                setImageError={setImageError}
                onShopNow={handleShopNow}
                savings={savings}
                dataSourceConfig={dataSourceConfig}
                categoryColor={categoryColor}
              />
            </div>

            {/* Mobile CTA Footer */}
            <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 safe-bottom">
              <button
                onClick={handleShopNow}
                className="gradient-button w-full justify-center flex items-center gap-2"
              >
                <span>Shop Now on Amazon</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Desktop: Sidebar modal */}
        <div className="hidden sm:block fixed right-0 top-0 h-full w-full max-w-lg">
          <div className="glass-modal h-full shadow-xl animate-fade-in overflow-y-auto">
            {/* Desktop Header */}
            <div className="sticky top-0 bg-white bg-opacity-90 backdrop-blur-sm border-b p-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                Deal Details
              </h2>
              <button
                onClick={onClose}
                className="
                  p-2 rounded-lg hover:bg-gray-100 transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                "
                aria-label="Close modal"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Desktop Content */}
            <div className="p-6 pb-24">
              <DealModalContent 
                deal={deal} 
                imageError={imageError}
                setImageError={setImageError}
                onShopNow={handleShopNow}
                savings={savings}
                dataSourceConfig={dataSourceConfig}
                categoryColor={categoryColor}
              />
            </div>

            {/* Desktop CTA Footer */}
            <div className="absolute bottom-0 left-0 right-0 bg-white border-t p-6">
              <button
                onClick={handleShopNow}
                className="gradient-button w-full justify-center flex items-center gap-2"
              >
                <span>Shop Now on Amazon</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Shared content component for both mobile and desktop
interface DealModalContentProps {
  deal: Deal;
  imageError: boolean;
  setImageError: (error: boolean) => void;
  onShopNow: () => void;
  savings: number;
  dataSourceConfig: typeof DATA_SOURCE_CONFIG[keyof typeof DATA_SOURCE_CONFIG];
  categoryColor: string;
}

const DealModalContent: React.FC<DealModalContentProps> = ({
  deal,
  imageError,
  setImageError,
  savings,
  dataSourceConfig,
  categoryColor
}) => {
  return (
    <div className="space-y-6">
      {/* Product Image */}
      <div className="relative">
        {!imageError ? (
          <img
            src={deal.imageUrl}
            alt={deal.title}
            className="w-full h-auto rounded-lg shadow-sm max-h-96 object-contain bg-white"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <span className="text-gray-400 text-6xl">🖼️</span>
          </div>
        )}

        {/* Featured badge */}
        {deal.featured && (
          <div className="absolute top-3 left-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              ⭐ Featured Deal
            </span>
          </div>
        )}

        {/* Discount badge */}
        {deal.discountPercent && deal.discountPercent >= 20 && (
          <div className="absolute top-3 right-3">
            <span className={`discount-badge ${getDiscountBadgeColor(deal.discountPercent)} text-lg`}>
              {deal.discountPercent}% OFF
            </span>
          </div>
        )}
      </div>

      {/* Product Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 leading-tight">
          {deal.title}
        </h1>
      </div>

      {/* Price Information */}
      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-3xl font-bold text-green-600">
            {formatPrice(deal.price)}
          </span>
          {deal.originalPrice && deal.originalPrice > deal.price && (
            <div className="text-right">
              <div className="text-lg text-gray-500 line-through">
                {formatPrice(deal.originalPrice)}
              </div>
              {savings > 0 && (
                <div className="text-green-600 font-medium">
                  Save {formatPrice(savings)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Data source info */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Price from:</span>
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${dataSourceConfig.color}`}>
            {dataSourceConfig.icon} {dataSourceConfig.label}
          </span>
        </div>
      </div>

      {/* Category and Meta Info */}
      <div className="flex flex-wrap gap-2">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${categoryColor}`}>
          {deal.category}
        </span>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
          ASIN: {deal.asin}
        </span>
      </div>

      {/* Description */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
        <p className="text-gray-700 leading-relaxed">
          {deal.description}
        </p>
      </div>

      {/* Additional Information */}
      <div className="border-t pt-4 space-y-3">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">Added:</span>
          <span className="text-gray-900">{formatDateAdded(deal.dateAdded)}</span>
        </div>
        
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">Deal ID:</span>
          <span className="text-gray-900 font-mono text-xs">{deal.id}</span>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-blue-50 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          <span className="font-medium">Note:</span> Prices and availability are subject to change. 
          As an Amazon Associate, we earn from qualifying purchases. All prices shown are in Canadian dollars.
        </p>
      </div>
    </div>
  );
};

export default DealModal;