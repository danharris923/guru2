# SavingsGuru Real Data Implementation Prompt

## Context
You have a React deals website that scrapes SavingsGuru.ca for Amazon affiliate links but generates completely FAKE pricing data. The user wants REAL Amazon pricing data, not fabricated numbers.

## Current Broken Flow
1. ✅ Scrape SavingsGuru.ca posts → extract amzn.to short links → resolve to Amazon ASINs  
2. ❌ Generate completely fake prices/discounts/descriptions
3. ❌ Use placeholder images instead of real Amazon images

## Required Real Data Flow  
1. ✅ Scrape SavingsGuru.ca posts → extract real Amazon ASINs
2. ✅ **USE AMAZON PRODUCT ADVERTISING API (PAAPI) for real pricing/images/titles**
3. ✅ **Fallback: scrape live Amazon.ca pages if API fails**
4. ❌ **NEVER generate fake data**

## Environment Variables (Already Provided)
```bash
AMZ_ACCESS_KEY=AKIAISXK3L5JWW6DBZTA  
AMZ_SECRET_KEY=nrdUizuoH2DAFr5ZEsCzSep2N2QlbK2xrQ1eEMFE
AMZ_PARTNER_TAG=savingsgurucc-20
```

## Implementation Requirements

### 1. Amazon API Integration (`amazon_api.py`)
- Use `python-amazon-paapi` library with Canadian marketplace
- Extract: real price, list price, discount %, title, high-res image URL
- Handle API failures gracefully

### 2. Live Scraping Fallback  
- If PAAPI fails → scrape live Amazon.ca product page
- Extract: current price, crossed-out price, product title, main image
- Use proper headers to avoid bot detection

### 3. Scraper Updates (`focused_scraper.py`)
- Replace `generate_canadian_pricing()` with real API calls
- **Image priority**: Amazon API image → scraped Amazon image → original SavingsGuru.ca image → placeholder
- Use real product titles from Amazon
- Skip products that have no real pricing data (don't generate fake data)

### 4. Data Integrity
- Only generate descriptions (marketing copy) - everything else must be real
- Validate all pricing data exists before creating deal
- Log clearly: "REAL API DATA" vs "SCRAPED DATA" vs "SKIPPED - NO DATA"

## Success Criteria
- **Zero fake prices** - every price comes from Amazon API or live scraping
- **Real product images** - direct from Amazon servers  
- **Real product titles** - from Amazon, not SavingsGuru post titles
- **Real discounts** - calculated from actual list vs current price
- **Robust fallbacks** - API failure → live scraping → skip product (no fake data)

## Frontend GUI Requirements

### React App Structure
- **Create React App** with TypeScript + Tailwind CSS
- **Static deployment** - no backend server, reads from `public/deals.json`
- **Responsive design** - mobile-first with desktop enhancements
- **Color scheme**: Card rotation through pink (#EAB2AB), blue (#93C4D8), yellow (#FCE3AB)

### Components Needed

#### 1. Main App (`App.tsx`)
- Load deals from `/public/deals.json` on mount
- Handle deal modal state
- Responsive layout: sidebar + main grid

#### 2. Deal Cards (`DealCard.tsx`)
- **Card rotation**: 3 background colors cycling
- **Price display**: Show both current price + crossed-out original price
- **Discount badge**: Red badge showing "X% OFF" for 40%+ discounts
- **Mobile modal**: Full-screen modal on mobile, sidebar modal on desktop
- **Image handling**: Lazy loading, error fallback to placeholder
- **Click actions**: Open Amazon affiliate link in new tab

#### 3. Deal Modal (`DealModal.tsx`)  
- **Product details**: Large image, full title, description
- **Pricing**: Prominent current price, strikethrough original price
- **CTA button**: "Shop Now" → Amazon affiliate link
- **Categories**: Chip-style category tags
- **Close**: X button or backdrop click

#### 4. Header (`Header.tsx`)
- **Branding**: "SavingsGuru" logo/title
- **Mobile responsive**: Collapsible navigation

#### 5. Sidebar (`Sidebar.tsx`)
- **Featured deals**: Top 20 deals with highest discounts
- **Compact layout**: Small images, prices, discount %
- **Desktop only**: Hidden on mobile

### Deal Data Interface
```typescript
interface Deal {
  id: string;
  title: string;
  imageUrl: string;  // From Amazon API or SavingsGuru.ca
  price: number;     // REAL Amazon current price
  originalPrice: number; // REAL Amazon list price
  discountPercent: number; // REAL calculated discount
  category: string;
  description: string;
  affiliateUrl: string; // https://amazon.ca/dp/{ASIN}?tag=savingsgurucc-20
  featured: boolean;
  dateAdded: string;
}
```

### UI/UX Features
- **Masonry/grid layout** with varying card heights
- **Lazy image loading** with skeleton placeholders  
- **Smooth animations** for modals and hover states
- **Price visibility logic**: Show prices on ~10% of cards, "Check Price" button on others
- **Sort by discount**: Highest discounts first
- **Mobile-optimized**: Touch-friendly buttons, swipe gestures

### Styling Requirements
- **Tailwind CSS** for all styling
- **Glass morphism effects** on modals/overlays
- **Gradient buttons** for CTAs
- **Responsive breakpoints**: Mobile-first design
- **Loading states**: Skeleton loaders for images
- **Error states**: Fallback UI for failed image loads

## Complete File Structure
```
src/
├── App.tsx                 # Main app orchestrator
├── components/
│   ├── DealCard.tsx       # Individual deal display
│   ├── DealModal.tsx      # Deal detail popup  
│   ├── Header.tsx         # Site navigation
│   ├── Sidebar.tsx        # Featured deals
│   └── HomePage.tsx       # Main grid layout
├── types/
│   └── Deal.ts           # TypeScript interfaces
├── utils/
│   ├── dealUtils.ts      # Price formatting utilities
│   └── priceVisibility.ts # Price display logic
└── index.css             # Tailwind imports

public/
└── deals.json            # Static data file (generated by scraper)

scraper/
├── amazon_api.py         # PAAPI + live scraping
├── focused_scraper.py    # Main scraper with real data
└── requirements.txt      # Python dependencies
```

## Deployment
- **Vercel static deployment** 
- **Git-based CI/CD**: Push to trigger rebuild
- **Environment variables**: Amazon API credentials in Vercel settings

Write a complete full-stack application with real Amazon data and a polished React GUI matching this specification.