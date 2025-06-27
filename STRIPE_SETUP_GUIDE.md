# 🔑 Stripe Setup Guide for MiM Youth Sports Swag Bot

## 📋 **Three Required Stripe Keys**

You need these **3 keys** from your Stripe Dashboard:

1. **NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY** - `pk_test_...` (for frontend)
2. **STRIPE_SECRET_KEY** - `sk_test_...` (for backend)  
3. **STRIPE_WEBHOOK_SECRET** - `whsec_...` (for webhook verification)

---

## 🏆 **Step 1: Get Your Stripe API Keys**

### 1.1 Login to Stripe Dashboard
1. Go to [https://stripe.com](https://stripe.com)
2. Log into your account (or create one if needed)
3. **Important**: Use **Test Mode** first, then switch to Live Mode later

### 1.2 Get API Keys
1. Go to **Developers → API Keys**
2. **Publishable Key**: Copy the `pk_test_...` key (visible by default)
3. **Restricted Secret Key** (Recommended for security):
   - Click **"Create restricted key"**
   - Give it a name: "MiM Youth Sports Storefront"
   - Set these permissions:
     - **Customers**: Write
     - **Checkout Sessions**: Write  
     - **Payment Intents**: Write
     - **Webhooks**: Write (if you plan to manage webhooks via API)
   - Click **"Create key"** and copy the `rk_test_...` key

**Alternative**: Use standard secret key by clicking **"Reveal test key"** (less secure)

---

## 🔗 **Step 2: Set Up Webhook**

### 2.1 Create Webhook Endpoint
1. Go to **Developers → Webhooks**
2. Click **"Add endpoint"**
3. **Endpoint URL**: `https://your-storefront-domain.vercel.app/api/webhooks/stripe`
4. **Events to send**: Select these events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Click **"Add endpoint"**

### 2.2 Get Webhook Secret
1. Click on your newly created webhook endpoint
2. Copy the **Webhook signing secret** (starts with `whsec_...`)

---

## 📁 **Step 3: Add Keys to Environment Files**

### 3.1 Main Flask App (.env file)
Create a `.env` file in your project root:

\`\`\`bash
# Flask App Environment Variables
FLASK_ENV=development
PORT=5000

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Printify Configuration (API-only, no shop needed)
PRINTIFY_API_TOKEN=your-printify-api-token

# Stripe Configuration (ADD YOUR KEYS HERE)
STRIPE_SECRET_KEY=rk_test_your_restricted_key_here  # or sk_test_ for standard key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Storefront Domain
STOREFRONT_DOMAIN=https://your-storefront.vercel.app
\`\`\`

### 3.2 Storefront App (drop/.env.local file)
Create a `.env.local` file in the `drop/` directory:

\`\`\`bash
# Next.js Storefront Environment Variables

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Stripe Configuration (ADD YOUR KEYS HERE)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_SECRET_KEY=rk_test_your_restricted_key_here  # or sk_test_ for standard key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Domain Configuration
NEXT_PUBLIC_DOMAIN=https://your-storefront.vercel.app

# Python Backend (for Printify fulfillment)
PYTHON_BACKEND_URL=https://your-python-backend.vercel.app
\`\`\`

---

## 🚚 **Step 4: Your Custom Storefront Architecture ✅**

### 4.1 Custom mim-drop Storefront (Already Built!)
You're using your **own custom storefront** in the `drop/` directory, not Printify's shop system:
- ✅ Custom Next.js storefront for complete control
- ✅ Printify API for product creation & mockups (no shop needed)
- ✅ Stripe checkout in YOUR storefront
- ✅ Supabase for order management
- ✅ Custom fulfillment workflow

### 4.2 No PRINTIFY_SHOP_ID Required! 
Your architecture uses Printify's **API only** for:
- Creating custom product designs
- Generating mockup images  
- Print-ready file creation
- Direct API fulfillment calls

**Much better than using Printify's shop system!** 🎉

---

## 🧪 **Step 5: Test the Complete Flow**

### 5.1 Test Stripe Payment
1. Start your storefront: `cd drop && npm run dev`
2. Go to a product page
3. Add items to cart and checkout
4. Use Stripe test card: `4242 4242 4242 4242`
5. Check Stripe Dashboard for successful payment

### 5.2 Test Custom Fulfillment Flow
After successful payment, your webhook should:
1. ✅ Update order status to "paid" in Supabase
2. ✅ Create print-ready files via Printify API
3. ✅ Process fulfillment through your custom workflow

---

## ⚡ **Step 6: Deploy to Production**

### 6.1 Vercel Deployment
1. Push your code to GitHub
2. Connect to Vercel
3. Add environment variables in Vercel dashboard
4. Update webhook URL to production domain

### 6.2 Switch to Live Mode
1. Get **live** Stripe keys (starts with `pk_live_...` and `sk_live_...`)
2. Update webhook endpoint to production URL
3. Update environment variables with live keys

---

## 🚨 **Common Issues & Solutions**

### Issue: "No such token" error
**Solution**: Check that your Stripe secret key is correct and starts with `rk_test_` (restricted) or `sk_test_` (standard)

### Issue: Webhook not receiving events  
**Solution**: Verify webhook URL is correct and publicly accessible

### Issue: Printify order creation fails
**Solution**: Check PRINTIFY_API_TOKEN is valid and you have sufficient Printify credits

### Issue: Orders not updating after payment
**Solution**: Check webhook secret matches and events are configured correctly

---

## 📞 **Need Help?**

1. **Stripe Issues**: Check [Stripe Dashboard → Events] for webhook delivery
2. **Printify Issues**: Check [Printify Dashboard → Orders] for fulfillment status
3. **App Issues**: Check logs in Vercel dashboard or local console

Your app already has the complete Stripe + Printify integration - you just need to add the keys! 🎉 