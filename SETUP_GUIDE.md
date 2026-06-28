# Setup Guide — do this once, then it runs forever by itself

This guide is written in plain steps for a screen reader. Every step is numbered.
Take it slowly. You only do this ONCE. After it is done, the bot posts 2 Shorts a
day on its own, with your computer off.

There are 4 parts:
A. Get a free Gemini API key.
B. Authorize YouTube (the longest part).
C. Put the project on GitHub and add your keys.
D. Turn on the schedule and test.

If any single step is hard with a screen reader, you can ask a trusted person to
help with just that one step. Nothing here ever needs to be repeated later.

--------------------------------------------------------------------------------
PART A. Free Gemini API key (about 3 minutes)
--------------------------------------------------------------------------------

1. In a browser go to: https://aistudio.google.com/app/apikey
2. Sign in with your Google account.
3. Activate the button that says "Create API key".
4. Copy the key it gives you. It is a long line of letters and numbers.
5. Paste it somewhere safe for a few minutes (a notepad). You will need it in
   Part C. This key is free and does not need a credit card.

--------------------------------------------------------------------------------
PART B. Authorize YouTube uploads (about 15 minutes, done once)
--------------------------------------------------------------------------------

This lets the bot upload to YOUR channel safely using Google's official method.

First, turn on the YouTube API:

1. Go to: https://console.cloud.google.com/
2. Sign in with the SAME Google account that owns your YouTube channel.
3. At the top, create a new project. Name it "anime bot". Select it.
4. Go to: https://console.cloud.google.com/apis/library/youtube.googleapis.com
5. Activate "Enable". This switches on the YouTube Data API v3.

Next, set up the consent screen:

6. Go to: https://console.cloud.google.com/apis/credentials/consent
7. Choose "External", then Create.
8. Fill App name "anime bot", your email for support, your email for developer
   contact. Save and continue through the next screens (you can leave scopes
   empty). On "Test users", add your own Gmail address. Save.

Now create the login key (OAuth client):

9. Go to: https://console.cloud.google.com/apis/credentials
10. Activate "Create credentials", then "OAuth client ID".
11. Application type: choose "Desktop app". Name it "anime bot". Create.
12. A box appears with a download option. Download the JSON file.
13. Rename that file to exactly:  yt_client_secret.json
14. Put it inside the project's "secrets" folder, so the path is:
        anime auto bot/secrets/yt_client_secret.json
    (Create the "secrets" folder if it is not there.)

Now make the token. This step opens a browser to approve once. It needs Python
and FFmpeg installed on your computer (see the box at the bottom for installing).

15. Open a terminal in the "anime auto bot" folder and run these two lines:
        pip install -r requirements.txt
        python scripts/setup_youtube_oauth.py
16. A browser window opens. Sign in, and approve. If it warns the app is
    unverified, choose "Continue" / "Advanced -> go to anime bot (unsafe)".
    This is your own app, so it is safe.
17. When it finishes it prints "Authorized channel: <your channel>" and creates
    a file:  secrets/yt_token.json
    Part B is done. You never repeat it (unless you change channels).

--------------------------------------------------------------------------------
PART C. Put it on GitHub and add your keys (about 10 minutes)
--------------------------------------------------------------------------------

GitHub will run the bot for free in the cloud on a schedule.

1. Make a free account at https://github.com if you do not have one.
2. Create a new repository. Name it "anime-auto-bot". Make it Private. Create it.
3. Upload this whole "anime auto bot" folder into the repository. The easiest way
   without commands: on the repo page use "Add file" -> "Upload files", drag the
   folder contents in, and Commit.
   IMPORTANT: the .gitignore already stops your private "secrets" folder from
   being uploaded. That is on purpose — keys must NOT go into the code. They go
   into GitHub Secrets next.
4. In the repository, open: Settings -> Secrets and variables -> Actions.
5. Activate "New repository secret" and add these THREE secrets:

   Secret 1
     Name:  GEMINI_API_KEY
     Value: the Gemini key from Part A.

   Secret 2
     Name:  YT_CLIENT_SECRET_JSON
     Value: open secrets/yt_client_secret.json on your computer, copy ALL of its
            text, and paste it as the value.

   Secret 3
     Name:  YT_TOKEN_JSON
     Value: open secrets/yt_token.json on your computer, copy ALL of its text,
            and paste it as the value.

   Save each one. These are encrypted by GitHub and never shown again.

--------------------------------------------------------------------------------
PART D. Turn it on and test (2 minutes)
--------------------------------------------------------------------------------

1. In the repository open the "Actions" tab. If it asks to enable workflows,
   enable them.
2. Open the workflow named "Post anime Short".
3. Activate "Run workflow" to do a manual test run right now.
4. Wait a few minutes. When the run finishes with a green check, your first
   Short is on your YouTube channel. (Open the run to download the video file
   and logs under "Artifacts" if you want to check it.)
5. From now on it runs automatically twice every day. Nothing else to do.

The two daily times are set in .github/workflows/publish.yml:
   2:00 PM India time and 9:00 PM India time. You can change those lines later.

--------------------------------------------------------------------------------
ADJUSTING THINGS (optional, anytime)
--------------------------------------------------------------------------------

Open config.example.yaml (or make a copy named config.yaml) and edit:

- channel.language:  "en" English, "hi" Hindi, or "hinglish".
- content.scenes:    how many images per Short (7 to 10). More = longer video.
- video.rain:        true or false to turn rain on/off.
- video.rain_opacity: 0.0 to 1.0, how heavy the rain looks.
- image.character:   change the recurring character's description.
- image.style_suffix: change the overall art style.
- publish.youtube.privacy: set to "private" while testing, "public" to go live.

MUSIC: drop a few free .mp3 files into assets/music/ (see that folder's note for
free, copyright-safe sources). If it is empty, the bot makes a soft ambient
sound automatically so videos always have audio.

--------------------------------------------------------------------------------
INSTALLING PYTHON + FFMPEG ON WINDOWS (only needed for the one-time Part B)
--------------------------------------------------------------------------------

- Python: install from https://www.python.org/downloads/ and during install
  tick "Add Python to PATH".
- FFmpeg: the simplest way is to open PowerShell and run:
      winget install Gyan.FFmpeg
  Then close and reopen the terminal so it is found.

You do NOT need FFmpeg or Python for the daily runs — GitHub installs them in the
cloud. They are only for the single local authorization in Part B.

--------------------------------------------------------------------------------
SAFETY + GOOD-TO-KNOW
--------------------------------------------------------------------------------

- Keep the repository Private. Never paste your keys into the code files; only
  into GitHub Secrets.
- Free Gemini allows around 500 images a day — far more than the ~18 this bot
  needs for 2 Shorts. You will not hit the limit.
- Uploading a video costs about 100 of YouTube's 10,000 free daily units, so 2
  uploads a day is comfortable.
- If Google ever renames the free image model, change ONE line in the config:
  image.model. Today it is gemini-2.0-flash-preview-image-generation.
- Earning money needs YouTube's bar: 1,000 subscribers + 4,000 watch hours, or
  10 million Shorts views in 90 days. This posts daily so you keep building
  toward it. Be patient and let it run.
