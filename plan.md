# Fantasy Adventure (Single-Model: **Gemini-2.5-Flash-Image**)

## Objective

Ship a browser-playable **fantasy adventure** that runs entirely on **Gemini-2.5-Flash-Image**: the model returns the **story text** *and* **images**. The user uploads a face photo → we treat it as the canonical **character reference** and keep identity consistent across generated scene art. We reuse the same model for both JSON scene planning and image rendering (either in one call with interleaved parts, or in two calls for stricter control).

---

## Tech & Keys

* **Frontend:** Single `index.html` (HTML/CSS/JS; parchment-fantasy theme).
* **Backend:** Minimal HTTP server (FastAPI or Node).
* **SDK:** **Google Gen AI SDK** (`google-genai` / `@google/genai`). Reads API key from env. Use the **Developer API** (not Vertex) for speed today.
* **Model ID:** `gemini-2.5-flash-image-preview` (a.k.a. Nano Banana). Supports text→image, image+text→image, multi-image fusion, and interleaved text+image responses.

---

## UX (single game, single session)

1. **Landing / Upload**: Inputs → `Name`, `One-line pitch`, `Art style` (default: “watercolor, inked line, gilded fantasy, soft film grain”), **Photo (required)**.
2. **Character Build**: Generate a **stylized portrait** from the uploaded photo (text+photo → image). Extract 3–5 **visual anchors** (hair, clothing, colors, prop, vibe) to enforce identity in later prompts.
3. **First Scene**: Model returns **scene JSON** + **illustration**.
4. **Turn Loop**: User types free-form or taps an option → backend calls the model → UI appends **narration** and **new image**.
5. **Continuity**: On every turn, include the **original uploaded photo** (and optionally the **last frame**) as inline inputs to preserve identity and scene coherence.

---

## API (server)

### `POST /api/new-game`  (multipart/form-data)

Fields: `name`, `pitch`, `art_style?`, `premise?`, `photo` (required).
Response:

```json
{
  "session_id": "uuid",
  "character": { "name": "Aria", "bio": "…", "portrait_data_uri": "data:image/png;base64,..." },
  "scene": {
    "title": "Moonlit Gate",
    "narration": "…",
    "options": ["Knock softly","Examine sigils","Circle the wall"],
    "image_data_uri": "data:image/png;base64,..."
  }
}
```

### `POST /api/turn`  (application/json)

Body: `{"session_id":"uuid","user_input":"free text", "choice_idx":0}` (one of `user_input` or `choice_idx`).
Response: same `scene` shape as above.

---

## Session State (server)

```json
{
  "session_id": "uuid",
  "style": "watercolor, …",
  "character": {
    "name": "Aria",
    "bio": "…",
    "visual_anchors": ["silver circlet", "violet cape", "green eyes", "oak staff"],
    "photo_inline_b64": "<base64 bytes>"
  },
  "history": [
    { "narration": "…", "image_b64": "…", "choice": "Examine sigils" }
  ]
}
```

---

## Single-Model Calling Pattern (choose one)

### **A) One-call, interleaved output (fastest)**

* **Request:** `models.generate_content(model="gemini-2.5-flash-image-preview", contents=[ systemInstruction?, userTurn, inlineData(userPhoto), optional inlineData(lastImage) ])`.
* **Model Output:** Iterate `response.candidates[0].content.parts`: first **text** parts (narration or JSON), then **inline\_data** image bytes → save as `data:image/png;base64,…`.
* **Notes:** Lowest latency & simplest wiring. If you want strict JSON structure, *guide firmly in prompt*, then parse the first text part as JSON; remaining image part(s) are the illustration.

### **B) Two-call, structured control (recommended)**

* **Call 1 (Plan):** Ask for **strict JSON** scene object (title, narration, choices, `image_prompt`). Optionally use **response schema** to hard-enforce shape.
* **Call 2 (Image):** Send `image_prompt` + `inlineData(userPhoto)` (+ last frame if needed) to **render**.
* **Tradeoff:** Slightly higher latency but *deterministic parsing* and cleaner UI logic.

---

## System Instruction (seed once)

Use **system instructions** to pin persona, fantasy tone, and structured output contract across turns.

```
You are STORYDIRECTOR, a fantasy game master.
ALWAYS (1) produce a compact JSON "scene plan" and (2) one illustration.

JSON SCHEMA (no markdown):
{
  "scene_title": "string",
  "narration": "2-6 sentences, present tense, vivid but concise",
  "suggested_options": ["up to 4 short, mutually exclusive actions"],
  "image_prompt": "camera/lighting/composition/mood; END with: STYLE: <style tags>",
  "need_references": true_or_false,
  "reference_hints": ["main_character", "previous_scene"?]
}

Rules: maintain protagonist identity from VISUAL_ANCHORS; fantasy tone only; wide shots for vistas, close/medium for dialogue; keep options actionable and disjoint; never break character.
```

**Per turn user message template**

```
Context:
- CHARACTER_NAME: <name>
- CHARACTER_BIO: <bio>
- VISUAL_ANCHORS: <["…","…"]>
- STYLE_TAGS: <"watercolor, inked line, gilded fantasy, soft film grain">
- STORY_SO_FAR (last 3 narrations): <["…","…","…"]>
- PLAYER_INPUT: <free text or chosen option>

Task: Advance by one scene. Return ONLY the JSON scene plan. Then (same turn or next call) render the illustration.
```

---

## Image Generation Contract (same model)

* **Inputs:** `[ image_prompt_text, inlineData(userPhotoB64), optional inlineData(lastFrameB64) ]`.
* **Output Handling:** Extract `part.inline_data.data` → base64 → `data:image/png;base64,…`.
* **Continuity:** Always include the **original photo**; include **last frame** only when `need_references=true`. (The model supports multi-image fusion and targeted edits.)

---

## Frontend (HTML/CSS/JS)

* **Look:** Dark stone backdrop; parchment cards; serif narration (“Spectral”); emerald (`#2e8b57`) + gold (`#caa954`) accents; smallcaps headings; soft drop-shadows.
* **Layout:** Upload card → portrait banner → scene cards (image left, text right; stack on mobile), choice buttons, free-form textbox.
* **Behavior:**

  * On `/api/new-game`: show portrait + scene; render `options` as buttons; autofocus input.
  * On turn submit: disable controls, show inline spinner, append new scene, scroll to bottom.
  * Keybinds: `Enter` submits; `1–4` choose options.
  * Errors: banner with “Retry” (replay the same request payload).

---

## Acceptance Criteria

* **Gemini-only**: All narration and images come from **`gemini-2.5-flash-image-preview`**.
* **Identity consistency** across ≥5 turns using the uploaded photo as a persistent reference.
* **Valid scene JSON** each turn; ≤1.5× single-call latency target per step (model call(s) only).
* **Robust UX**: free-form and choice inputs both work; failures surface cleanly; UI stays responsive.

---

## Key references (for your agent)

* **Interleaved text+image responses + example code**: iterate `parts`, check for `inline_data`.
* **Image generation/editing prompt guide (Gemini)** and **model catalog**: use `generateContent` with image parts.
* **Model availability/IDs**: `gemini-2.5-flash-image-preview`.
* **Passing images:** Use **inlineData** for speed.
* **SDK quickstart & client config**: Developer API; `GEMINI_API_KEY` env.

---
