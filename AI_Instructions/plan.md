# MiM Youth Sports Team Swag Slack Bot - Action Plan

## 🎯 Project Overview
Build a Slack bot that helps parents customize youth sports team merchandise by:
- Filtering products tagged as "best" from product_cache.json
- Accepting team logo uploads (file or URL)
- Using OpenAI to understand parent requests
- Applying logos to products via Printify API
- Displaying customized products directly in Slack with purchase links

## 🔧 Technical Requirements
- **Platform**: Slack Bot app (DMs and channels)
- **Logo Input**: Both file upload and URL input
- **Product Selection**: Ask parents to specify product type if not mentioned
- **AI**: OpenAI for natural language understanding
- **APIs**: Printify for product customization
- **Display**: Show images in Slack + provide Printify purchase links

## 📋 Actionable Implementation Plan

### Phase 1: Foundation & Slack Bot Setup (Day 1)
1. **Environment Setup**
   - ✅ Load existing Printify and OpenAI credentials from .env
   - Create Slack app configuration and get bot token
   - Set up Flask application structure

2. **Core Slack Integration**
   - Implement Slack Events API webhook endpoints
   - Add request verification for Slack signatures
   - Create basic message handling and responses
   - Test bot connectivity in Slack workspace

### Phase 2: Product Intelligence (Day 1-2)
3. **Product Cache Service**
   - Create service to filter "best" tagged products:
     - Product ID 124: Kids Heavy Cotton Tee
     - Product ID 325: Youth Heavy Blend Hooded Sweatshirt  
     - Product ID 1446: Snapback Trucker Cap
   - Format product info for Slack display (with colors, categories)

4. **OpenAI Integration**
   - Implement conversation handler using OpenAI
   - Create prompts to understand parent requests
   - Extract product preferences from natural language
   - Handle product type clarification when not specified

### Phase 3: Logo Processing (Day 2)
5. **Logo Upload Handling**
   - Accept Slack file uploads (images)
   - Process URL inputs for logo images
   - Validate image formats (PNG, JPG, SVG)
   - Store/cache logos temporarily for processing

### Phase 4: Printify Integration (Day 2-3)
6. **Product Customization**
   - Set up Printify API client with existing credentials
   - Implement logo application to selected products
   - Generate product mockups/renders
   - Handle Printify API errors gracefully

7. **Purchase Link Generation**
   - Create Printify product listings with applied logos
   - Generate purchase URLs for parents
   - Format links for Slack display

### Phase 5: Slack Response System (Day 3)
8. **Rich Message Formatting**
   - Display customized product images directly in Slack
   - Add product details (colors, sizes available)
   - Include purchase buttons/links
   - Handle conversation flow management

9. **Error Handling**
   - Graceful handling of API failures
   - User-friendly error messages
   - Fallback responses for edge cases

### Phase 6: Testing & Polish (Day 3)
10. **Integration Testing**
    - Test complete flow: request → product selection → logo upload → customization → display
    - Test both file upload and URL input methods
    - Verify purchase links work correctly

11. **Deployment Preparation**
    - Set up production environment configuration
    - Add logging and monitoring
    - Create deployment documentation

## 🏗️ Architecture Overview

```
Parent Message → Slack Bot → OpenAI Analysis → Product Selection
                                    ↓
Logo Upload/URL → Image Processing → Printify API → Product Mockup
                                    ↓
Customized Product Images → Slack Display + Purchase Links
```

## 📁 File Structure
```
MiM_slack/
├── app.py                  # Main Flask application
├── slack_bot.py           # Slack event handling
├── product_service.py     # Product cache filtering
├── openai_service.py      # AI conversation handling  
├── printify_service.py    # Printify API integration
├── logo_processor.py      # Image upload/URL handling
├── .env                   # API credentials
└── requirements.txt       # Dependencies
```

## 🎯 Success Criteria
- Parents can request products in natural language
- Bot correctly identifies product preferences or asks for clarification
- Logo uploads work via both file and URL methods
- Customized products display properly in Slack
- Purchase links direct to working Printify listings
- Sub-5 second response times for most interactions

## 📦 Key Dependencies
- `slack-sdk` - Slack API integration
- `flask` - Web framework for webhooks
- `openai` - AI conversation handling
- `requests` - HTTP requests for Printify API
- `pillow` - Image processing
- `python-dotenv` - Environment variable management

Let's build a youth sports team swag bot that makes parents' lives easier! 🏆 