import os
import praw
import argparse
from urllib.parse import urlparse
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def get_username_from_url(url: str) -> str:
    """Extracts the Reddit username from a profile URL."""
    parsed_path = urlparse(url).path
    # The path will be something like '/user/username/'
    parts = parsed_path.strip('/').split('/')
    if len(parts) >= 2 and parts[0].lower() == 'user':
        return parts[1]
    raise ValueError("Invalid Reddit user profile URL format.")

def scrape_reddit_data(username: str, reddit_client: praw.Reddit, post_limit: int = 50, comment_limit: int = 200):
    """
    Scrapes a user's most recent posts and comments.

    Args:
        username (str): The Reddit username.
        reddit_client (praw.Reddit): An authenticated PRAW instance.
        post_limit (int): Max number of posts to fetch.
        comment_limit (int): Max number of comments to fetch.

    Returns:
        A tuple containing two lists: posts and comments.
    """
    print(f"Scraping data for Reddit user: {username}...")
    try:
        redditor = reddit_client.redditor(username)
        # Check if the user exists or is suspended
        redditor.id
    except Exception as e:
        print(f"Error: Cannot fetch user '{username}'. The user may not exist or is suspended. Details: {e}")
        return [], []

    posts = []
    comments = []

    # Fetch posts
    try:
        for submission in redditor.submissions.new(limit=post_limit):
            posts.append({
                "title": submission.title,
                "text": submission.selftext,
                "url": f"https://www.reddit.com{submission.permalink}",
                "subreddit": submission.subreddit.display_name
            })
    except Exception as e:
        print(f"Could not fetch posts for {username}. It might be a private profile. Error: {e}")

    # Fetch comments
    try:
        for comment in redditor.comments.new(limit=comment_limit):
            comments.append({
                "text": comment.body,
                "url": f"https://www.reddit.com{comment.permalink}",
                "subreddit": comment.subreddit.display_name
            })
    except Exception as e:
        print(f"Could not fetch comments for {username}. It might be a private profile. Error: {e}")
        
    print(f"Scraping complete. Found {len(posts)} posts and {len(comments)} comments.")
    return posts, comments

def generate_user_persona(username: str, posts: list, comments: list, llm_chain) -> str:
    """
    Generates a user persona using an LLM based on their posts and comments.
    """
    if not posts and not comments:
        return "No data available to generate a persona. The user's profile might be private, new, or empty."

    print("Generating user persona with Google Gemini Flash 1.5...")

    # Format the scraped data for the prompt
    formatted_posts = "\n".join(
        [f"- Subreddit: r/{p['subreddit']}, Title: {p['title']}\n  Text: {p['text']}\n  URL: {p['url']}" for p in posts]
    )
    formatted_comments = "\n".join(
        [f"- Subreddit: r/{c['subreddit']}\n  Comment: {c['text']}\n  URL: {c['url']}" for c in comments]
    )


    # Invoke the LCEL chain
    persona = llm_chain.invoke({
        "username": username,
        "posts": formatted_posts,
        "comments": formatted_comments
    })

    print("Persona generation complete.")

    return persona

def main():
    """Main function to orchestrate the persona generation process."""
    # --- Load Credentials ---
    load_dotenv()
    reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not all([reddit_client_id, reddit_client_secret, reddit_user_agent, google_api_key]):
        print("Error: Missing API credentials in .env file. Please check your setup.")
        return

    # --- Interactive URL Input ---
    url = input("Enter the full URL of the Reddit user's profile: ")
    try:
        target_username = get_username_from_url(url)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # --- Initialize PRAW and Google AI ---
    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
    )

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=google_api_key)

    # --- Define Prompt and Build LCEL Chain ---
    persona_template = """
    Based on the following Reddit posts and comments from the user '{username}', create a detailed user persona.

    **Collected Posts:**
    {posts}

    **Collected Comments:**
    {comments}

    **Instructions for Persona Generation:**
    1.  Analyze the provided text to infer the user's characteristics.
    2.  For each point in the persona, you MUST cite the specific URL of the post or comment that supports your conclusion.
    3.  If information for a category is not found, explicitly state "Not enough information to determine."
    4.  Synthesize the information into a coherent persona following the structure below.

    **--- User Persona for {username} ---**

    **1. Demographics (Inferred)**
    *   **Age Range:** [Provide an estimated age range and cite the source URL]
    *   **Gender:** [Infer gender if possible and cite the source URL]
    *   **Location:** [Infer location (country, region, or city) and cite the source URL]
    *   **Occupation/Field of Study:** [Infer occupation or field and cite the source URL]

    **2. Key Interests & Hobbies**
    *   [Interest 1]: [Describe the interest and cite the source URL]
    *   [Interest 2]: [Describe the interest and cite the source URL]
    *   [Add more as found]

    **3. Personality & Communication Style**
    *   **Personality Traits:** [Describe traits like helpful, analytical, humorous, etc., and cite the source URL(s)]
    *   **Communication Style:** [Describe their tone - e.g., formal, casual, technical, uses slang. Cite the source URL(s)]
    
    **4. Topics of Expertise / Frequent Discussion**
    *   [Topic 1]: [Describe the topic the user seems knowledgeable about and cite the source URL]
    *   [Add more as found]
    
    **5. Summary Narrative**
    [Provide a brief, holistic paragraph summarizing the user's likely persona based on all the evidence.]
    """
    
    prompt = ChatPromptTemplate.from_template(persona_template)
    chain = prompt | llm | StrOutputParser()

    # --- Execute the Process ---
    posts, comments = scrape_reddit_data(target_username, reddit)
    user_persona = generate_user_persona(target_username, posts, comments, chain)

    # --- Save Output to File in persona folder ---
    output_dir = os.path.join(os.path.dirname(__file__), "persona")
    output_filename = os.path.join(output_dir, f"{target_username}_persona.txt")
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(user_persona)

    print(f"\nSuccess! User persona has been saved to '{output_filename}'")


if __name__ == "__main__":
    main()