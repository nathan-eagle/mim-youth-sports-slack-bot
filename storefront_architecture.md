# Custom Storefront Architecture for MiM Youth Sports Team Swag

## 🎯 Technical Architecture Overview

### Core Strategy: Direct API Integration with Printify
Instead of trying to publish products through Printify's limited publishing system, we create a **custom storefront** that:
1. Uses Printify API only for fulfillment (not sales)
2. Builds our own product catalog and checkout experience
3. Processes payments independently
4. Sends orders directly to Printify for production & shipping

---

## 🏗️ System Components

### 1. **Slack Bot (Existing)** - Product Design Interface
- ✅ Handles logo uploads and product customization conversations
- ✅ Creates product mockups using Printify API
- ✅ Shows preview images to parents
- 🔄 **NEW**: Saves product designs to database instead of trying to publish
- 🔄 **NEW**: Provides link to custom storefront for purchase

### 2. **Custom Storefront** - Sales Interface
- **Frontend**: React/Next.js web application
- **Backend**: Flask API (can be same as Slack bot)
- **Database**: Store product designs, customer info, orders
- **Payment**: Stripe integration for secure payment processing
- **UI/UX**: Youth sports themed, parent-friendly interface

### 3. **Printify Integration Layer** - Fulfillment Only
- **Order Creation**: Send completed orders directly to Printify
- **Status Tracking**: Monitor production and shipping status
- **Webhooks**: Receive updates on order progress
- **No Publishing**: Skip Printify's publishing system entirely

---

## 📊 Database Schema Design

```sql
-- Product Designs (created from Slack bot)
CREATE TABLE product_designs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    blueprint_id INTEGER NOT NULL,
    print_provider_id INTEGER NOT NULL,
    team_logo_image_id VARCHAR(255) NOT NULL,  -- Printify image ID
    mockup_image_url VARCHAR(500),
    base_price DECIMAL(10,2) NOT NULL,
    markup_percentage DECIMAL(5,2) DEFAULT 50.00,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),  -- Slack user ID
    status VARCHAR(50) DEFAULT 'active'  -- active, archived
);

-- Product Variants (sizes, colors available for each design)
CREATE TABLE product_variants (
    id UUID PRIMARY KEY,
    product_design_id UUID REFERENCES product_designs(id),
    printify_variant_id INTEGER NOT NULL,
    size VARCHAR(50),
    color VARCHAR(50),
    printify_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    is_available BOOLEAN DEFAULT true
);

-- Customer Orders
CREATE TABLE customer_orders (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(50),  -- pending, paid, failed
    stripe_payment_intent_id VARCHAR(255),
    fulfillment_status VARCHAR(50),  -- pending, processing, shipped, delivered
    printify_order_id VARCHAR(255),  -- Set when sent to Printify
    created_at TIMESTAMP DEFAULT NOW()
);

-- Order Items
CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES customer_orders(id),
    product_design_id UUID REFERENCES product_designs(id),
    variant_id UUID REFERENCES product_variants(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL
);

-- Shipping Addresses
CREATE TABLE shipping_addresses (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES customer_orders(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    address1 VARCHAR(255),
    address2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(2) DEFAULT 'US'
);
```

---

## 🔄 User Flow Architecture

### Phase 1: Product Design (Slack Bot)
```
Parent uploads logo → Slack Bot
    ↓
Bot: "What product type?"
    ↓
Parent: "Baseball hats for the team"
    ↓
Bot creates mockup via Printify API
    ↓
Bot saves design to database
    ↓
Bot: "Great! View and purchase: https://store.mimyouthsports.com/design/{design_id}"
```

### Phase 2: Purchase (Custom Storefront)
```
Parent clicks link → Custom Storefront
    ↓
Shows product design with mockup image
    ↓
Parent selects quantities/sizes/colors
    ↓
Stripe checkout for payment
    ↓
Payment confirmed → Order saved to database
    ↓
Order automatically sent to Printify for fulfillment
    ↓
Parent receives order confirmation + tracking info
```

---

## 🛠️ Technical Implementation

### A. Slack Bot Updates (Minimal Changes)
```python
# Updated slack_bot.py workflow
def handle_product_creation():
    # 1. Create design in Printify (for mockup)
    design_result = printify_service.create_design(...)
    
    # 2. Save design to database (NEW)
    design_id = database.save_product_design({
        'name': f"{team_name} {product_type}",
        'blueprint_id': blueprint_id,
        'logo_image_id': logo_image_id,
        'mockup_url': design_result['mockup_url'],
        'base_price': base_price
    })
    
    # 3. Send storefront link instead of "purchase" link
    storefront_url = f"https://store.mimyouthsports.com/design/{design_id}"
    send_message(f"🎉 Your {product_type} design is ready! Purchase here: {storefront_url}")
```

### B. Custom Storefront Frontend
```javascript
// React component for product display
function ProductDesignPage({ designId }) {
    const [design, setDesign] = useState(null);
    const [selectedVariants, setSelectedVariants] = useState({});
    
    // Load product design
    useEffect(() => {
        fetch(`/api/designs/${designId}`)
            .then(res => res.json())
            .then(setDesign);
    }, [designId]);
    
    const handleCheckout = async () => {
        // Create Stripe checkout session
        const response = await fetch('/api/checkout', {
            method: 'POST',
            body: JSON.stringify({
                design_id: designId,
                variants: selectedVariants,
                customer_info: customerInfo
            })
        });
        
        const { checkout_url } = await response.json();
        window.location.href = checkout_url;
    };
    
    return (
        <div className="youth-sports-theme">
            <img src={design.mockup_url} alt="Product Preview" />
            <VariantSelector variants={design.variants} onChange={setSelectedVariants} />
            <button onClick={handleCheckout}>Purchase Team Gear</button>
        </div>
    );
}
```

### C. Backend API for Storefront
```python
# New routes in app.py
@app.route('/api/designs/<design_id>')
def get_product_design(design_id):
    design = database.get_product_design(design_id)
    if not design:
        return {'error': 'Design not found'}, 404
    
    return {
        'id': design.id,
        'name': design.name,
        'mockup_url': design.mockup_image_url,
        'variants': get_available_variants(design),
        'base_price': design.base_price
    }

@app.route('/api/checkout', methods=['POST'])
def create_checkout_session():
    data = request.json
    
    # Calculate total price
    total = calculate_order_total(data['design_id'], data['variants'])
    
    # Create Stripe checkout session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f"Custom {design.name}"},
                'unit_amount': int(total * 100)
            },
            'quantity': 1
        }],
        mode='payment',
        success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{DOMAIN}/cancel'
    )
    
    # Save pending order
    order_id = database.create_pending_order(data)
    
    return {'checkout_url': checkout_session.url}

@app.route('/api/webhook/stripe', methods=['POST'])
def stripe_webhook():
    # Handle successful payment
    event = stripe.Webhook.construct_event(
        request.data, request.headers.get('stripe-signature'), 
        stripe_webhook_secret
    )
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Mark order as paid
        order = database.mark_order_paid(session.id)
        
        # Send to Printify for fulfillment
        fulfillment_result = send_to_printify_for_fulfillment(order)
        
        # Update order with Printify order ID
        database.update_order_printify_id(order.id, fulfillment_result['order_id'])
    
    return {'status': 'success'}
```

### D. Printify Fulfillment Integration
```python
def send_to_printify_for_fulfillment(order):
    """Send completed order to Printify for production & shipping"""
    
    # Build line items for Printify order
    line_items = []
    for item in order.items:
        line_item = printify_service.create_line_item_for_blueprint(
            blueprint_id=item.product_design.blueprint_id,
            print_provider_id=item.product_design.print_provider_id,
            variant_id=item.variant.printify_variant_id,
            image_id=item.product_design.team_logo_image_id,
            quantity=item.quantity
        )
        line_items.append(line_item['line_item'])
    
    # Create order in Printify
    printify_order = printify_service.create_order(
        customer_info={
            'email': order.email,
            'first_name': order.shipping_address.first_name,
            'last_name': order.shipping_address.last_name,
            'phone': order.phone,
            'address1': order.shipping_address.address1,
            'address2': order.shipping_address.address2,
            'city': order.shipping_address.city,
            'state': order.shipping_address.state,
            'zip': order.shipping_address.zip,
            'country': order.shipping_address.country
        },
        line_items=line_items
    )
    
    return printify_order
```

---

## 🎨 Custom Storefront Design

### Visual Design Principles
- **Youth Sports Theme**: Team colors, energetic layouts, sports imagery
- **Parent-Friendly**: Clear pricing, simple checkout, mobile-optimized
- **Trust Indicators**: Security badges, testimonials, clear shipping info
- **Team Spirit**: Emphasize customization, team unity, quality

### Key Pages
1. **Product Design Page**: Shows mockup, variant selection, pricing
2. **Team Info Page**: Capture team name, coach contact, bulk discounts
3. **Checkout Page**: Stripe-powered, address collection, order summary
4. **Order Status Page**: Real-time updates from Printify webhooks
5. **Gallery Page**: Showcase previous team designs (with permission)

---

## 📈 Business Model Integration

### Pricing Strategy
```python
def calculate_selling_price(printify_base_price, markup_percentage=50):
    """Apply markup to Printify base price"""
    return printify_base_price * (1 + markup_percentage / 100)

def apply_bulk_discounts(total_quantity):
    """Team bulk discounts"""
    if total_quantity >= 20:
        return 0.15  # 15% discount
    elif total_quantity >= 10:
        return 0.10  # 10% discount
    return 0.0
```

### Revenue Streams
- **Product Markup**: 50-100% markup on Printify base prices
- **Bulk Discounts**: Encourage larger team orders
- **Design Services**: Premium design consultation
- **Rush Orders**: Expedited processing fees

---

## 🔧 Deployment & Infrastructure (DECIDED: Vercel + Supabase)

### Chosen Architecture
- **Frontend**: Vercel for Next.js React storefront
- **Backend API**: Keep Flask on Vercel (existing setup)
- **Database**: Supabase PostgreSQL (managed, real-time capabilities)
- **CDN**: Vercel's built-in CDN for fast global delivery
- **SSL**: Vercel provides automatic SSL certificates
- **File Storage**: Supabase Storage for any additional assets

### Environment Variables
```bash
# Existing
PRINTIFY_API_TOKEN=xxx
PRINTIFY_SHOP_ID=xxx
OPENAI_API_KEY=xxx
SLACK_BOT_TOKEN=xxx

# New for storefront
STRIPE_PUBLISHABLE_KEY=xxx
STRIPE_SECRET_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
DOMAIN=https://store.mimyouthsports.com
```

---

## 🚀 Implementation Phases

### Phase 1: Backend Foundation (Week 1)
- Set up database schema
- Create API endpoints for product designs
- Integrate Stripe payment processing
- Update Slack bot to save designs instead of publishing

### Phase 2: Custom Storefront (Week 2)
- Build React frontend for product display
- Implement checkout flow
- Create order management system
- Set up Printify fulfillment automation

### Phase 3: Enhancement & Testing (Week 3)
- Add bulk discount logic
- Implement order tracking
- Create admin dashboard
- Comprehensive testing with real orders

### Phase 4: Launch & Marketing (Week 4)
- Domain setup and SSL
- Parent user testing
- Coach/team outreach
- Analytics and monitoring

---

## ✅ Advantages of This Architecture

1. **Full Control**: Own the customer experience and data
2. **Better Margins**: Direct pricing control with markup flexibility
3. **No Publishing Limits**: Bypass Printify's publishing restrictions
4. **Scalable**: Can handle high volume during sports seasons
5. **Brand Building**: Create MiM brand recognition in youth sports
6. **Customer Relationships**: Direct contact with parents and coaches
7. **Analytics**: Full visibility into sales and customer behavior

This architecture transforms the Printify API limitation into an opportunity to build a proper youth sports merchandise business! 