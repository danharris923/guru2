/**
 * Tests for DealCard component.
 * Tests responsive behavior, price display logic, and modal interactions.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DealCard } from '../../components/DealCard';
import { Deal } from '../../types/Deal';

// Mock the price visibility utility
jest.mock('../../utils/priceVisibility', () => ({
  shouldShowPrice: jest.fn((dealId: string) => dealId.includes('show-price'))
}));

const mockDeal: Deal = {
  id: 'test-deal-show-price',
  title: 'Test Product Title',
  imageUrl: 'https://example.com/image.jpg',
  price: 29.99,
  originalPrice: 49.99,
  discountPercent: 40,
  category: 'Electronics',
  description: 'Test product description',
  affiliateUrl: 'https://amazon.ca/dp/TEST123?tag=test-20',
  featured: false,
  dateAdded: '2024-12-11T10:00:00Z',
  dataSource: 'PAAPI',
  asin: 'TEST123'
};

const mockOnClick = jest.fn();

describe('DealCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders deal card with basic information', () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    expect(screen.getByText('Test Product Title')).toBeInTheDocument();
    expect(screen.getByText('Electronics')).toBeInTheDocument();
    expect(screen.getByText('ASIN: TEST123')).toBeInTheDocument();
  });

  it('displays price when shouldShowPrice returns true', () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    expect(screen.getByText('$29.99')).toBeInTheDocument();
    expect(screen.getByText('$49.99')).toBeInTheDocument();
    expect(screen.getByText('Save $20.00')).toBeInTheDocument();
  });

  it('displays "Check Price" button when shouldShowPrice returns false', () => {
    const dealWithHiddenPrice = { ...mockDeal, id: 'test-deal-hide-price' };
    
    render(<DealCard deal={dealWithHiddenPrice} onClick={mockOnClick} index={0} />);

    expect(screen.getByText('Check Price')).toBeInTheDocument();
    expect(screen.queryByText('$29.99')).not.toBeInTheDocument();
  });

  it('shows discount badge for significant discounts', () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    expect(screen.getByText('40% OFF')).toBeInTheDocument();
  });

  it('does not show discount badge for low discounts', () => {
    const lowDiscountDeal = { ...mockDeal, discountPercent: 10 };
    
    render(<DealCard deal={lowDiscountDeal} onClick={mockOnClick} index={0} />);

    expect(screen.queryByText('10% OFF')).not.toBeInTheDocument();
  });

  it('shows featured badge for featured deals', () => {
    const featuredDeal = { ...mockDeal, featured: true };
    
    render(<DealCard deal={featuredDeal} onClick={mockOnClick} index={0} />);

    expect(screen.getByText('⭐ Featured')).toBeInTheDocument();
  });

  it('shows data source indicator', () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    // Should show PAAPI indicator (✓)
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('handles card click', () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    const cardElement = screen.getByRole('button');
    fireEvent.click(cardElement);

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard interaction', () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    const cardElement = screen.getByRole('button');
    fireEvent.keyDown(cardElement, { key: 'Enter' });

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('handles "Shop Now" button click', () => {
    const originalOpen = window.open;
    window.open = jest.fn();

    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    const shopButton = screen.getByText('Shop Now →');
    fireEvent.click(shopButton);

    expect(window.open).toHaveBeenCalledWith(
      mockDeal.affiliateUrl,
      '_blank',
      'noopener,noreferrer'
    );

    window.open = originalOpen;
  });

  it('applies correct color based on index', () => {
    const { container } = render(
      <DealCard deal={mockDeal} onClick={mockOnClick} index={1} />
    );

    // Index 1 should get blue color (index % 3 = 1)
    expect(container.firstChild).toHaveClass('bg-blue-100');
  });

  it('handles image load error gracefully', async () => {
    render(<DealCard deal={mockDeal} onClick={mockOnClick} index={0} />);

    const image = screen.getByAltText('Test Product Title');
    fireEvent.error(image);

    await waitFor(() => {
      expect(screen.getByText('🖼️')).toBeInTheDocument();
    });
  });

  it('overrides price visibility when showPrice prop is provided', () => {
    const dealWithHiddenPrice = { ...mockDeal, id: 'test-deal-hide-price' };
    
    render(
      <DealCard 
        deal={dealWithHiddenPrice} 
        onClick={mockOnClick} 
        index={0}
        showPrice={true}
      />
    );

    // Should show price despite shouldShowPrice returning false
    expect(screen.getByText('$29.99')).toBeInTheDocument();
  });

  it('renders without original price when not available', () => {
    const dealWithoutOriginalPrice = { 
      ...mockDeal, 
      originalPrice: undefined,
      discountPercent: undefined 
    };
    
    render(<DealCard deal={dealWithoutOriginalPrice} onClick={mockOnClick} index={0} />);

    expect(screen.getByText('$29.99')).toBeInTheDocument();
    expect(screen.queryByText('$49.99')).not.toBeInTheDocument();
    expect(screen.queryByText('Save')).not.toBeInTheDocument();
  });

  it('truncates long titles appropriately', () => {
    const longTitleDeal = {
      ...mockDeal,
      title: 'This is a very long product title that should be truncated to prevent layout issues and maintain good user experience across different screen sizes and devices'
    };
    
    render(<DealCard deal={longTitleDeal} onClick={mockOnClick} index={0} />);

    // Should still render the title (truncated by CSS)
    expect(screen.getByText(longTitleDeal.title.substring(0, 80) + '...')).toBeInTheDocument();
  });

  it('renders different data source indicators correctly', () => {
    const scrapedDeal = { ...mockDeal, dataSource: 'SCRAPED' as const };
    const fallbackDeal = { ...mockDeal, dataSource: 'FALLBACK' as const };
    
    const { rerender } = render(<DealCard deal={scrapedDeal} onClick={mockOnClick} index={0} />);
    expect(screen.getByText('◯')).toBeInTheDocument();

    rerender(<DealCard deal={fallbackDeal} onClick={mockOnClick} index={0} />);
    expect(screen.getByText('△')).toBeInTheDocument();
  });
});