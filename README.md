# MiM Youth Sports Team Swag Slack Bot 🏆

A Slack bot that helps parents customize youth sports team merchandise using Printify's print-on-demand services. Parents can request products, upload team logos, and get instant customized product mockups!

## 🎯 Features

- **Smart Product Selection**: AI-powered understanding of parent requests
- **Logo Upload Support**: Both file uploads and URL inputs
- **Three "Best" Products**: 
  - Kids Heavy Cotton Tee
  - Youth Heavy Blend Hooded Sweatshirt  
  - Snapback Trucker Cap
- **Instant Mockups**: Custom product previews with team logos
- **Purchase Links**: Direct links to buy customized products

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file with the following variables:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# OpenAI Configuration  
OPENAI_API_KEY=your-openai-api-key-here

# Printify Configuration
PRINTIFY_API_TOKEN=your-printify-api-token-here
PRINTIFY_SHOP_ID=your-printify-shop-id-here

# Flask Configuration (optional)
FLASK_ENV=development
PORT=5000
```

### 3. Test Your Setup
```bash
python test_setup.py
```

### 4. Run the Bot
```bash
python app.py
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

### Parent Conversation Flow:

**Parent**: "I need a shirt for my son's baseball team"

**Bot**: "Great choice on the Kids Heavy Cotton Tee! Please upload your team logo (image file) or provide a URL link to your logo, and I'll customize it for you."

**Parent**: *uploads logo file*

**Bot**: "🎉 Awesome! I've created a custom Kids Heavy Cotton Tee for your son's baseball team!"
*[Shows product mockup with logo]*
*[Provides purchase link]*

## 🏗️ Architecture

```
Parent Message → Slack Events API → Flask App
                      ↓
OpenAI Analysis → Product Selection → Logo Processing
                      ↓
Printify API → Custom Product → Mockup Generation
                      ↓
Slack Response with Image & Purchase Link
```

## 📁 Project Structure

```
MiM_slack/
├── app.py                  # Main Flask application
├── slack_bot.py           # Slack event handling
├── product_service.py     # Product cache filtering  
├── openai_service.py      # AI conversation handling
├── printify_service.py    # Printify API integration
├── logo_processor.py      # Image upload/URL handling
├── test_setup.py          # Setup verification
├── requirements.txt       # Dependencies
├── product_cache.json     # Product data (optimized)
└── AI_Instructions/       # Documentation
    ├── plan.md           # Development plan
    └── printify_API.pdf  # API documentation
```

## 🧪 Testing

Run the test suite to verify everything is working:

```bash
python test_setup.py
```

This will check:
- Environment variables
- Product cache loading
- OpenAI service connection
- Printify API configuration

## 🚀 Deployment

### Deploy to Production:

1. **Set Environment Variables** in your hosting platform
2. **Update Slack App** with production webhook URL
3. **Use Production WSGI Server**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:$PORT app:app
   ```

### Recommended Platforms:
- **Heroku**: Easy Slack app deployment
- **Railway**: Great for Python apps
- **Vercel**: With Flask adapter
- **DigitalOcean App Platform**: Scalable option

## 🎯 Success Metrics

- Parents complete product selection in under 2 minutes
- Zero "None" returns causing errors  
- Sub-5 second response times
- Successful logo application and mockup generation

## 🤝 Contributing

This bot is designed specifically for MiM Youth Sports Team merchandise. The product catalog is pre-optimized and should not be refreshed unless explicitly requested.

## 📞 Support

For issues or questions about the MiM Youth Sports Swag Bot, please check the logs and verify your API credentials are correct.

---

**Built with ❤️ for youth sports parents who want awesome team merchandise! 🏆** 