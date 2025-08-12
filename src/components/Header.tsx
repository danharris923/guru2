/**
 * Responsive header component with SavingsGuru branding.
 * Mobile-responsive navigation as specified in PRP.
 */

import React, { useState } from 'react';

interface HeaderProps {
  totalDeals?: number;
  featuredDeals?: number;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ 
  totalDeals = 0, 
  featuredDeals = 0, 
  onRefresh,
  isLoading = false 
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const handleRefresh = () => {
    onRefresh?.();
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              {/* Logo Icon */}
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold text-lg">$</span>
              </div>
              
              {/* Brand Name */}
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  SavingsGuru
                </h1>
                <p className="text-xs text-gray-500 hidden sm:block">Real Amazon Deals</p>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            {/* Stats */}
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <span className="font-medium text-gray-900">{totalDeals}</span>
                <span>Deals</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="font-medium text-purple-600">{featuredDeals}</span>
                <span>Featured</span>
              </div>
            </div>

            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="
                flex items-center gap-2 px-3 py-2 rounded-lg
                bg-gray-100 hover:bg-gray-200 text-gray-700
                transition-colors duration-200
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed
              "
              aria-label="Refresh deals"
            >
              <svg 
                className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
                />
              </svg>
              <span className="hidden lg:inline">Refresh</span>
            </button>

            {/* Data Quality Indicator */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-600">Real Prices</span>
              </div>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={toggleMobileMenu}
              className="
                p-2 rounded-lg hover:bg-gray-100 transition-colors
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              "
              aria-expanded={isMobileMenuOpen}
              aria-label="Toggle mobile menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t py-4 animate-fade-in">
            <div className="space-y-4">
              {/* Mobile Stats */}
              <div className="flex justify-between items-center px-2">
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <span className="font-medium text-gray-900">{totalDeals}</span>
                    <span>Deals</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="font-medium text-purple-600">{featuredDeals}</span>
                    <span>Featured</span>
                  </div>
                </div>
                
                {/* Data Quality Indicator */}
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-600">Real Prices</span>
                </div>
              </div>

              {/* Mobile Actions */}
              <div className="px-2">
                <button
                  onClick={handleRefresh}
                  disabled={isLoading}
                  className="
                    w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg
                    bg-gray-100 hover:bg-gray-200 text-gray-700
                    transition-colors duration-200
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                >
                  <svg 
                    className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
                    />
                  </svg>
                  <span>{isLoading ? 'Refreshing...' : 'Refresh Deals'}</span>
                </button>
              </div>

              {/* Mobile Info */}
              <div className="px-2 pt-2 border-t">
                <p className="text-xs text-gray-500 text-center">
                  Real Amazon prices • No fake data • Updated regularly
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Loading Bar */}
      {isLoading && (
        <div className="absolute bottom-0 left-0 right-0">
          <div className="h-1 bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse"></div>
        </div>
      )}
    </header>
  );
};

export default Header;