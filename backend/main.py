import os
import base64
import uuid
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from PIL import Image
from io import BytesIO
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=api_key)

# In-memory session storage
sessions: Dict[str, Dict] = {}

# System prompt for the fantasy game master
SYSTEM_PROMPT = """You are a fantasy game master running an epic adventure game.

CRITICAL RULES:
- Write EXACTLY 2-3 sentences of narration per turn. No more!
- Provide EXACTLY 3-4 numbered action choices
- Keep narration punchy and action-focused
- Each choice should be distinct and lead somewhere different

FORMAT:
[2-3 sentences describing what happens]

Choose your action:
1. [Short action]
2. [Different action]
3. [Another action]
4. [Optional fourth action]

Do NOT generate images. Keep responses SHORT."""

# Scene generation prompt
SCENE_GENERATION_PROMPT = """Create a detailed fantasy scene illustration based on this story moment:

{scene_context}

IMPORTANT:
- Show the character (from the provided photo) in this exact situation
- Epic fantasy watercolor art style with dramatic lighting
- Rich atmospheric details showing action, emotion, and environment
- The character's appearance must match the provided photo
- Make the scene dynamic and visually engaging"""

# Character generation prompt
CHARACTER_GENERATION_PROMPT = """Transform this person into an EPIC FANTASY HERO!

Create a stunning fantasy character portrait showing them as a legendary adventurer. 

IMPORTANT TRANSFORMATIONS:
- Add fantasy armor, robes, or adventuring gear appropriate for a hero
- Include magical elements: glowing eyes, mystical aura, or enchanted weapons
- Place them in a dramatic fantasy setting with atmospheric lighting
- Maintain their facial features and identity while making them look heroic
- Add fantasy accessories: cloaks, amulets, staffs, swords, or spell effects

Style: Detailed fantasy art, painted style, dramatic lighting, epic atmosphere
The person should look powerful, confident, and ready for adventure!"""

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    character_name: Optional[str] = None
    character_image: Optional[str] = None  # base64 encoded image

class ChatResponse(BaseModel):
    session_id: str
    image: Optional[str] = None  # base64 encoded
    text: str
    is_user: bool = False

class CharacterRequest(BaseModel):
    name: str
    image: str  # base64 encoded image

class CharacterResponse(BaseModel):
    portrait: str  # base64 encoded
    description: str

async def generate_scene_image(character_image_b64: str, scene_context: str) -> Optional[str]:
    """Generate a scene image based on the story context"""
    try:
        # Decode character image
        image_data = base64.b64decode(character_image_b64.split(",")[1] if "," in character_image_b64 else character_image_b64)
        
        # Prepare the prompt with scene context
        scene_prompt = SCENE_GENERATION_PROMPT.format(scene_context=scene_context)
        
        # Call Gemini to generate scene image
        contents = [
            {
                "parts": [
                    {"text": scene_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64.b64encode(image_data).decode()
                        }
                    }
                ]
            }
        ]
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=contents
        )
        
        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                if isinstance(part.inline_data.data, bytes):
                    image_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                else:
                    image_b64 = part.inline_data.data
                return f"data:image/png;base64,{image_b64}"
        
        return None
    except Exception as e:
        logger.error(f"Error generating scene image: {str(e)}")
        return None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = {
                "history": [],
                "character_name": None,
                "character_image": None,
                "turn_count": 0
            }
        
        session = sessions[session_id]
        
        # Update character info if provided
        if request.character_name:
            session["character_name"] = request.character_name
        if request.character_image:
            session["character_image"] = request.character_image
        
        # Prepare content for story generation
        contents = []
        
        # Add system prompt at the beginning of new sessions
        if len(session["history"]) == 0:
            contents.append({
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT}]
            })
        
        # Add conversation history (text only)
        for entry in session["history"]:
            contents.append(entry)
        
        # Add user message
        message_text = request.message
        if session["character_name"] and len(session["history"]) == 0:
            message_text = f"My character's name is {session['character_name']}. {message_text}"
        
        contents.append({
            "role": "user",
            "parts": [{"text": message_text}]
        })
        
        # Call Gemini API for story text
        logger.info(f"Generating story for session {session_id}")
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=contents
        )
        
        # Extract text response
        text_data = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_data += part.text
        
        # Generate scene image if not the first turn (first turn uses cover.png)
        image_data = None
        if session["turn_count"] > 0 and session["character_image"]:
            # Create scene context from user choice and AI response
            scene_context = f"Player action: {request.message}\n\nScene: {text_data[:500]}"
            logger.info(f"Generating scene image for turn {session['turn_count']}")
            image_data = await generate_scene_image(session["character_image"], scene_context)
        
        # Store in history (text only)
        session["history"].append({
            "role": "user",
            "parts": [{"text": message_text}]
        })
        
        session["history"].append({
            "role": "model",
            "parts": [{"text": text_data}]
        })
        
        # Increment turn count
        session["turn_count"] += 1
        
        # Limit history size to prevent token overflow
        if len(session["history"]) > 20:
            session["history"] = session["history"][:2] + session["history"][-18:]
        
        return ChatResponse(
            session_id=session_id,
            image=image_data,
            text=text_data
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-character", response_model=CharacterResponse)
async def generate_character(request: CharacterRequest):
    try:
        logger.info(f"Generating character portrait for {request.name}")
        
        # Decode the uploaded image
        image_data = base64.b64decode(request.image.split(",")[1] if "," in request.image else request.image)
        
        # Prepare the content for character generation
        contents = [
            {
                "parts": [
                    {"text": f"{CHARACTER_GENERATION_PROMPT}\n\nThis hero's name is {request.name}."},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64.b64encode(image_data).decode()
                        }
                    }
                ]
            }
        ]
        
        # Call Gemini to generate the character portrait
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=contents
        )
        
        # Parse response
        portrait_data = None
        description = f"{request.name}, a legendary hero ready for adventure!"
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Check if data is bytes or string
                if isinstance(part.inline_data.data, bytes):
                    # Encode bytes to base64 string
                    image_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                else:
                    # Already a string
                    image_b64 = part.inline_data.data
                portrait_data = f"data:image/png;base64,{image_b64}"
            elif hasattr(part, 'text') and part.text:
                description = part.text[:200]  # Keep description brief
        
        if not portrait_data:
            raise Exception("Failed to generate character portrait")
        
        return CharacterResponse(
            portrait=portrait_data,
            description=description
        )
        
    except Exception as e:
        logger.error(f"Error generating character: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)