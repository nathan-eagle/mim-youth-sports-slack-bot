# 🚀 MiM Youth Sports - Complete Deployment Guide

## Overview

You now have a complete React storefront that integrates with your Slack bot! Here's what we've built:

### ✅ What's Complete
- **React/Next.js Storefront** (`/storefront/`) with beautiful UI
- **Supabase Database Integration** with complete schema
- **Stripe Payment Processing** with checkout flow
- **Product Design Pages** that display Slack bot creations
- **Order Management System** with fulfillment tracking
- **Responsive Design** optimized for parents on mobile

## 🗄️ Database Setup (Supabase)

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com) → "New Project"
2. Choose organization and project name: `mim-youth-sports`
3. Generate a strong database password
4. Select region closest to your users (US East for East Coast teams)

### 2. Run Database Schema
1. In Supabase dashboard, go to SQL Editor
2. Copy contents of `storefront/supabase-setup.sql`
3. Paste and run the script
4. Verify tables are created: `product_designs`, `customer_orders`, `order_items`, etc.

### 3. Get API Keys
1. Go to Settings > API
2. Copy your `Project URL` and `anon public` key
3. Copy the `service_role secret` key (for backend)

## 💳 Payment Setup (Stripe)

### 1. Create Stripe Account
1. Sign up at [stripe.com](https://stripe.com)
2. Complete account verification
3. Go to Dashboard > Developers > API keys

### 2. Get API Keys
- **Publishable key**: `pk_test_...` (for frontend)
- **Secret key**: `sk_test_...` (for backend)

### 3. Configure Webhooks
1. Go to Developers > Webhooks
2. Add endpoint: `https://your-domain.vercel.app/api/webhooks/stripe`
3. Select events: `checkout.session.completed`, `payment_intent.succeeded`
4. Copy webhook signing secret: `whsec_...`

## 🌐 Frontend Deployment (Vercel)

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Deploy Storefront
```bash
cd storefront
vercel
```

Follow prompts:
- Set up and deploy: `Yes`
- Which scope: `Your personal account`
- Link to existing project: `No`
- Project name: `mim-youth-sports-storefront`
- Directory: `./`
- Override settings: `No`

### 3. Configure Environment Variables
In Vercel dashboard, go to Settings > Environment Variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Domain
NEXT_PUBLIC_DOMAIN=https://your-storefront.vercel.app
```

### 4. Redeploy
```bash
vercel --prod
```

## 🤖 Backend Integration

### 1. Update Slack Bot Environment Variables
Add to your main project `.env`:

```bash
# Supabase (same as storefront)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Storefront domain
STOREFRONT_DOMAIN=https://your-storefront.vercel.app
```

### 2. Install Supabase Python Client
```bash
pip install supabase
```

### 3. Test Integration
The Slack bot will now:
1. ✅ Save designs to Supabase (not JSON files)
2. ✅ Generate working storefront URLs
3. ✅ Create mockups via Printify API

## 🧪 Testing the Complete Flow

### 1. Test Design Creation
1. Message your Slack bot: "I need blue shirts for my soccer team"
2. Upload a team logo
3. Bot should respond with working storefront link
4. Visit link → Should see your design with mockup

### 2. Test Ordering
1. On storefront, select sizes and quantities
2. Fill in customer and shipping info
3. Click "Proceed to Payment"
4. Use test card: `4242 4242 4242 4242`
5. Should redirect to success page

### 3. Verify Database
1. Check Supabase dashboard
2. Go to Table Editor
3. Should see records in `product_designs` and `customer_orders`

## 🔧 Customization Options

### Update Team Colors
Edit `storefront/tailwind.config.js`:
```js
team: {
  gold: '#fbbf24',    // Your team colors
  navy: '#1e40af',
  red: '#dc2626',
  green: '#059669',
}
```

### Update Domain
1. Purchase domain (e.g., `mimyouthsports.com`)
2. Add to Vercel project settings
3. Update environment variables

### Add Team Logos
Add SVG logos to `storefront/public/team-logos/`

## 📊 Analytics & Monitoring

### Recommended Tools
- **Vercel Analytics**: Built-in performance monitoring
- **Supabase Logs**: Database query monitoring
- **Stripe Dashboard**: Payment and revenue tracking
- **Google Analytics**: User behavior tracking

## 🚨 Production Checklist

### Security
- [ ] Enable Supabase Row Level Security (RLS) - ✅ Already configured
- [ ] Use HTTPS everywhere - ✅ Vercel provides this
- [ ] Secure environment variables - ✅ Not in code
- [ ] Enable Stripe webhook signature verification

### Performance
- [ ] Enable Vercel caching
- [ ] Optimize images (already using Next.js Image)
- [ ] Monitor database query performance
- [ ] Set up CDN for mockup images

### Business
- [ ] Set up customer support email
- [ ] Create terms of service and privacy policy
- [ ] Configure order confirmation emails
- [ ] Set up backup system for critical data

## 🛠️ Development Workflow

### Local Development
```bash
cd storefront
npm install
npm run dev
```

### Database Changes
1. Update `supabase-setup.sql`
2. Run in Supabase SQL Editor
3. Update TypeScript types in `lib/supabase.ts`

### Deploying Changes
```bash
git add .
git commit -m "Update storefront"
vercel --prod
```

## 🆘 Troubleshooting

### Common Issues

**"Product design not found"**
- Check if design exists in Supabase `product_designs` table
- Verify Slack bot is saving to Supabase (check logs)

**Stripe checkout fails**
- Verify webhook endpoint is correct
- Check Stripe dashboard for webhook delivery
- Ensure environment variables are set

**Mockup images not showing**
- Check Next.js image domains in `next.config.js`
- Verify Printify image URLs are accessible

### Debug Commands
```bash
# Check Supabase connection
curl "https://your-project.supabase.co/rest/v1/product_designs" \
  -H "apikey: YOUR_ANON_KEY"

# Test Stripe webhook
stripe listen --forward-to localhost:3000/api/webhooks/stripe
```

## 🎉 Success Metrics

Your MVP is successful when:
- [ ] 5 different parents successfully create and order designs
- [ ] Average checkout time < 2 minutes
- [ ] Zero technical errors during user flow
- [ ] Slack bot → Storefront → Payment → Fulfillment works end-to-end

## 📞 Support

**Technical Issues:**
- Check Vercel deployment logs
- Monitor Supabase logs
- Review Stripe webhook events

**Business Questions:**
- Track conversion rates in Stripe dashboard
- Monitor popular product types in Supabase
- Survey parents about experience

---

## 🎯 You're Ready to Launch!

The complete youth sports merchandise platform is now ready:

1. **Parents use Slack bot** → Create custom designs
2. **Bot generates storefront links** → Professional product pages
3. **Parents order through storefront** → Secure Stripe checkout
4. **Orders auto-fulfill through Printify** → Team gets their gear

**Next Steps:**
1. Deploy following this guide
2. Test with a few parent volunteers
3. Gather feedback and iterate
4. Scale to more teams and sports

Your revolutionary youth sports merchandise platform is ready to help teams across the country! 🏆⚽🏀⚾ 