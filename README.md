# 🍌 Banana Quest - A Nano Banana Driven Fantasy Adventure

An interactive fantasy adventure game powered by Google's Gemini 2.5 Flash Image model (aka "Nano Banana"). Upload your photo, transform into a fantasy hero, and embark on an AI-generated quest with dynamic scene illustrations and story progression.

## 🎮 What We Built

**Banana Quest** is a browser-based fantasy adventure game that showcases the power of Gemini's multimodal capabilities. The game features:

### Core Features
- **AI Character Transformation**: Upload any photo and watch it transform into an epic fantasy hero portrait
- **Dynamic Scene Generation**: Every story turn generates a unique fantasy scene illustration featuring your character
- **Interactive Storytelling**: AI-driven narrative that responds to your choices with 2-3 sentence turns
- **Immersive Experience**: Looping fantasy soundtrack, visual effects, and themed UI
- **Smart Session Management**: Maintains character consistency and story continuity throughout your adventure
- **Visual Feedback**: Selected choices highlight in gold, auto-scrolling to new content

### Technical Implementation
- **Single Model Architecture**: Uses Gemini 2.5 Flash Image (gemini-2.5-flash-image-preview) for both text and image generation
- **Two-Call Pattern**: Separates story generation from scene illustration for reliability
- **Character Consistency**: Maintains your character's appearance across all generated scenes using the original photo as reference
- **Optimized Prompting**: Carefully crafted prompts ensure short, punchy narration (2-3 sentences) with meaningful choices

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for Python environment management
- Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

1. **Clone the repository**
   ```bash
   cd banana-game
   ```

2. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Create and activate virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   uv pip install -e .
   ```

5. **Set up environment variables**
   
   The `.env` file already exists with the API key. If you need to update it:
   ```bash
   # Edit .env file
   GEMINI_API_KEY=your_api_key_here
   ```

## 🚀 Running the Game

### Starting the Backend Server

1. **Navigate to backend directory and run with uv**
   ```bash
   cd backend
   uv run python main.py
   ```
   The server will start on `http://localhost:8000`

   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

### Opening the Game

2. **Open the game in your browser**
   
   Simply open `frontend/index.html` in your web browser:
   - **Option 1**: Double-click `frontend/index.html` in your file explorer
   - **Option 2**: Open your browser and use `File > Open` to select the file
   - **Option 3**: Drag and drop `frontend/index.html` into your browser

## 🎯 How to Play

### Step 1: Create Your Character
1. Enter your character's name (e.g., "Aragorn", "Luna", "Shadowbane")
2. Upload a photo - this will be transformed into your fantasy hero
3. Click **"Generate Character"** to see your epic transformation
4. Review your hero portrait
5. Click **"Begin Your Quest"** to start the adventure

### Step 2: Gameplay
- **Opening Scene**: The game starts with a cover image and opening narration
- **Make Choices**: Select from 3-4 numbered options or type custom actions
- **Watch Scenes Unfold**: Each choice generates a new illustrated scene
- **Story Progress**: AI remembers your choices and maintains continuity

### Keyboard Shortcuts
- **1-4**: Quick select numbered options
- **Enter**: Send your typed action
- **Click anywhere**: Starts background music (first interaction)

### Game Features
- **Gold Highlighting**: Selected choices turn gold
- **Auto-Scroll**: Automatically scrolls to new content
- **Character Persistence**: Your hero appears in every scene
- **Short Narration**: 2-3 sentences per turn for quick pacing
- **Background Music**: Ambient soundtrack at 30% volume

## 📁 Project Structure

```
banana-game/
├── backend/
│   └── main.py              # FastAPI server with Gemini integration
├── frontend/
│   ├── index.html           # Complete game UI (HTML/CSS/JS)
│   ├── cover.png            # Welcome screen image
│   └── soundtrack.mp3       # Looping background music
├── .env                     # API key configuration
├── pyproject.toml           # Python dependencies (uv compatible)
├── nano-banana-docs.md      # Gemini image generation documentation
├── plan.md                  # Original project plan
├── CLAUDE.md               # Instructions for Claude Code
└── README.md               # This file
```

## 🛠️ Technical Stack

### Backend
- **Framework**: FastAPI with async/await support
- **AI SDK**: `google-genai` Python library
- **Model**: Gemini 2.5 Flash Image (`gemini-2.5-flash-image-preview`)
- **Session**: In-memory storage with turn tracking
- **Pattern**: Two-call approach (story + image generation)

### Frontend
- **Framework**: Pure vanilla HTML/CSS/JavaScript
- **Styling**: Custom CSS with fantasy theme
- **Fonts**: Spectral (body), Cinzel (headers)
- **Colors**: Gold (#caa954), Emerald (#2e8b57), Dark stone (#1a1a2e)
- **Audio**: HTML5 audio element with looping

### AI Architecture
- **Character Generation**: Transforms uploaded photo into fantasy hero
- **Story Generation**: Text-only generation with strict 2-3 sentence limit
- **Scene Generation**: Separate image call with character reference + context
- **Session Management**: Maintains conversation history (text only)

## 🐛 Troubleshooting

### Common Issues and Solutions

1. **"Failed to generate character"**
   - Verify your Gemini API key in `.env`
   - Check backend server is running (`uv run python main.py`)
   - Look for errors in terminal where backend is running

2. **No images after first turn**
   - Restart backend server
   - Check browser console (F12) for errors
   - Ensure API key has image generation permissions

3. **Music not playing**
   - Click or type anywhere to trigger audio
   - Check browser volume settings
   - Verify `soundtrack.mp3` exists in `frontend/`

4. **Connection refused errors**
   - Ensure backend is running on port 8000
   - Try `127.0.0.1:8000` instead of `localhost:8000`
   - Check if another service is using port 8000: `lsof -i :8000`

5. **CORS errors**
   - Backend has CORS enabled for all origins
   - If still having issues, try opening HTML via `http://` not `file://`

## 🔧 Development Tips

### Customization Options

- **Change narration length**: Edit `SYSTEM_PROMPT` in `backend/main.py`
- **Adjust music volume**: Change `audio.volume` value (0.0-1.0) in `frontend/index.html`
- **Modify visual theme**: Update CSS variables in `frontend/index.html`
- **Add new prompts**: Edit prompt constants in `backend/main.py`
- **Session timeout**: Add cleanup logic in `backend/main.py`

### Running in Development Mode

```bash
# Backend with auto-reload
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend with live server (optional)
cd frontend
python3 -m http.server 8080
```

## License

MIT