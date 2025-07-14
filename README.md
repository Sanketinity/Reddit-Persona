# Reddit Persona Generator

This project scrapes Reddit user data (posts and comments) and generates a detailed persona using Google Gemini Flash 1.5 via LangChain.

## Features
- Scrapes recent posts and comments from any Reddit user profile
- Uses Google Generative AI to synthesize a persona
- Saves the persona to a text file in the `persona/` folder

## Setup Instructions

### 1. Clone or Download the Repository
Place all files in a folder (e.g., `reddit scrapper`).

### 2. Install Python & Dependencies
- Ensure you have Python 3.8 or newer installed.
- Install required packages:

```powershell
pip install -r requirements.txt
```

### 3. Create a `.env` File
Create a `.env` file in the project root with the following variables:

```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent  #user agent needs to be customized, its not mention on reddit pref app page.
GOOGLE_API_KEY=your_google_api_key
```

- Get Reddit API credentials from https://www.reddit.com/prefs/apps
- Get a Google Generative AI API key from https://aistudio.google.com/

### 4. Run the Script

Open a terminal in the project folder and run:

```powershell
python persona_generator.py
```

You will be prompted to enter the full URL of the Reddit user's profile (e.g., `https://www.reddit.com/user/spez/`).

### 5. Output
- The generated persona will be saved as a text file in the `persona/` folder (e.g., `persona/spez_persona.txt`).

## Troubleshooting
- Ensure all API keys and credentials are correct in `.env`.
- If you see missing package errors, re-run `pip install -r requirements.txt`.
- For private or suspended profiles, the script will notify you and skip persona generation.

## License
This project is for educational and research purposes only.
