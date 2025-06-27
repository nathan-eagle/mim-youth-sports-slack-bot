# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Flask Backend (Main Slack Bot)
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests and setup verification
python test_setup.py

# Start the Flask application
python app.py

# Start Flask in development mode (if FLASK_ENV=development in .env)
FLASK_ENV=development python app.py
```

### Next.js Frontend (Drop Storefront)
```bash
# Navigate to storefront directory
cd drop/

# Install Node.js dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint
```

## High-Level Architecture

### Dual Application Structure
This is a hybrid system with two main components:

1. **Python Flask Backend** (`app.py`, `slack_bot.py`) - Handles Slack bot interactions and Printify API integration
2. **Next.js Frontend** (`drop/` directory) - Custom storefront for product purchases with Stripe integration

### Core System Flow
```
Parent Message → Slack Bot → AI Analysis → Product Selection → Logo Processing
                     ↓
Database Storage → Custom Storefront → Stripe Payment → Printify Fulfillment
```

### Key Components

**Slack Bot Layer** (`slack_bot.py`, `conversation_manager.py`):
- Handles parent conversations and logo uploads
- Uses OpenAI for intelligent product recommendations
- Creates product mockups via Printify API
- Saves designs to database instead of publishing to Printify

**Product Services** (`product_service.py`, `printify_service.py`):
- Manages cached product catalog from Printify
- Three "best products": Kids Heavy Cotton Tee, Youth Heavy Blend Hooded Sweatshirt, Snapback Trucker Cap
- Handles logo processing and mockup generation

**Custom Storefront** (`drop/` directory):
- Next.js/React frontend with Tailwind CSS
- Supabase database integration for storing designs and orders
- Stripe payment processing
- Automatic fulfillment via Printify API

**Database Architecture** (Supabase PostgreSQL):
- `product_designs` - Stores custom designs created in Slack
- `customer_orders` - Order management and tracking
- `product_variants` - Size/color options for each design
- `order_items` - Individual items within orders

### Environment Configuration
Required environment variables:
- **Slack**: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- **OpenAI**: `OPENAI_API_KEY`
- **Printify**: `PRINTIFY_API_TOKEN`
- **Stripe**: `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- **Supabase**: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`

### Key Files and Responsibilities

**Python Backend**:
- `app.py` - Main Flask application with Slack webhook handling
- `slack_bot.py` - Core bot logic and conversation flow
- `conversation_manager.py` - Stateful conversation handling
- `openai_service.py` - AI-powered product recommendations
- `printify_service.py` - Printify API integration for fulfillment
- `logo_processor.py` - Image upload and URL processing
- `database_service.py` - Database operations and order management
- `product_cache.json` - Optimized product catalog (DO NOT refresh without explicit request)

**Next.js Frontend** (`drop/`):
- `app/page.tsx` - Main storefront landing page
- `app/design/[id]/page.tsx` - Individual product design pages
- `app/api/checkout/route.ts` - Stripe checkout session creation
- `app/api/fulfill-order/route.ts` - Order fulfillment to Printify
- `components/ProductOrderForm.tsx` - Product ordering interface
- `lib/stripe.ts` - Stripe configuration
- `lib/supabase.ts` - Database client configuration

### Deployment Architecture
- **Backend**: Can be deployed on Heroku, Railway, or similar Python hosting
- **Frontend**: Optimized for Vercel deployment with automatic builds
- **Database**: Supabase managed PostgreSQL
- **Production WSGI**: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

### Testing and Validation
- Always run `python test_setup.py` to verify API connections and environment setup
- Test Slack webhook integration in development before deployment
- Verify Printify fulfillment with small test orders before production use

### Business Logic Notes
- Product catalog is pre-optimized for youth sports (don't modify without explicit request)
- Markup strategy built into pricing (typically 50-100% on Printify base prices)
- Bulk discount logic for team orders (10+ items get discounts)
- All orders flow through custom storefront, NOT Printify's publishing system