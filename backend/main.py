from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import requests
import json
import re
import os
from datetime import datetime
import sqlite3
import asyncio
import aiohttp
from urllib.parse import urlparse
import google.generativeai as genai
from PIL import Image
import io
import base64
from dataclasses import dataclass
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Smart Talent Profile Builder", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key")
genai.configure(api_key=GEMINI_API_KEY)

# Database setup
def init_database():
    conn = sqlite3.connect('talent_profiles.db')
    cursor = conn.cursor()
    
    # Create profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT,
            bio TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            profession TEXT,
            skills TEXT,  -- JSON array
            social_links TEXT,  -- JSON object
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create portfolio items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            title TEXT,
            description TEXT,
            media_type TEXT,  -- image, video, document
            media_url TEXT,
            tags TEXT,  -- JSON array
            ai_analysis TEXT,  -- AI-generated insights
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Pydantic models
class ProfileImportRequest(BaseModel):
    user_id: str
    sources: List[str]  
    source_types: List[str]  

class ProfileResponse(BaseModel):
    user_id: str
    name: Optional[str]
    bio: Optional[str]
    email: Optional[str]
    profession: Optional[str]
    skills: List[str]
    social_links: Dict[str, str]
    portfolio_items: List[Dict[str, Any]]

# AI Services
class AIService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image content using Gemini Vision"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            prompt = """
            Analyze this image and provide:
            1. Content type (portrait, landscape, product, artwork, etc.)
            2. Main subjects or themes
            3. Technical quality assessment
            4. Relevant tags/keywords
            5. Professional category (photography, design, art, etc.)
            
            Return as JSON format with keys: content_type, subjects, quality, tags, category
            """
            
            response = self.model.generate_content([prompt, image])
            
            try:
                return json.loads(response.text)
            except:
                return {
                    "content_type": "unknown",
                    "subjects": [],
                    "quality": "medium",
                    "tags": [],
                    "category": "general"
                }
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {"error": str(e)}
    
    async def generate_bio(self, profile_data: Dict[str, Any]) -> str:
        """Generate professional bio using Gemini"""
        try:
            prompt = f"""
            Create a professional bio for a creative professional based on this information:
            
            Name: {profile_data.get('name', 'Unknown')}
            Profession: {profile_data.get('profession', 'Creative Professional')}
            Skills: {', '.join(profile_data.get('skills', []))}
            Portfolio highlights: {profile_data.get('portfolio_summary', 'Various creative works')}
            
            Make it engaging, professional, and 2-3 sentences long. Focus on their creative expertise and unique value.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Bio generation error: {e}")
            return "Creative professional with diverse skills and experience."
    
    async def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using Gemini"""
        try:
            prompt = f"""
            Extract professional skills and competencies from this text:
            
            {text}
            
            Return only a JSON array of skills, focusing on:
            - Technical skills
            - Creative skills
            - Software proficiency
            - Industry expertise
            
            Example: ["Photography", "Adobe Photoshop", "Portrait Photography", "Digital Marketing"]
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                skills = json.loads(response.text)
                return skills if isinstance(skills, list) else []
            except:
                return [skill.strip() for skill in response.text.split(',') if skill.strip()]
        except Exception as e:
            logger.error(f"Skill extraction error: {e}")
            return []

# Data Sources
class InstagramScraper:
    async def scrape_profile(self, username: str) -> Dict[str, Any]:
        """Mock Instagram scraping (in real implementation, use Instagram Basic Display API)"""
        # Simulated Instagram data
        return {
            "name": f"@{username}",
            "bio": "Creative photographer capturing life's moments",
            "follower_count": 5420,
            "following_count": 1230,
            "post_count": 342,
            "profile_pic_url": "https://example.com/profile.jpg",
            "recent_posts": [
                {
                    "url": "https://example.com/post1.jpg",
                    "caption": "Golden hour magic ✨ #photography #goldenhour",
                    "likes": 234,
                    "type": "image"
                },
                {
                    "url": "https://example.com/post2.jpg", 
                    "caption": "Behind the scenes of today's shoot",
                    "likes": 156,
                    "type": "image"
                }
            ]
        }

class LinkedInScraper:
    async def scrape_profile(self, profile_url: str) -> Dict[str, Any]:
        """Mock LinkedIn scraping (in real implementation, use LinkedIn API)"""
        return {
            "name": "John Doe",
            "headline": "Creative Director & Photographer",
            "location": "New York, NY",
            "experience": [
                {
                    "title": "Senior Photographer",
                    "company": "Creative Studio Inc.",
                    "duration": "2021 - Present",
                    "description": "Lead photographer for commercial and portrait projects"
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Fine Arts",
                    "school": "Art Institute",
                    "year": "2020"
                }
            ],
            "skills": ["Photography", "Adobe Creative Suite", "Portrait Photography", "Commercial Photography"]
        }

class WebsiteScraper:
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """Basic website scraping for portfolio sites"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {
                            "title": self._extract_title(content),
                            "description": self._extract_description(content),
                            "images": self._extract_images(content, url),
                            "content": content[:1000]  
                        }
        except Exception as e:
            logger.error(f"Website scraping error: {e}")
        
        return {"error": "Failed to scrape website"}
    
    def _extract_title(self, html: str) -> str:
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        return match.group(1) if match else "Unknown"
    
    def _extract_description(self, html: str) -> str:
        match = re.search(r'<meta name="description" content="(.*?)"', html, re.IGNORECASE)
        return match.group(1) if match else ""
    
    def _extract_images(self, html: str, base_url: str) -> List[str]:
        images = re.findall(r'<img[^>]+src="([^"]+)"', html, re.IGNORECASE)
        base_domain = urlparse(base_url).netloc
        absolute_images = []
        for img in images[:10]:  
            if img.startswith('http'):
                absolute_images.append(img)
            elif img.startswith('/'):
                absolute_images.append(f"https://{base_domain}{img}")
        return absolute_images

# Main Profile Builder Service
class ProfileBuilderService:
    def __init__(self):
        self.ai_service = AIService()
        self.instagram_scraper = InstagramScraper()
        self.linkedin_scraper = LinkedInScraper()
        self.website_scraper = WebsiteScraper()
    
    async def build_profile(self, request: ProfileImportRequest) -> Dict[str, Any]:
        """Main method to build profile from multiple sources"""
        profile_data = {
            "user_id": request.user_id,
            "name": None,
            "bio": None,
            "email": None,
            "profession": None,
            "skills": [],
            "social_links": {},
            "portfolio_items": []
        }

        for source, source_type in zip(request.sources, request.source_types):
            try:
                if source_type == "instagram":
                    username = source.split('/')[-1] if '/' in source else source
                    data = await self.instagram_scraper.scrape_profile(username)
                    await self._process_instagram_data(profile_data, data, source)
                
                elif source_type == "linkedin":
                    data = await self.linkedin_scraper.scrape_profile(source)
                    await self._process_linkedin_data(profile_data, data)
                
                elif source_type == "website":
                    data = await self.website_scraper.scrape_website(source)
                    await self._process_website_data(profile_data, data, source)
                
                elif source_type == "resume":
                    # Handle resume files (PDF, DOC)
                    await self._process_resume_data(profile_data, source)
                
            except Exception as e:
                logger.error(f"Error processing {source_type} source: {e}")
        
        # AI Enhancement
        await self._enhance_with_ai(profile_data)
        
        # Save to database
        await self._save_profile(profile_data)
        
        return profile_data
    
    async def _process_instagram_data(self, profile_data: Dict, data: Dict, source: str):
        """Process Instagram data"""
        if not profile_data["name"]:
            profile_data["name"] = data.get("name", "").replace("@", "")
        
        profile_data["social_links"]["instagram"] = source

        bio_text = data.get("bio", "")
        captions = " ".join([post.get("caption", "") for post in data.get("recent_posts", [])])
        combined_text = f"{bio_text} {captions}"
        
        if combined_text:
            skills = await self.ai_service.extract_skills(combined_text)
            profile_data["skills"].extend(skills)
        
        # Add portfolio items from posts
        for post in data.get("recent_posts", []):
            portfolio_item = {
                "title": f"Instagram Post - {post.get('likes', 0)} likes",
                "description": post.get("caption", ""),
                "media_type": post.get("type", "image"),
                "media_url": post.get("url"),
                "tags": self._extract_hashtags(post.get("caption", "")),
                "source": "instagram"
            }
            profile_data["portfolio_items"].append(portfolio_item)
    
    async def _process_linkedin_data(self, profile_data: Dict, data: Dict):
        """Process LinkedIn data"""
        if not profile_data["name"]:
            profile_data["name"] = data.get("name")
        
        profile_data["profession"] = data.get("headline")
        profile_data["location"] = data.get("location")
        
        # Add LinkedIn skills
        linkedin_skills = data.get("skills", [])
        profile_data["skills"].extend(linkedin_skills)
        
        # Generate bio from experience
        experience_text = " ".join([
            f"{exp.get('title')} at {exp.get('company')}: {exp.get('description', '')}"
            for exp in data.get("experience", [])
        ])
        
        if experience_text:
            bio = await self.ai_service.generate_bio({
                "name": profile_data["name"],
                "profession": profile_data["profession"],
                "skills": profile_data["skills"],
                "portfolio_summary": experience_text
            })
            profile_data["bio"] = bio
    
    async def _process_website_data(self, profile_data: Dict, data: Dict, source: str):
        """Process website data"""
        if "error" not in data:
            profile_data["social_links"]["website"] = source
            
            content = data.get("content", "")
            if content:
                skills = await self.ai_service.extract_skills(content)
                profile_data["skills"].extend(skills)

            for img_url in data.get("images", []):
                portfolio_item = {
                    "title": "Website Image",
                    "description": data.get("description", ""),
                    "media_type": "image",
                    "media_url": img_url,
                    "tags": [],
                    "source": "website"
                }
                profile_data["portfolio_items"].append(portfolio_item)
    
    async def _process_resume_data(self, profile_data: Dict, file_path: str):
        """Process resume file (mock implementation)"""
        mock_resume_text = """
        John Doe - Creative Director & Photographer
        Email: john@example.com
        Phone: (555) 123-4567
        
        Experience:
        - Senior Photographer at Creative Studio (2021-Present)
        - Freelance Designer (2019-2021)
        
        Skills: Photography, Adobe Creative Suite, Video Editing, Brand Design
        """
        
        # Extract contact info
        email_match = re.search(r'Email:\s*([^\s\n]+)', mock_resume_text)
        if email_match:
            profile_data["email"] = email_match.group(1)
        
        phone_match = re.search(r'Phone:\s*([^\n]+)', mock_resume_text)
        if phone_match:
            profile_data["phone"] = phone_match.group(1).strip()
        
        # Extract skills
        skills = await self.ai_service.extract_skills(mock_resume_text)
        profile_data["skills"].extend(skills)
    
    async def _enhance_with_ai(self, profile_data: Dict):
        """Enhance profile with AI-generated content"""
        profile_data["skills"] = list(set(profile_data["skills"]))

        if not profile_data["bio"] and profile_data["skills"]:
            profile_data["bio"] = await self.ai_service.generate_bio(profile_data)

        for item in profile_data["portfolio_items"]:
            if item["media_type"] == "image" and item["media_url"]:
                try:
                    # Mock image analysis (in real implementation, download and analyze)
                    analysis = {
                        "content_type": "photography",
                        "subjects": ["portrait", "professional"],
                        "quality": "high",
                        "tags": ["professional", "portrait", "creative"],
                        "category": "photography"
                    }
                    item["ai_analysis"] = json.dumps(analysis)
                    item["tags"].extend(analysis["tags"])
                except Exception as e:
                    logger.error(f"Image analysis failed: {e}")
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#(\w+)', text)
    
    async def _save_profile(self, profile_data: Dict):
        """Save profile to database"""
        conn = sqlite3.connect('talent_profiles.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO profiles 
            (user_id, name, bio, email, phone, location, profession, skills, social_links, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile_data["user_id"],
            profile_data.get("name"),
            profile_data.get("bio"),
            profile_data.get("email"),
            profile_data.get("phone"),
            profile_data.get("location"),
            profile_data.get("profession"),
            json.dumps(profile_data.get("skills", [])),
            json.dumps(profile_data.get("social_links", {})),
            datetime.now().isoformat()
        ))
        
        profile_id = cursor.lastrowid
        
        # Save portfolio items
        for item in profile_data["portfolio_items"]:
            cursor.execute('''
                INSERT INTO portfolio_items 
                (profile_id, title, description, media_type, media_url, tags, ai_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile_id,
                item.get("title"),
                item.get("description"),
                item.get("media_type"),
                item.get("media_url"),
                json.dumps(item.get("tags", [])),
                item.get("ai_analysis")
            ))
        
        conn.commit()
        conn.close()

# Initialize service
profile_service = ProfileBuilderService()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Smart Talent Profile Builder API", "version": "1.0.0"}

@app.post("/import-profile", response_model=Dict[str, Any])
async def import_profile(request: ProfileImportRequest):
    """Import and build profile from external sources"""
    try:
        profile = await profile_service.build_profile(request)
        return {
            "success": True,
            "message": "Profile imported successfully",
            "data": profile
        }
    except Exception as e:
        logger.error(f"Profile import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get profile by user ID"""
    conn = sqlite3.connect('talent_profiles.db')
    cursor = conn.cursor()
    
    # Get profile
    cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
    profile_row = cursor.fetchone()
    
    if not profile_row:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get portfolio items
    cursor.execute('SELECT * FROM portfolio_items WHERE profile_id = ?', (profile_row[0],))
    portfolio_rows = cursor.fetchall()
    
    conn.close()
    
    # Format response
    profile = {
        "user_id": profile_row[1],
        "name": profile_row[2],
        "bio": profile_row[3],
        "email": profile_row[4],
        "phone": profile_row[5],
        "location": profile_row[6],
        "profession": profile_row[7],
        "skills": json.loads(profile_row[8] or "[]"),
        "social_links": json.loads(profile_row[9] or "{}"),
        "created_at": profile_row[10],
        "updated_at": profile_row[11],
        "portfolio_items": [
            {
                "id": row[0],
                "title": row[2],
                "description": row[3],
                "media_type": row[4],
                "media_url": row[5],
                "tags": json.loads(row[6] or "[]"),
                "ai_analysis": json.loads(row[7] or "{}") if row[7] else {},
                "created_at": row[8]
            }
            for row in portfolio_rows
        ]
    }
    
    return {"success": True, "data": profile}

@app.get("/profiles")
async def list_profiles():
    """List all profiles"""
    conn = sqlite3.connect('talent_profiles.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, name, profession, skills, created_at FROM profiles ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    profiles = [
        {
            "user_id": row[0],
            "name": row[1],
            "profession": row[2],
            "skills": json.loads(row[3] or "[]")[:5],  
            "created_at": row[4]
        }
        for row in rows
    ]
    
    return {"success": True, "data": profiles}

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image"""
    try:
        contents = await file.read()
        analysis = await profile_service.ai_service.analyze_image(contents)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)