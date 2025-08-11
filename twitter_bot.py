import os
import json
import time
import random
import sys
import traceback

print("=== Importing required modules ===")

try:
    print("Importing dotenv...")
    from dotenv import load_dotenv
    print("✓ dotenv imported successfully")
except Exception as e:
    print(f"❌ Failed to import dotenv: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    print("Importing selenium modules...")
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    print("✓ selenium modules imported successfully")
except Exception as e:
    print(f"❌ Failed to import selenium modules: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    print("Importing datetime...")
    from datetime import datetime, timedelta
    print("✓ datetime imported successfully")
except Exception as e:
    print(f"❌ Failed to import datetime: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    print("Importing google.genai...")
    import google.genai as genai
    print("✓ google.genai imported successfully")
except Exception as e:
    print(f"❌ Failed to import google.genai: {e}")
    print("Please install it with: pip install google-genai")
    input("Press Enter to exit...")
    sys.exit(1)

print("\n=== Starting Twitter Bot ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Load environment variables
load_dotenv()
print("Environment variables loaded")

# Check required environment variables
env_vars = {
    'TWITTER_USERNAME': os.getenv('TWITTER_USERNAME'),
    'TWITTER_PASSWORD': os.getenv('TWITTER_PASSWORD'),
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    'COOKIES_FILE': os.getenv('COOKIES_FILE')
}

print("\n=== Environment Variables Status ===")
for key, value in env_vars.items():
    if value:
        if 'PASSWORD' in key or 'API_KEY' in key:
            print(f"{key}: {'*' * 8} (hidden)")
        else:
            print(f"{key}: {value}")
    else:
        print(f"{key}: NOT SET ⚠️")

missing_vars = [k for k, v in env_vars.items() if not v]
if missing_vars:
    print(f"\n⚠️ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file")
    sys.exit(1)

class TwitterBot:
    def __init__(self):
        print("\n=== Initializing TwitterBot ===")
        try:
            self.username = os.getenv('TWITTER_USERNAME')
            self.password = os.getenv('TWITTER_PASSWORD')
            self.cookies_file = os.getenv('COOKIES_FILE')
            # Set Chrome profile path to a custom directory
            self.chrome_profile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chrome_profile')
            print(f"Chrome profile directory: {self.chrome_profile}")
            
            # Initialize Gemini AI
            print("\nInitializing Gemini AI...")
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            self.client = genai.Client(api_key=gemini_api_key)
            self.models = self.client.models
            print("✓ Gemini AI client initialized successfully!")
        except Exception as e:
            print(f"\n❌ Error during initialization: {str(e)}")
            print(traceback.format_exc())
            sys.exit(1)
        
        self.tech_search_queries = [
            "Next.js", "Node.js", "Express.js", "Golang", "CI/CD", "Docker",
            "#fullstackdev", "#webdev", "#softwareengineering",
            "cloud computing", "#AWS", "#GCP", "#Azure", "#DevOps",
            "serverless", "microservices", "kubernetes", "reactjs"
        ]
        print(f"\nSearch queries configured: {len(self.tech_search_queries)} queries")
        
        # Initialize the driver when creating the bot
        print("\n=== Setting up Chrome Driver ===")
        self.setup_driver()

    def setup_driver(self):
        print("[setup_driver] Called.")
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
                
            print("[setup_driver] Success.")
        except Exception as e:
            print(f"[setup_driver] Error: {str(e)}")
            if hasattr(self, 'driver'):
                self.driver.quit()
            raise e


    def save_cookies(self):
        print("[save_cookies] Called.")
        with open(self.cookies_file, 'w') as f:
            json.dump(self.driver.get_cookies(), f)
        print("[save_cookies] Cookies saved.")

    def load_cookies(self):
        print("[load_cookies] Called.")
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            print("[load_cookies] Cookies loaded.")
            return True
        except FileNotFoundError:
            print("[load_cookies] No cookies file found.")
            return False

    def login(self):
        print("[login] Called.")
        try:
            print("Starting login process...")
            print("Navigating to login flow...")
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
            if "home" in self.driver.current_url.lower() or "communities/1493446837214187523" or "communities/1471580197908586507" in self.driver.current_url:
                print("Successfully logged in and navigated to the community!")
                # Navigate to the specified community after login
                # print("Navigating to the community page...")
                # self.driver.get('https://x.com/i/communities/1471580197908586507')
                time.sleep(5)
                return True
            else:
                print("Login verification failed. Current URL:", self.driver.current_url)
                return False
            
        except Exception as e:
            print(f"Login failed with error: {str(e)}")
            print("Current URL:", self.driver.current_url)
            return False

    def search_tweets(self, query):
        print(f"[search_tweets] Called with query: {query}")
        try:
            print(f"Searching for tweets with query: {query}")
            search_url = f"https://x.com/search?q={query}&src=typed_query"
            self.driver.get(search_url)
            time.sleep(5)

            tweets = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            print(f"[search_tweets] Found {len(tweets)} tweets for '{query}'")
            return tweets
        except Exception as e:
            print(f"Error searching tweets for query '{query}': {str(e)}")
            return []

    def get_tweet_id(self, tweet_element):
        print("[get_tweet_id] Called.")
        try:
            # Find all anchor tags in the tweet element
            anchors = tweet_element.find_elements(By.TAG_NAME, 'a')
            for anchor in anchors:
                href = anchor.get_attribute('href')
                if href and '/status/' in href:
                    # The tweet ID is the part after the last '/'
                    tweet_id = href.split('/status/')[-1].split('?')[0]
                    print(f"[get_tweet_id] Found tweet_id: {tweet_id}")
                    return tweet_id
            return None
        except Exception as e:
            print(f"Error extracting tweet ID: {str(e)}")
            return None

    def is_blocked_handle(self, tweet_element):
        print("[is_blocked_handle] Called.")
        blocked_handles = [
            'elonmusk',
            'skysingh04'
        ]
        try:
            # Find all anchor tags in the tweet element (recursively)
            anchors = tweet_element.find_elements(By.XPATH, ".//a")
            found_handles = []
            for anchor in anchors:
                href = anchor.get_attribute('href')
                if href:
                    # Check for Twitter/X handle patterns
                    if href.startswith('https://x.com/') or href.startswith('https://twitter.com/'):
                        # Extract handle from full URL
                        parts = href.split('/')
                        if len(parts) >= 4 and parts[3] and '/status/' not in href:
                            handle = parts[3].lower()
                            found_handles.append(handle)
                            print(f"[is_blocked_handle] Checking handle: {handle}")
                            if handle in blocked_handles:
                                print(f"[is_blocked_handle] Blocked handle found: {handle}")
                                return True
                    elif href.startswith('/') and '/status/' not in href and '/search' not in href:
                        handle = href.strip('/').lower()
                        found_handles.append(handle)
                        print(f"[is_blocked_handle] Checking handle: {handle}")
                        if handle in blocked_handles:
                            print(f"[is_blocked_handle] Blocked handle found: {handle}")
                            return True
            
            # Fallback: check if tweet text contains @blocked_handle or handle name
            try:
                tweet_text_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = tweet_text_elem.text.lower()
                for handle in blocked_handles:
                    if f"@{handle}" in tweet_text:
                        print(f"[is_blocked_handle] Blocked handle found in tweet text: {handle}")
                        return True
            except Exception as e:
                print(f"[is_blocked_handle] Could not extract tweet text for fallback: {str(e)}")
            
            print(f"[is_blocked_handle] All found handles in tweet: {found_handles}")
            return False
        except Exception as e:
            print(f"Error checking blocked handle: {str(e)}")
            return False

    def is_own_tweet(self, tweet_element):
        print("[is_own_tweet] Called.")
        try:
            # Find all anchor tags in the tweet element
            anchors = tweet_element.find_elements(By.TAG_NAME, 'a')
            for anchor in anchors:
                href = anchor.get_attribute('href')
                if href and href.startswith('/') and '/status/' not in href:
                    # href is like '/username'
                    handle = href.strip('/').lower()
                    if handle == self.username.lower():
                        print(f"[is_own_tweet] Own tweet found: {handle}")
                        return True
            return False
        except Exception as e:
            print(f"Error checking own tweet: {str(e)}")
            return False

    def is_reply_tweet(self, tweet_element):
        print("[is_reply_tweet] Called.")
        try:
            # Check for 'Replying to' text in the tweet element
            reply_texts = tweet_element.find_elements(By.XPATH, ".//*[contains(text(), 'Replying to')]")
            if reply_texts:
                print(f"[is_reply_tweet] Reply tweet found: {reply_texts[0].text}")
                return True
            # Optionally, check for reply icon or other indicators here
            return False
        except Exception as e:
            print(f"Error checking reply tweet: {str(e)}")
            return False

    def generate_ai_response(self, tweet_text):
        print(f"[generate_ai_response] Called with tweet_text: {tweet_text}")
        try:
            tones = [
                "professional and insightful",
                "light-hearted and witty",
                "assertive and confident",
                "knowledgeable and helpful",
                "slightly egoistic but still professional"
            ]
            selected_tone = random.choice(tones)

            # Mohit Nagaraj's background and skills
            mohit_bio = (
                "You are Mohit Nagaraj, a Computer Science and Engineering student at Dayananda Sagar College Of Engineering (graduating 2026, CGPA 9.23). "
                "You have strong technical skills: JavaScript, TypeScript, Go, Dart, C++. "
                "You work with React, Next.js, Node.js + Express, PostgreSQL, MongoDB, Firestore, Flutter, Git, Redis, and Cloud. "
                "You are experienced with Tailwind, Three.js, OAuth, tRPC, Redux, Context, Firebase, Passport, Prisma, Bootstrap, RESTful API, GraphQL, gRPC, GoFiber, Gin, and Nginx. "
                "Notable projects: Solace (GitHub deploy platform with Docker, AWS S3, Node.js, Redis), VidStreamX (Go, FFmpeg, Docker, AWS S3/SQS), WeChat (React, Vite, Express, Socket.io, MongoDB, AWS EC2/CloudFront), Exsense (Vite, Express, Apollo GraphQL, MongoDB, Passport). "
                "Experience: Frontend Developer at Boho, SellerSetu (Nov 2024 - Feb 2025, Expo React Native, payments, Zustand, React Query), SDE Intern at Springreen (Sep 2024 - Dec 2024, Flask, Golang, CI/CD, microservices on EC2). "
                "Achievements: 1st place Innerve 9 AIT Pune Hackathon (AI EdTech), 2nd place GoFr Hackathon (AI social outreach), Hacktoberfest 2024 open-source contributor. "
                "You are passionate about building, learning, and sharing in the tech community. "
            )

            prompt = f"""
            {mohit_bio}
            Your goal is to increase your outreach on Twitter by providing valuable, engaging, and sometimes humorous or assertive comments.

            TONE: {selected_tone}

            IMPORTANT GUIDELINES:
            - Sound like a real person with a strong technical background.
            - Use professional but accessible language. Avoid overly technical jargon unless it's appropriate for the context.
            - Use abbreviations like 'sheesh', 'cool', 'nice', 'lmao', 'lol', 'tf' sparingly and only when it fits the tone.
            - Keep replies concise and under 280 characters.
            - No hashtags.
            - Be relevant to the tweet's content.
            - Project confidence and expertise.

            Tweet to respond to: "{tweet_text}"

            Generate a natural and engaging reply as Mohit Nagaraj:"""

            response = self.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            ai_reply = response.text.strip().strip('"')

            ai_reply = self.clean_text(ai_reply)

            if len(ai_reply) > 280:
                ai_reply = ai_reply[:277] + "..."

            print(f"Generated AI response (tone: {selected_tone}): {ai_reply}")
            print(f"[generate_ai_response] AI reply: {ai_reply}")
            return ai_reply

        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return "cool"

    def monitor_and_reply(self, interval=60 * 5):
        print(f"[monitor_and_reply] Called with interval: {interval}")
        if not self.login():
            print("Failed to login. Please check your credentials.")
            return

        processed_tweets = set()
        print("Starting to monitor tech tweets...")
        max_tweets_per_query = 5  # Limit tweets per query

        while True:
            random.shuffle(self.tech_search_queries)
            for query in self.tech_search_queries:
                try:
                    print(f"\nProcessing query: {query}")
                    tweets = self.search_tweets(query)
                    print(f"Found {len(tweets)} tweets for '{query}'")

                    tweets_processed_this_round = 0
                    for tweet in tweets[:max_tweets_per_query]:  # Process only first 5 tweets
                        try:
                            tweet_id = self.get_tweet_id(tweet)
                            if not tweet_id or tweet_id in processed_tweets:
                                continue

                            # Check if tweet is already liked (to prevent duplicate comments)
                            if self.is_tweet_already_liked(tweet):
                                print(f"Tweet {tweet_id} already liked, skipping...")
                                processed_tweets.add(tweet_id)
                                continue

                            if self.is_blocked_handle(tweet) or self.is_own_tweet(tweet) or self.is_reply_tweet(tweet):
                                continue
                            
                            print(f"Processing tweet: {tweet_id}")
                            if self.reply_to_tweet(tweet):
                                processed_tweets.add(tweet_id)
                                tweets_processed_this_round += 1
                                print(f"Successfully replied to tweet: {tweet_id}")
                                time.sleep(random.uniform(20, 40))

                        except Exception as e:
                            print(f"Error processing a tweet: {str(e)}")
                            continue
                    
                    print(f"Processed {tweets_processed_this_round} new tweets for query '{query}'")
                    
                    # Add 10 second delay between queries
                    print(f"Waiting 10 seconds before next query...")
                    time.sleep(10)

                except Exception as e:
                    print(f"An error occurred while processing query '{query}': {str(e)}")
                    continue
            
            if len(processed_tweets) > 500:
                print("Cleaning up processed tweets list...")
                processed_list = list(processed_tweets)
                processed_tweets = set(processed_list[-500:])

            print(f"\nFinished a cycle of queries. Waiting {interval} seconds before the next cycle...")
            time.sleep(interval)

    def cleanup(self):
        print("[cleanup] Called.")
        if hasattr(self, 'driver'):
            self.driver.quit()
        print("[cleanup] Browser closed.")

    def clean_text(self, text):
        """Clean the AI-generated text (strip whitespace, remove unwanted characters, etc)."""
        print(f"[clean_text] Called with text: {text}")
        # Basic cleaning: strip whitespace, remove leading/trailing quotes, and remove all '*' characters
        cleaned = text.strip().strip('"').replace('*', '')
        print(f"[clean_text] Returning: {cleaned}")
        return cleaned

    def reply_to_tweet(self, tweet_element):
        """Reply to a tweet using Selenium. Log the tweet_id and the AI-generated reply. Return True if successful, False otherwise."""
        print("[reply_to_tweet] Called.")
        try:
            tweet_id = self.get_tweet_id(tweet_element)
            print(f"[reply_to_tweet] Processing tweet_id: {tweet_id}")
            
            # Like the tweet before replying
            try:
                like_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="like"]')
                like_button.click()
                print(f"[reply_to_tweet] Liked tweet: {tweet_id}")
                time.sleep(1)
            except Exception as e:
                print(f"[reply_to_tweet] Could not like tweet: {str(e)}")
            
            # Extract tweet text for context
            tweet_text = ""
            try:
                tweet_text_elem = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_text = tweet_text_elem.text
            except Exception as e:
                print(f"[reply_to_tweet] Could not extract tweet text: {str(e)}")
            
            ai_reply = self.generate_ai_response(tweet_text)
            print(f"[reply_to_tweet] AI reply: {ai_reply}")
            
            # Find and click the reply button
            reply_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="reply"]')
            reply_button.click()
            time.sleep(2)
            
            # Find the reply text area (should be the only textarea visible)
            reply_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"] div[role="textbox"]'))
            )
            reply_box.send_keys(ai_reply)
            time.sleep(1)
            
            # Find and click the reply submit button
            submit_buttons = tweet_element.parent.find_elements(By.CSS_SELECTOR, 'div[role="dialog"] [data-testid="tweetButton"]')
            if not submit_buttons:
                # Try global search if not found in parent
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"] [data-testid="tweetButton"]')
            
            if submit_buttons:
                submit_buttons[0].click()
                print(f"[reply_to_tweet] Successfully replied to tweet: {tweet_id}")
                time.sleep(2)
                return True
            else:
                print(f"[reply_to_tweet] Could not find reply submit button for tweet: {tweet_id}")
                return False
                
        except Exception as e:
            print(f"[reply_to_tweet] Error replying to tweet: {str(e)}")
            return False

    def is_tweet_already_liked(self, tweet_element):
        """Check if a tweet is already liked by looking for the unlike button."""
        print("[is_tweet_already_liked] Called.")
        try:
            # Check if unlike button exists (which means tweet is already liked)
            unlike_button = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="unlike"]')
            if unlike_button:
                print("[is_tweet_already_liked] Tweet is already liked")
                return True
        except NoSuchElementException:
            # No unlike button means tweet is not liked
            print("[is_tweet_already_liked] Tweet is not liked")
            return False
        except Exception as e:
            print(f"[is_tweet_already_liked] Error checking like status: {str(e)}")
            return False


def main():
    print("\n" + "="*50)
    print("   TWITTER BOT STARTING")
    print("="*50)
    
    try:
        print("\nCreating TwitterBot instance...")
        bot = TwitterBot()
        print("\n✅ Bot initialized successfully!")
        print("\nStarting monitoring loop...")
        bot.monitor_and_reply(interval=60 * 5)  # Check for new tweets every 5 minutes
    except KeyboardInterrupt:
        print("\n\n⚠️ Keyboard interrupt received. Stopping bot...")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        print("\nFull error traceback:")
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'bot' in locals():
            print("\nCleaning up...")
            bot.cleanup()
        print("\nBot stopped.")

if __name__ == "__main__":
    try:
        print("Starting main function...")
        main()
    except Exception as e:
        print(f"\n\n❌ Unhandled exception: {str(e)}")
        print(traceback.format_exc())
        input("\nPress Enter to exit...")
        sys.exit(1)
    except SystemExit as e:
        print(f"\n\n⚠️ Script exited with code: {e.code}")
        if e.code != 0:
            print("This indicates an error occurred during execution.")
        input("\nPress Enter to exit...")
        sys.exit(e.code)
