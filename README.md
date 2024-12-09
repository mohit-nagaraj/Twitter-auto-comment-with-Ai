# Twitter Bot with AI-Powered Replies

An automated Twitter bot that monitors your feed and generates contextual replies using Google's Gemini AI.

## Features

- **Automated Feed Monitoring**
  - Processes up to 20 tweets per refresh cycle
  - Smart scrolling to load more content
  - 10-second refresh interval between cycles
  - Skips replies and already processed tweets
  - Avoids replying to own tweets

- **AI-Powered Responses**
  - Uses Google Gemini AI for contextual replies
  - Intelligent text cleaning for non-ASCII characters
  - Fallback responses when tweet text can't be retrieved

- **Robust Automation**
  - Cookie-based authentication
  - Comprehensive error handling
  - Element interaction retry mechanisms
  - Random delays between replies (10-20 seconds)
  - Automatic scrolling to ensure tweet visibility

## Requirements

- Python 3.8+
- Chrome browser
- Required Chrome Extension:
  - [Control Panel for Twitter](https://chromewebstore.google.com/detail/control-panel-for-twitter/kpmjjdhbcfebfjgdnpjagcndoelnidfj)
- Required Python packages (see requirements.txt):
  - selenium==4.15.2
  - webdriver-manager==4.0.1
  - python-dotenv==1.0.0
  - google-generativeai==0.3.1

## Setup

1. Install Chrome Extension:
   - Visit the [Control Panel for Twitter](https://chromewebstore.google.com/detail/control-panel-for-twitter/kpmjjdhbcfebfjgdnpjagcndoelnidfj) extension page
   - Click "Add to Chrome" to install the extension
   - After installation, ensure the extension is enabled in Chrome

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your credentials:
   ```
   TWITTER_USERNAME=your_username
   TWITTER_PASSWORD=your_password
   COOKIES_FILE=twitter_cookies.json
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Usage

Run the bot:
```bash
python twitter_bot.py
```

The bot will:
1. Login to Twitter using your credentials
2. Monitor your feed continuously
3. Load 20 tweets per cycle
4. Generate and post AI-powered replies
5. Skip replies and previously processed tweets
6. Maintain delays between interactions

## Error Handling

- Retries for element interactions
- Fallback mechanisms for tweet text extraction
- Safe error recovery and continuation
- Comprehensive logging of operations
- Automatic page refresh on errors

## Safety Features

- Cookie-based authentication for security
- Text cleaning for safe responses
- Skip mechanisms for replies and own tweets
- Rate limiting through random delays
- Maximum processed tweet history management

## Notes

- The bot maintains a history of processed tweets to avoid duplicates
- Cleans up history periodically (keeps last 100 processed tweets)
- Uses smart scrolling to ensure fresh content loading
- Implements safe error recovery mechanisms
- The Control Panel for Twitter extension is required for proper bot functionality
