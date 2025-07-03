# MiM Slack Bot Architecture

## Overview
A Slack bot that enables parents to create custom merchandise for youth sports teams through AI-powered product recommendations and Printify fulfillment.

## Core Business Flow
```
1. Parent uploads logo in Slack
2. AI analyzes logo and suggests products + colors
3. System creates mockups via Printify API
4. Designs saved to Supabase database
5. Parent directed to custom storefront for purchase
6. Orders fulfilled through Printify on payment
```

## Technical Architecture

### Backend (Python/Flask)
**Core Services:**
- **Slack Integration**: Webhook-based message handling
- **AI Services**: OpenAI for product/color recommendations
- **Image Processing**: Logo upload and processing
- **Printify Integration**: Product catalog and mockup generation
- **Database**: Supabase for state and order management

### Frontend (Next.js)
**Storefront Features:**
- Product display with mockups
- Size/color variant selection
- Stripe payment integration
- Order fulfillment automation

## Planned Module Structure (Post-Refactor)

### Slack Layer (Split from monolithic slack_bot.py)
```
slack/
├── handlers.py          # Event handlers (<200 lines)
├── message_builder.py   # Message formatting (<200 lines)
├── conversation_flow.py # Conversation logic (<300 lines)
└── utils.py            # Slack utilities (<100 lines)
```

### Services Layer
```
services/
├── ai/
│   ├── product_selector.py  # AI product selection
│   └── color_selector.py    # AI color matching
├── printify/
│   ├── client.py           # API client
│   ├── products.py         # Product operations
│   └── mockups.py          # Mockup generation
└── storage/
    └── supabase_manager.py # All storage operations
```

### Data Layer
```
data/
├── printifychoicecache.json  # Cached Printify Choice products
└── models.py                 # Data models/schemas
```

## Key Design Principles

1. **No Hardcoding**: All product data from Printify API/cache
2. **AI-Driven Selection**: Products and colors selected by AI based on context
3. **Serverless Ready**: Supabase-only storage (no file operations)
4. **Modular Design**: No file exceeds 500 lines
5. **Clear Separation**: Slack handling, business logic, and external services isolated

## Data Flow

### Product Selection Flow
1. Default: Show t-shirt + sweatshirt mockups
2. AI suggests these + lists alternatives in message
3. User can request different products
4. AI selects from Printify Choice catalog
5. Shows most popular option with alternatives listed

### Color Selection Flow (Same pattern for all selections)
1. AI analyzes logo/context for best color match
2. Creates mockup with selected color
3. Lists 3-5 alternative colors in message
4. User can request different colors

## External Dependencies
- Slack SDK
- OpenAI API
- Printify API
- Supabase Client
- Stripe (frontend only)

## Environment Variables
```
# Slack
SLACK_BOT_TOKEN
SLACK_SIGNING_SECRET

# AI
OPENAI_API_KEY

# Printify
PRINTIFY_API_TOKEN

# Database
SUPABASE_URL
SUPABASE_SERVICE_KEY
```

## Database Schema (Supabase)
- `conversations` - Conversation state management
- `product_designs` - Saved custom designs
- `customer_orders` - Order tracking
- `product_variants` - Size/color options
- `order_items` - Individual order items