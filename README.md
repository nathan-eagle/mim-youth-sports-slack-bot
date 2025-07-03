# MiM Youth Sports Merchandise Bot 🏆

A modern, AI-powered Slack bot that enables parents to easily create custom sports merchandise for their kids' teams through intelligent product selection and Printify fulfillment.

## ✨ Key Features

- **AI-Powered Product Selection**: Understands natural language requests ("I need shirts for my soccer team") and selects the best products
- **Smart Color Matching**: Analyzes uploaded logos to recommend perfect color combinations
- **Printify Choice Integration**: Access to 76+ high-quality, pre-vetted products
- **Serverless Architecture**: Fully compatible with Vercel/serverless deployments
- **Custom Storefront**: Beautiful Next.js frontend for product customization and ordering
- **Stripe Integration**: Secure payment processing
- **Automated Fulfillment**: Orders automatically sent to Printify for production

## 🏗️ Clean Architecture

### Modular Design Principles
- **No Hardcoding**: All product data from Printify API, AI handles selection
- **Serverless Ready**: Supabase-only storage, no file dependencies
- **Microservices**: Each module under 500 lines for maintainability
- **AI-First**: Product and color selection follow same intelligent patterns

```
┌─ Slack Events ─────────────────────────────────────────┐
│  ↓                                                     │
│  Flask Webhook Handler (app.py)                       │
│  ↓                                                     │
│  Slack Bot Layer (slack/)                             │
│  ├── bot.py           # Main coordination              │
│  ├── handlers.py      # Event handling                │
│  ├── conversation_flow.py # State management          │
│  ├── mockup_generator.py  # Product creation          │
│  └── message_sender.py    # Slack messaging           │
│  ↓                                                     │
│  Services Layer (services/)                           │
│  ├── product_service.py   # Product catalog           │
│  ├── product_selector.py  # AI product selection      │
│  └── variant_manager.py   # Color/size handling       │
│  ↓                                                     │
│  External Services                                     │
│  ├── OpenAI (AI decisions)                           │
│  ├── Printify (products & fulfillment)               │
│  ├── Supabase (database)                             │
│  └── Custom Storefront (Next.js)                     │
└───────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
MiM_slack/
├── slack/                    # Modular Slack bot (<500 lines each)
│   ├── bot.py               # Main bot coordination
│   ├── handlers.py          # Message & file handling
│   ├── conversation_flow.py # State machine logic
│   ├── mockup_generator.py  # Product mockup creation
│   ├── message_sender.py    # Slack message utilities
│   └── utils.py             # Helper functions
├── services/                 # Business logic services
│   ├── product_service.py   # Product catalog management
│   ├── product_selector.py  # AI-powered product selection
│   └── variant_manager.py   # Color/size variant handling
├── drop/                     # Next.js storefront
│   ├── app/                 # Next.js 13+ app directory
│   ├── components/          # React components
│   └── lib/                 # Utilities (Stripe, Supabase)
├── app.py                   # Flask webhook server
├── printifychoicecache.json # Cached Printify Choice products
├── conversation_manager.py  # Supabase conversation state
├── database_service.py      # Supabase data operations
├── printify_service.py      # Printify API integration
├── openai_service.py        # OpenAI integration
├── ai_color_service.py      # AI color recommendations
└── logo_processor.py        # Logo upload handling
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for storefront)
- Slack App with Bot Token
- OpenAI API Key
- Printify API Token
- Supabase Database
- Stripe Account (for payments)

### Environment Variables
```bash
# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# AI
OPENAI_API_KEY=sk-your-openai-key

# Printify
PRINTIFY_API_TOKEN=your-printify-token

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Storefront
DROP_BASE_URL=https://your-storefront.vercel.app

# Payments (in storefront)
STRIPE_PUBLISHABLE_KEY=pk_your-stripe-key
STRIPE_SECRET_KEY=sk_your-stripe-secret
```

### Installation

1. **Clone and setup Python backend:**
```bash
git clone <repo>
cd MiM_slack
pip install -r requirements.txt
```

2. **Setup Supabase database:**
```sql
-- Create tables (run in Supabase SQL editor)
CREATE TABLE conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_key TEXT UNIQUE,
  channel TEXT,
  user TEXT,
  state TEXT,
  product_selected JSONB,
  logo_info JSONB,
  team_info JSONB,
  selected_variants JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_activity TIMESTAMPTZ DEFAULT NOW(),
  error_count INTEGER DEFAULT 0,
  last_error TEXT,
  pending_request JSONB,
  recent_creation JSONB
);

CREATE TABLE product_designs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  product_name TEXT,
  product_id INTEGER,
  variant_id INTEGER,
  color TEXT,
  size TEXT,
  mockup_url TEXT,
  logo_url TEXT,
  price DECIMAL,
  printify_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'active'
);

CREATE TABLE customer_orders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  customer_email TEXT,
  customer_name TEXT,
  shipping_address JSONB,
  total_amount DECIMAL,
  stripe_payment_intent TEXT,
  printify_order_id TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  order_id UUID REFERENCES customer_orders(id),
  design_id UUID REFERENCES product_designs(id),
  product_name TEXT,
  color TEXT,
  size TEXT,
  quantity INTEGER,
  unit_price DECIMAL,
  total_price DECIMAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

3. **Setup Next.js storefront:**
```bash
cd drop/
npm install
npm run build
```

4. **Test the setup:**
```bash
python test_setup.py
```

## 🤖 How It Works

### AI Product Selection Pattern
Following the same intelligent pattern as color selection:

1. **User Request**: "I need shirts for my basketball team"
2. **AI Analysis**: Identifies `tshirt` category, `basketball` sport context
3. **Best Match**: Selects most popular Printify Choice t-shirt
4. **Show Alternatives**: Lists other t-shirt options
5. **Suggest Complementary**: Recommends hoodies, tank tops, hats

### Smart Color Matching
1. **AI analyzes uploaded logo** for dominant colors
2. **Selects best matching product colors** from available options
3. **Creates mockup** with selected color
4. **Shows alternatives** ("Also available in: Blue, Red, Green...")
5. **User can request different colors** naturally

### Conversation Flow States
- `initial` → User starts conversation
- `product_selection` → AI analyzes product requests
- `awaiting_logo` → Waiting for logo upload
- `creating_mockups` → Generating product mockups
- `selecting_colors` → User wants different colors
- `completed` → Ready for purchase

## 📊 Product Catalog

Uses **Printify Choice products** - pre-vetted, high-quality options:
- **76 products** across 6 categories
- **T-Shirts**: 29 options (Youth, Unisex, Performance)
- **Hoodies**: 18 options (Pullover, Zip-up, Fleece)
- **Headwear**: 6 options (Hats, Beanies, Caps)
- **Tank Tops**: 7 options (Racerback, Muscle, Standard)
- **Long Sleeve**: 7 options (Performance, Cotton, Blend)
- **Accessories**: 9 options (Bags, Drinkware, etc.)

Products automatically scored by:
- **Popularity with youth sports**
- **Number of color/size variants**
- **Quality and rating**
- **Youth/kids sizing availability**

## 🛒 Complete Purchase Flow

1. **Bot creates mockups** → Saves to Supabase
2. **Generates storefront URL** → `your-drop.vercel.app/design/{id}`
3. **Customer customizes** → Size, quantity, additional colors
4. **Stripe checkout** → Secure payment processing
5. **Auto-fulfillment** → Order sent to Printify
6. **Tracking updates** → Status notifications

## 🔧 Development Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests and setup verification
python test_setup.py

# Start Flask development server
FLASK_ENV=development python app.py

# Production server
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

### Next.js Storefront
```bash
cd drop/

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build && npm start

# Linting
npm run lint
```

## 🛠️ Slack App Setup

### Required Slack App Configuration:

1. **Create a Slack App** at https://api.slack.com/apps
2. **Add Bot Token Scopes**:
   - `chat:write`
   - `files:read`
   - `im:history`
   - `mpim:history`
   - `channels:history`
3. **Enable Events API**:
   - Request URL: `https://your-domain.com/slack/events`
   - Subscribe to Bot Events:
     - `message.channels`
     - `message.im`
     - `message.mpim`
     - `file_shared`
4. **Install to Workspace** and get Bot Token

## 📝 Usage Examples

### Modern Parent Conversation:

**Parent**: "I need gear for my daughter's volleyball team"

**Bot**: "Perfect! I'll create custom tank tops and t-shirts for volleyball.

*Other options in the same categories:*
• **Tank:** Racerback Performance Tank, Muscle Tank, Standard Tank
• **T-shirt:** Moisture-Wicking Tee, Cotton Blend Tee

*You might also like:*
• **Hoodies** for cooler weather
• **Headwear** for team spirit

Now I just need your team logo..."

**Parent**: *uploads logo*

**Bot**: "Great! Creating mockups with colors that match your logo..."
*[Shows navy tank top mockup]*
*[Shows orange t-shirt mockup]*
*Also available in: Red, White, Black, Royal Blue*

## 🚀 Deployment

### Backend (Heroku/Railway/Render)
```bash
# Set environment variables
# Deploy with requirements.txt
# Use: gunicorn -w 4 app:app
```

### Storefront (Vercel)
```bash
cd drop/
vercel --prod
# Auto-deploys from git pushes
```

### Database (Supabase)
- Managed PostgreSQL
- Auto-scaling
- Built-in auth (for admin)

## 📈 Key Improvements Made

✅ **Eliminated Bloat**: Removed 70% of redundant files and code
✅ **Modular Architecture**: Split 1911-line monolith into focused modules
✅ **Serverless Ready**: Converted all file storage to Supabase
✅ **AI-Powered**: Both product and color selection use intelligent patterns
✅ **No Hardcoding**: All data comes from Printify API dynamically
✅ **Modern Stack**: Next.js storefront with Stripe integration

## 🤝 Contributing

1. Keep modules **under 500 lines**
2. Use **Supabase-only** storage (no files)
3. Follow **AI-first** patterns
4. Test with `python test_setup.py`
5. Update documentation

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for youth sports families**