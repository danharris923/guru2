/**
 * Main App component orchestrating the entire application.
 * Handles deal loading, modal state, and responsive layout with sidebar and main grid.
 */

import React from 'react';
import { useDeals } from './hooks/useDeals';
import { useModal } from './hooks/useModal';
import Header from './components/Header';
import HomePage from './components/HomePage';
import Sidebar from './components/Sidebar';
import DealModal from './components/DealModal';
import { getFeaturedDeals } from './utils/dealUtils';
import './index.css';

const App: React.FC = () => {
  const { deals, loading, error, selectedDeal, selectDeal, clearSelection, refresh, isRefreshing } = useDeals({
    autoRefresh: true,
    refreshInterval: 300000, // 5 minutes
  });

  const { isOpen: isModalOpen, openModal, closeModal } = useModal({
    closeOnEscape: true,
    closeOnBackdropClick: true,
    preventBodyScroll: true,
  });

  // Handle deal selection
  const handleDealSelect = (deal: any) => {
    selectDeal(deal);
    openModal();
  };

  // Handle modal close
  const handleModalClose = () => {
    closeModal();
    // Clear selection after modal animation completes
    setTimeout(() => clearSelection(), 300);
  };

  // Get featured deals for sidebar
  const featuredDeals = getFeaturedDeals(deals, 20);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <Header
        totalDeals={deals.length}
        featuredDeals={featuredDeals.length}
        onRefresh={refresh}
        isLoading={loading || isRefreshing}
      />

      {/* Main Layout */}
      <div className="flex-1 flex">
        {/* Main Content */}
        <div className="flex-1 lg:mr-80">
          <HomePage
            deals={deals}
            onDealSelect={handleDealSelect}
            loading={loading}
            error={error}
          />
        </div>

        {/* Sidebar - Desktop Only */}
        <Sidebar
          deals={deals}
          onDealSelect={handleDealSelect}
          selectedDeal={selectedDeal}
          className="fixed right-0 top-16 h-[calc(100vh-4rem)] w-80 overflow-y-auto p-6"
        />
      </div>

      {/* Deal Modal */}
      <DealModal
        deal={selectedDeal}
        isOpen={isModalOpen}
        onClose={handleModalClose}
      />

      {/* Skip to main content link for accessibility */}
      <a
        href="#main-content"
        className="
          sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4
          bg-blue-600 text-white px-4 py-2 rounded-lg z-50
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        "
      >
        Skip to main content
      </a>

      {/* App Info Footer - Only visible when no deals are loading */}
      {!loading && deals.length > 0 && (
        <footer className="bg-white border-t py-4 px-4 lg:mr-80">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-gray-600">
              <div className="flex items-center gap-4 mb-2 sm:mb-0">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  Real Amazon pricing
                </span>
                <span>No fake data</span>
                <span>Updated regularly</span>
              </div>
              
              <div className="flex items-center gap-4 text-xs">
                <span>
                  Data from: Amazon API & Web Scraping
                </span>
                <a 
                  href="#" 
                  className="text-blue-600 hover:text-blue-800"
                  onClick={(e) => {
                    e.preventDefault();
                    // Could open an info modal about data sources
                  }}
                >
                  Learn more
                </a>
              </div>
            </div>
          </div>
        </footer>
      )}

      {/* Error boundary - could be enhanced with proper error boundary component */}
      {error && (
        <div 
          className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded max-w-sm z-50"
          role="alert"
        >
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium">Error loading deals</h3>
              <div className="text-sm mt-1">
                {error}
              </div>
              <div className="mt-2">
                <button
                  onClick={refresh}
                  className="text-sm bg-red-200 hover:bg-red-300 text-red-800 px-3 py-1 rounded transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;