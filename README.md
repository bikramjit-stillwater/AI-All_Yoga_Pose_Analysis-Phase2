# 🪷 Stillwater Pose Hub

A single, production-ready landing page that unifies all of Stillwater Yoga's
AI pose-detection modules. Each underlying module lives in its own repository
and deploys independently — this hub only routes traffic and provides a
consistent, branded experience.

**Stack:** FastAPI · Jinja2 · vanilla CSS · deploys on Render in < 5 minutes.

---

## 🌿 Why a hub instead of a monolith?

Your three pose detectors (`Static-Tadasana`, `RealTime-Tadasana`,
`Static-Child-Pose`) are already live and working on Render. Merging them
into one repo would mean:

- ❌ Heavy single-deploy (MediaPipe + OpenCV + Gemini all loaded at boot)
- ❌ One bug in module A breaks modules B and C
- ❌ Every change re-deploys everything
- ❌ Hard to scale individual modules

This hub keeps each detector independent. The hub itself is **dependency-light**
(just FastAPI), so it boots in seconds and almost never goes down.

```
                        ┌─────────────────────────────┐
   stillwater.yoga ───▶ │  Stillwater Pose Hub        │
                        │  (this repo — light + fast) │
                        └────────────┬────────────────┘
                                     │ routes/embeds
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
       ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
       │ Static       │    │ RealTime     │    │ Static       │
       │ Tadasana     │    │ Tadasana     │    │ Child Pose   │
       └──────────────┘    └──────────────┘    └──────────────┘
       (independent Render services — each in its own repo)
```

---

## 📁 Project Structure

```
stillwater-pose-hub/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app: 6 routes total
│   └── modules.json         # ⭐ The only file you edit to add modules
├── templates/
│   ├── base.html
│   ├── index.html           # Landing page (cards)
│   └── launch.html          # Iframe wrapper for embedded module view
├── static/
│   ├── css/styles.css       # All styling
│   └── img/favicon.svg
├── requirements.txt
├── render.yaml              # Render auto-deploy config
├── Dockerfile               # Optional alternate deploy path
├── .python-version
├── .gitignore
└── README.md
```

---

## 🚀 Local Development

```bash
# 1. Create a virtual environment
python3.11 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate     # Windows

# 2. Install deps
pip install -r requirements.txt

# 3. Run
python -m app.main
# or
uvicorn app.main:app --reload

# 4. Open
# http://localhost:8000
```

The dev server hot-reloads on code changes. `modules.json` is re-read on every
request in dev mode, so you see new cards instantly.

---

## ➕ Adding a New Pose Module (the whole point)

This is the workflow you'll use forever. **No code changes — only config.**

1. **Deploy the new pose-detection app** to Render in its own repo (just like
   your existing three). Note its public URL, e.g.
   `https://your-new-pose.onrender.com`.

2. **Edit `app/modules.json`** — append a new object to the `modules` array:

   ```json
   {
     "id": "vrksasana-static",
     "name": "Vṛkṣāsana — Video Analysis",
     "sanskrit": "वृक्षासन",
     "english_name": "Tree Pose",
     "category": "Static Analysis",
     "description": "Upload a video of your Tree Pose and receive balance & alignment feedback.",
     "features": [
       "Standing-leg stability score",
       "Hip openness check",
       "AI coaching from Gemini 2.5 Flash"
     ],
     "url": "https://your-new-pose.onrender.com",
     "icon": "lotus",
     "color": "sage",
     "status": "live",
     "input_mode": "Upload Video"
   }
   ```

3. **Field reference:**

   | Field         | Required | Notes                                                          |
   | ------------- | -------- | -------------------------------------------------------------- |
   | `id`          | ✅        | URL slug. Lowercase, hyphens only. Must be unique.             |
   | `name`        | ✅        | Card title                                                     |
   | `sanskrit`    | ✅        | Devanagari script                                              |
   | `english_name`| ✅        | English translation                                            |
   | `category`    | ✅        | Free text (e.g. "Static Analysis", "Real-Time Analysis")       |
   | `description` | ✅        | 1–3 sentence card body                                         |
   | `features`    | ✅        | Array of 2–4 bullet strings                                    |
   | `url`         | ✅        | Public URL of the underlying detector app                      |
   | `icon`        | ✅        | `mountain` · `camera` · `lotus` (or add a new one in `index.html`) |
   | `color`       | ✅        | `sage` · `ochre` · `river`                                     |
   | `status`      | ✅        | `live` or `coming` (badge color changes)                       |
   | `input_mode`  | ✅        | Short label like "Upload Video" or "Webcam"                    |

4. **Commit & push.** Render auto-deploys. The new card appears live.

```bash
git add app/modules.json
git commit -m "Add Vrksasana pose module"
git push
```

That's the full process. Existing modules are untouched.

---

## 🌐 Embedding into Your Main Website

You have three options for hooking this hub up to `stillwater.yoga`:

### Option A — Simple link (recommended for navigation)
Just link from your nav: `<a href="https://hub.stillwater.yoga/">Pose Analysis</a>`.
Clean, fast, opens the full hub.

### Option B — Full-bleed iframe (recommended for embedded UX)
On a dedicated page like `stillwater.yoga/practice/`, embed:

```html
<iframe
  src="https://hub.stillwater.yoga/"
  style="width:100%; height:100vh; border:none;"
  allow="camera; microphone; autoplay; fullscreen"
  title="Stillwater Pose Analysis">
</iframe>
```

### Option C — Direct module deep-links
Skip the hub landing and link straight to a module:
`https://hub.stillwater.yoga/launch/tadasana-static`

Either way, **your main website never has to redeploy** when you add a new
pose. Zero risk.

---

## 📦 Deploy to Render (full walkthrough)

### Step 1 — Push to GitHub

```bash
cd stillwater-pose-hub
git init
git add .
git commit -m "Initial commit — Stillwater Pose Hub"
git branch -M main
git remote add origin https://github.com/<you>/stillwater-pose-hub.git
git push -u origin main
```

### Step 2 — Create the Render service

1. Go to <https://dashboard.render.com>
2. Click **New +** → **Web Service**
3. Connect your GitHub repo (`stillwater-pose-hub`)
4. Render reads `render.yaml` and pre-fills everything:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - Plan: Free (upgradable later)
5. Click **Create Web Service**.

### Step 3 — Wait ~2 minutes

First build takes about 90–120 seconds. You'll get a URL like
`https://stillwater-pose-hub.onrender.com`.

### Step 4 — (Optional) Add a custom domain

In the Render dashboard → **Settings → Custom Domains**, add e.g.
`hub.stillwater.yoga`. Update your DNS (a `CNAME` to the Render URL). HTTPS is
automatic.

### Step 5 — Verify

- `https://hub.stillwater.yoga/` → landing page with all 3 cards
- `https://hub.stillwater.yoga/healthz` → `{"status":"ok"}`
- `https://hub.stillwater.yoga/api/modules` → JSON of all modules

---

## 🔌 API Endpoints

| Method | Path                    | Purpose                                                    |
| ------ | ----------------------- | ---------------------------------------------------------- |
| GET    | `/`                     | Landing page                                               |
| GET    | `/launch/{module_id}`   | Embedded iframe view (keeps user inside the hub shell)     |
| GET    | `/go/{module_id}`       | 302 redirect to the underlying app (same tab)              |
| GET    | `/api/modules`          | JSON list of all modules — useful for external integrations |
| GET    | `/healthz`              | Health check                                               |
| GET    | `/api/docs`             | FastAPI auto-generated Swagger UI                          |

---

## 🪶 Notes on the Render Free Tier

- Free services sleep after 15 minutes of inactivity. The hub itself wakes in
  ~2s (it's tiny). Your detector apps may take 30–60s to wake.
- The `launch.html` page shows a "Waking the practice space…" loader to handle
  this gracefully.
- For production, the **Starter plan ($7/mo)** keeps the hub always-on.

---

## 🎨 Customization

| Want to change…      | Edit…                                            |
| -------------------- | ------------------------------------------------ |
| Colors / fonts       | CSS variables at top of `static/css/styles.css`  |
| Hero copy            | `app/modules.json` → `site` object               |
| Page sections        | `templates/index.html`                           |
| Add a new icon       | Add an `{% elif m.icon == "newname" %}` block in `index.html` |
| Brand mark           | Replace SVG in `templates/index.html` topbar     |
| Favicon              | `static/img/favicon.svg`                         |

---

## 📜 License

Internal Stillwater Yoga project. All rights reserved.
