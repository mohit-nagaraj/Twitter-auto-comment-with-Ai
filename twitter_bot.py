import os
import json
import time
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import google.generativeai as genai

# Load environment variables
load_dotenv()

class TwitterBot:
    def __init__(self):
        self.username = os.getenv('TWITTER_USERNAME')
        self.password = os.getenv('TWITTER_PASSWORD')
        self.cookies_file = os.getenv('COOKIES_FILE')
        # Set Chrome profile path to a custom directory
        self.chrome_profile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chrome_profile')
        
        # Initialize Gemini AI
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Remove the static reply templates as we'll use AI-generated responses
        print("AI model initialized successfully!")
        self.setup_driver()  # Initialize the driver when creating the bot

    def setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        try:
            # Create profile directory if it doesn't exist
            os.makedirs(self.chrome_profile, exist_ok=True)
            
            # Set up Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--user-data-dir={self.chrome_profile}')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize the Chrome WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            # Navigate to Twitter
            print("Opening Twitter...")
            self.driver.get("https://twitter.com")
            print("Twitter opened successfully!")
                
        except Exception as e:
            print(f"Error setting up Chrome driver: {str(e)}")
            if hasattr(self, 'driver'):
                self.driver.quit()
            raise e

    def save_cookies(self):
        """Save cookies to file"""
        with open(self.cookies_file, 'w') as f:
            json.dump(self.driver.get_cookies(), f)

    def load_cookies(self):
        """Load cookies from file if exists"""
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            return True
        except FileNotFoundError:
            return False

    def login(self):
        """Login to Twitter using credentials"""
        try:
            print("Starting login process...")
            self.driver.get('https://x.com/i/flow/login')
            time.sleep(5)  # Wait for page to fully load
            
            print("Checking for existing cookies...")
            if not self.load_cookies():
                print("No existing cookies found. Proceeding with manual login...")
                
                # Wait and enter username
                print("Looking for username field...")
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
                )
                print("Found username field, entering username...")
                username_input.clear()
                for char in self.username:
                    username_input.send_keys(char)
                    time.sleep(0.1)
                time.sleep(1)
                username_input.send_keys(Keys.RETURN)
                time.sleep(2)
                
                # Wait and enter password
                print("Looking for password field...")
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
                )
                print("Found password field, entering password...")
                password_input.clear()
                for char in self.password:
                    password_input.send_keys(char)
                    time.sleep(0.1)
                time.sleep(1)
                password_input.send_keys(Keys.RETURN)
                
                # Wait for login to complete
                print("Waiting for login to complete...")
                time.sleep(10)
                self.save_cookies()
            
            # Navigate to home feed
            print("Navigating to home feed...")
            self.driver.get('https://x.com/home')
            time.sleep(5)
            
            # Verify login success
            if "home" in self.driver.current_url.lower():
                print("Successfully logged in!")
                return True
            else:
                print("Login verification failed. Current URL:", self.driver.current_url)
                return False
            
        except Exception as e:
            print(f"Login failed with error: {str(e)}")
            print("Current URL:", self.driver.current_url)
            return False

    def get_feed_tweets(self):
        """Get tweets from the home feed"""
        try:
            # Wait for tweets to load
            tweets = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            return tweets
        except Exception as e:
            print(f"Error getting feed tweets: {str(e)}")
            return []

    def get_tweet_text(self, tweet_element):
        """Extract text content from a tweet"""
        try:
            text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
            return text_element.text
        except NoSuchElementException:
            print("Could not find tweet text element")
            return None
        except Exception as e:
            print(f"Error getting tweet text: {str(e)}")
            return None

    def get_tweet_id(self, tweet_element):
        """Extract unique identifier for a tweet"""
        try:
            # Try to get the tweet link first
            time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
            tweet_link = time_element.find_element(By.XPATH, '..').get_attribute('href')
            
            # Also try to get the tweet author to make the ID more unique
            try:
                author_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                author_name = author_element.text.split('\n')[0]  # Get the first line which is usually the name
                return f"{author_name}_{tweet_link}"
            except:
                return tweet_link
        except NoSuchElementException:
            return None

    def get_tweet_timestamp(self, tweet_element):
        """Extract timestamp from a tweet"""
        try:
            time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
            timestamp = time_element.get_attribute('datetime')
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        except (NoSuchElementException, ValueError) as e:
            print(f"Error getting tweet timestamp: {str(e)}")
            return None

    def is_within_24_hours(self, tweet_element):
        """Check if tweet is within the last 24 hours"""
        tweet_time = self.get_tweet_timestamp(tweet_element)
        if tweet_time:
            current_time = datetime.utcnow()
            time_difference = current_time - tweet_time
            return time_difference <= timedelta(hours=24)
        return False

    def is_own_tweet(self, tweet_element):
        """Check if the tweet is from our own account"""
        try:
            # Find the username element within the tweet
            username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
            username_text = username_element.text.lower()
            our_username = os.getenv('TWITTER_USERNAME', '').lower()
            
            # Check if our username appears in the tweet's user info
            return our_username in username_text
        except Exception as e:
            print(f"Error checking tweet ownership: {str(e)}")
            return True  # If we can't verify, skip it to be safe

    def is_reply_tweet(self, tweet_element):
        """Check if the tweet is a reply"""
        try:
            # Check for reply indicator elements
            reply_indicators = tweet_element.find_elements(By.CSS_SELECTOR, '[data-testid="socialContext"]')
            if reply_indicators:
                return True

            # Also check for "Replying to" text
            replying_to = tweet_element.find_elements(By.XPATH, './/*[contains(text(), "Replying to")]')
            if replying_to:
                return True

            return False
        except Exception as e:
            print(f"Error checking if tweet is reply: {str(e)}")
            return True  # If we can't verify, skip it to be safe

    def clean_text(self, text):
        """Clean text to ensure it only contains supported characters"""
        if not text:
            return text
        # Remove emojis and other special characters
        cleaned = text.encode('ascii', 'ignore').decode('ascii')
        return cleaned or "Hmm"  # Return "Hmm" if cleaning results in empty string

    def generate_ai_response(self, tweet_text):
        """Generate a contextual response using Gemini AI"""
        try:
            prompt = f"""
            Generate a friendly and engaging response to this tweet. The response should be:
            1. Relevant to the tweet content
            2. Casual and conversational
            3. Not longer than 200 characters
            4. Without hashtags or emojis
            5. Engaging but not controversial
            6. Use only basic ASCII characters
            
            Tweet: "{tweet_text}"
            
            Response:"""
            
            response = self.model.generate_content(prompt)
            ai_reply = response.text.strip().strip('"')  # Remove quotes if present
            
            # Clean the response text
            ai_reply = self.clean_text(ai_reply)
            
            # Ensure the response isn't too long for Twitter
            if len(ai_reply) > 200:
                ai_reply = ai_reply[:197] + "..."
                
            print(f"Generated AI response: {ai_reply}")
            return ai_reply
            
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return "Hmm"  # Fallback response

    def find_element_with_retry(self, by, value, max_attempts=3, check_interactable=False):
        """Find an element with retry logic for stale elements"""
        for attempt in range(max_attempts):
            try:
                if check_interactable:
                    # Wait for element to be clickable
                    element = self.wait.until(
                        EC.element_to_be_clickable((by, value))
                    )
                else:
                    # Wait for element to be present and visible
                    element = self.wait.until(
                        EC.presence_of_element_located((by, value))
                    )
                    if not element.is_displayed():
                        raise Exception("Element is not visible")
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)  # Wait for scroll to complete
                
                return element
            except Exception as e:
                if attempt == max_attempts - 1:  # Last attempt
                    print(f"Failed to find element after {max_attempts} attempts: {str(e)}")
                    raise e
                print(f"Retrying to find element... Attempt {attempt + 2}/{max_attempts}")
                time.sleep(1)
        return None

    def reply_to_tweet(self, tweet_element):
        """Reply to a specific tweet with an AI-generated response"""
        try:
            # First, ensure we're working with the correct tweet by scrolling it into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", tweet_element)
            time.sleep(2)  # Wait for scroll to complete

            # Re-find the tweet element to ensure it's fresh
            tweet_link = self.get_tweet_id(tweet_element)
            if not tweet_link:
                print("Could not get tweet link, skipping...")
                return False

            # Get the tweet text with retry
            try:
                # Find text element within this specific tweet
                text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = text_element.text if text_element else None
            except Exception:
                tweet_text = None

            # Use fallback comment if tweet text couldn't be retrieved
            if not tweet_text:
                print("Could not get tweet text, using fallback comment: 'Hmm'")
                reply_text = "Hmm"
            else:
                # Generate AI response for valid tweet text
                reply_text = self.generate_ai_response(tweet_text)
            
            # Clean the reply text
            reply_text = self.clean_text(reply_text)
            
            # Find the reply button within this specific tweet
            try:
                reply_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
                if not reply_button.is_displayed():
                    print("Reply button not visible, skipping...")
                    return False
            except Exception as e:
                print(f"Could not find reply button: {str(e)}")
                return False

            # Click the reply button
            try:
                reply_button.click()
            except:
                try:
                    self.driver.execute_script("arguments[0].click();", reply_button)
                except Exception as e:
                    print(f"Could not click reply button: {str(e)}")
                    return False
            time.sleep(2)

            # Now find the reply box in the popup
            try:
                reply_box = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
                )
                if not reply_box.is_displayed():
                    print("Reply box not visible, skipping...")
                    return False
            except Exception as e:
                print(f"Could not find reply box: {str(e)}")
                return False

            # Try to enter the reply text
            try:
                reply_box.clear()
                reply_box.send_keys(reply_text)
            except Exception as e:
                print(f"Could not enter reply text: {str(e)}")
                try:
                    # Fallback: try character by character
                    reply_box.clear()
                    for char in reply_text:
                        reply_box.send_keys(char)
                        time.sleep(0.05)
                except Exception as e:
                    print(f"Could not enter reply text character by character: {str(e)}")
                    return False

            # Find and click the tweet button
            try:
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButton"]'))
                )
                submit_button.click()
            except Exception as e:
                print(f"Could not click tweet button: {str(e)}")
                try:
                    self.driver.execute_script("arguments[0].click();", submit_button)
                except:
                    return False

            # Wait for the reply to be posted
            time.sleep(3)
            return True

        except Exception as e:
            print(f"Error replying to tweet: {str(e)}")
            return False

    def scroll_to_top(self):
        """Scroll to the top of the feed"""
        try:
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(2)  # Wait for scroll to complete
        except Exception as e:
            print(f"Error scrolling to top: {str(e)}")

    def scroll_feed(self, scroll_count=3):
        """Scroll the feed to load more tweets"""
        try:
            for _ in range(scroll_count):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Wait for content to load
        except Exception as e:
            print(f"Error scrolling feed: {str(e)}")

    def get_recent_tweets(self, max_tweets=20):
        """Get the most recent tweets from the feed"""
        try:
            # First scroll to top to ensure we're at the latest tweets
            self.scroll_to_top()
            time.sleep(2)  # Wait for initial load
            
            # Scroll a few times to load more tweets
            self.scroll_feed(scroll_count=3)
            
            # Wait for tweets to load
            tweets = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            
            if not tweets:
                return []

            print(f"Found {len(tweets)} tweets total")
            
            # Ensure we're getting fresh tweet elements
            fresh_tweets = []
            processed_count = 0
            
            for tweet in tweets:
                try:
                    # Skip if tweet is not displayed or we can't get its ID
                    if not tweet.is_displayed() or not self.get_tweet_id(tweet):
                        continue
                        
                    # Skip our own tweets and replies
                    if self.is_own_tweet(tweet):
                        print("Skipping our own tweet")
                        continue
                        
                    # Skip if it's a reply
                    if self.is_reply_tweet(tweet):
                        print("Skipping reply tweet")
                        continue
                        
                    fresh_tweets.append(tweet)
                    processed_count += 1
                    
                    # Break if we have enough valid tweets
                    if processed_count >= max_tweets:
                        break
                        
                except Exception as e:
                    print(f"Error processing tweet in get_recent_tweets: {str(e)}")
                    continue
            
            print(f"Retrieved {len(fresh_tweets)} valid tweets to process")
            return fresh_tweets
        except Exception as e:
            print(f"Error getting recent tweets: {str(e)}")
            return []

    def monitor_feed(self, interval=10):
        """Monitor the home feed and reply to new tweets"""
        if not self.login():
            print("Failed to login. Please check your credentials.")
            return

        processed_tweets = set()
        print("Starting feed monitoring...")
        
        while True:
            try:
                print("Refreshing feed...")
                self.driver.refresh()
                time.sleep(5)
                
                print("Getting tweets to process...")
                tweets = self.get_recent_tweets(max_tweets=20)  # Get 20 most recent tweets
                print(f"Found {len(tweets)} tweets to process")
                
                tweets_processed_this_round = 0
                
                for tweet in tweets:
                    try:
                        tweet_id = self.get_tweet_id(tweet)
                        if not tweet_id:
                            print("Could not get tweet ID, skipping...")
                            continue
                            
                        if tweet_id in processed_tweets:
                            print(f"Already processed tweet: {tweet_id}")
                            continue
                        
                        print(f"Processing tweet: {tweet_id}")
                        if self.reply_to_tweet(tweet):
                            processed_tweets.add(tweet_id)
                            tweets_processed_this_round += 1
                            print(f"Successfully replied to tweet: {tweet_id}")
                            time.sleep(random.uniform(10, 20))  # Random delay between replies
                    except Exception as e:
                        print(f"Error processing tweet: {str(e)}")
                        continue
                
                print(f"Processed {tweets_processed_this_round} new tweets this round")
                
                # Keep only the 100 most recent processed tweets to maintain a smaller window
                if len(processed_tweets) > 100:
                    print("Cleaning up processed tweets list...")
                    processed_list = list(processed_tweets)
                    processed_tweets = set(processed_list[-100:])
                
                print(f"Waiting {interval} seconds before next refresh...")
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in feed monitoring: {str(e)}")
                print("Attempting to refresh page...")
                try:
                    self.driver.refresh()
                except:
                    pass
                time.sleep(interval)

    def cleanup(self):
        """Close the browser and clean up"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    bot = TwitterBot()
    try:
        # Changed interval to 10 seconds to match monitor_feed default
        bot.monitor_feed(interval=10)
    except KeyboardInterrupt:
        print("\nStopping bot...")
    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()
