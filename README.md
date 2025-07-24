# Smart Talent Profile Builder

## Project Structure

```
smart-talent-profile-builder/
│
├── backend/
│   ├── main.py                    # Complete FastAPI application (from artifact 1)
│   ├── requirements.txt           # Python dependencies (from artifact 3)
│   ├── test_api.py               # API test script (from artifact 5)
│   ├── .env                      # Environment variables (you create this)
│   └── talent_profiles.db        # SQLite database (auto-created when you run)
│
└── README.md                    # Documentation (from artifact 4)
```


---

## What You Actually Get

### Backend Features:
- ✅ FastAPI server with 5 endpoints
- ✅ SQLite database with 2 tables
- ✅ Gemini AI integration
- ✅ Mock data scrapers for Instagram/LinkedIn/websites
- ✅ Automatic profile building with AI

## What it actually does

This FastAPI application, **Smart Talent Profile Builder**, automates the creation of professional profiles by aggregating and enriching data from multiple sources such as Instagram, LinkedIn, personal websites, and resumes. When a user provides one or more source links or files, the system scrapes relevant content like bios, captions, posts, experience, education, and media and uses Gemini AI to extract professional skills, analyze portfolio images, and generate a concise and engaging bio. The enriched data is structured into a profile containing personal details, skills, social links, and tagged portfolio items. This profile is then stored in a SQLite database and can be retrieved or listed through API endpoints. AI enhanced components include skill extraction from text, bio generation based on experience and profession, and visual analysis of uploaded images.
