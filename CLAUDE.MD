# CLAUDE.MD - MoFA FM Project Guide

This file provides context for AI assistants (like Claude) working on the MoFA FM codebase.

## Project Overview

**MoFA FM** is a modern podcast hosting and distribution platform with AI-powered script generation, TTS synthesis, and full community interaction features.

- **Website**: https://mofa.fm
- **Architecture Version**: v2.0
- **Design Philosophy**: MoFA DataFlow + Django Business Logic + Vue User Interface

## Tech Stack

### Backend
- **Framework**: Django 5.1 + Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache/Queue**: Redis + Celery
- **AI Services**:
  - Moonshot AI (Kimi) for script generation
  - MiniMax for TTS synthesis
  - Tavily for AI-powered search
- **DataFlow Engine**: MoFA + Dora (Rust-based)

### Frontend
- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite
- **State Management**: Pinia
- **UI Components**: Element Plus
- **Key Libraries**: Axios, Vue Router

### Infrastructure
- **Task Queue**: Celery with Celery Beat
- **File Processing**: PyPDF2, python-docx for document parsing
- **Audio Processing**: FFmpeg, scipy, numpy

## Project Structure

```
mofa-fm/
├── backend/
│   ├── apps/
│   │   ├── users/          # User authentication and creator system
│   │   ├── podcasts/       # Podcast shows, episodes, scripts
│   │   ├── interactions/   # Comments, likes, follows, play history
│   │   ├── search/         # Full-text search functionality
│   │   └── core/           # Core utilities and base classes
│   ├── config/             # Django settings and URL configuration
│   ├── utils/              # Shared utilities
│   └── requirements/       # Python dependencies (dev.txt, prod.txt)
│
├── frontend/
│   ├── src/
│   │   ├── api/            # API client modules
│   │   ├── components/     # Reusable Vue components
│   │   │   ├── common/     # Common UI components
│   │   │   ├── creator/    # Creator-specific components
│   │   │   ├── player/     # Audio player components
│   │   │   └── podcast/    # Podcast display components
│   │   ├── views/          # Page components
│   │   │   ├── auth/       # Login, Register
│   │   │   └── creator/    # Creator dashboard, AI Studio
│   │   ├── stores/         # Pinia state stores
│   │   ├── router/         # Vue Router configuration
│   │   └── assets/         # Static assets
│   └── package.json
│
├── deploy/                 # Deployment scripts and configurations
├── media/                  # User-uploaded files (dev only)
│
└── Documentation files:
    ├── README.md           # User-facing documentation
    ├── architecture.md     # Detailed architecture diagrams
    ├── AGENTS.md           # AI agent documentation
    ├── FRONTEND_AI_USAGE_GUIDE.md
    └── MOFA_FLOW_MIGRATION.md
```

## Key Features & Models

### Core Django Apps

#### 1. **users** (`backend/apps/users/`)
- User authentication and profiles
- Creator verification system
- Fields: `username`, `email`, `is_creator`, `is_verified`, `avatar`

#### 2. **podcasts** (`backend/apps/podcasts/`)
- **Show**: Podcast series (has many Episodes)
- **Episode**: Individual podcast episodes
- **Category**: Content categorization
- **Tag**: Flexible tagging system
- **ScriptSession**: AI script creation sessions
- **UploadedReference**: Reference files (PDF, DOCX, TXT, MD)

Key models:
```python
# Show: title, slug, description, creator, category, content_type
# Episode: title, audio_file, duration, status, play_count
# ScriptSession: chat_history, current_script, voice_config
```

#### 3. **interactions** (`backend/apps/interactions/`)
- **Comment**: MPTT tree structure for threaded comments
- **Like**: Episode likes
- **Follow**: User follows Show
- **PlayHistory**: Playback progress tracking

#### 4. **search** (`backend/apps/search/`)
- Full-text search across shows and episodes
- Search history tracking

### Frontend Architecture

#### State Management (Pinia)
- `stores/auth.js` - User authentication state
- `stores/player.js` - Global audio player state
- `stores/podcasts.js` - Podcast data caching

#### Key Views
- **Creator Workspace**:
  - `views/creator/AIScriptStudio.vue` - AI-powered script creation
  - `views/creator/Dashboard.vue` - Creator analytics
  - `views/creator/ManageShow.vue` - Podcast management
- **Public Views**:
  - `views/Home.vue` - Homepage with recommendations
  - `views/Discover.vue` - Category browsing
  - `views/ShowDetail.vue` - Podcast show page
  - `views/EpisodeDetail.vue` - Episode player page

## MoFA DataFlow Integration

### AI Chat DataFlow (`openai_chat_dataflow.yml`)
- **terminal-input** (dynamic): Receives Django messages, returns LLM results
- **openai_chat_agent** (static): Calls Kimi AI API

### Podcast Generation DataFlow (`podcast_dataflow.yml`)
- **script-segmenter** (dynamic): Parses Markdown scripts, splits by character roles
- **minimax-{daniu,yifan,boyu}** (static): TTS engines with different voices
- **voice-output** (dynamic): Combines audio segments with smart silence insertion
- **viewer** (dynamic): Real-time logging and monitoring

### Key Flow Patterns
1. User creates script via AI chat → Django API → (Future: Dora openai_chat flow)
2. User generates podcast → Django API → (Future: Dora podcast_dataflow) → Audio file
3. Currently uses Django services: `script_ai.py`, `audio_processor.py` (marked for replacement)

## Development Guidelines

### When Working on Backend

1. **Follow Django Best Practices**:
   - Use Django ORM, avoid raw SQL unless necessary
   - Keep views thin, business logic in services
   - Use DRF serializers for API validation

2. **API Endpoints**:
   - All APIs under `/api/` namespace
   - Use ViewSets for CRUD operations
   - Check `backend/config/urls.py` for routing

3. **Database Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Environment Variables**:
   - Check `.env.example` for required variables
   - AI API keys: `OPENAI_API_KEY`, `MINIMAX_API_KEY`, `TAVILY_API_KEY`
   - Never commit `.env` file

5. **Celery Tasks**:
   - Long-running tasks should use Celery
   - Audio processing, AI generation are async

### When Working on Frontend

1. **Component Structure**:
   - Use Composition API (`<script setup>`)
   - Keep components focused and reusable
   - Follow Element Plus design patterns

2. **API Calls**:
   - Use centralized API modules in `src/api/`
   - Handle loading states and errors consistently

3. **State Management**:
   - Use Pinia for global state
   - Local state with `ref()` and `reactive()`

4. **Styling**:
   - Scoped styles in components
   - Use CSS variables for theming

5. **Build Commands**:
   ```bash
   npm run dev      # Development server
   npm run build    # Production build
   npm run preview  # Preview production build
   ```

### Code Quality

- **Python**: Follow PEP 8, use type hints where helpful
- **JavaScript**: Use ESLint configuration
- **Git**: Write clear commit messages, no force-push to main

## Common Tasks

### Add a New API Endpoint

1. Define model in `backend/apps/{app}/models.py`
2. Create serializer in `backend/apps/{app}/serializers.py`
3. Add ViewSet in `backend/apps/{app}/views.py` or `api.py`
4. Register route in `backend/apps/{app}/urls.py`
5. Update frontend API client in `frontend/src/api/{module}.js`

### Add a New Vue Component

1. Create component in appropriate directory
2. Import and register in parent component
3. Add to router if it's a page view
4. Update Pinia store if state management needed

### Debug AI Features

- Check `ScriptSession.chat_history` in Django admin
- Review `current_script` field for generated content
- Monitor MoFA dataflow logs via `viewer` node
- Check Celery worker logs for async tasks

### File Upload Flow

1. User uploads PDF/DOCX/TXT/MD → `POST /api/script-sessions/{id}/upload_file/`
2. Django saves to `media/` directory
3. `FileParser` service extracts text content
4. Creates `UploadedReference` record with `extracted_text`
5. Text used as context in next AI chat message

## Important Considerations

### Security
- User authentication required for creator features
- File upload validation (type, size limits)
- CSRF protection enabled in Django
- API rate limiting recommended for production

### Performance
- Redis caching for hot podcast data
- Database indexing on `created_at`, `status`, `slug` fields
- Audio files should be served via CDN in production
- Use pagination for list endpoints

### AI Service Limits
- **Kimi AI**: 8k token context window
- **MiniMax TTS**: Batch processing in 2s chunks
- Rate limits apply to external APIs

### Migration Notes
- Old services (`script_ai.py`, `audio_processor.py`) marked for replacement by MoFA
- See `MOFA_FLOW_MIGRATION.md` for integration roadmap
- Current status: Django handles AI calls directly, MoFA integration pending

## Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Useful Commands

### Development
```bash
# Backend
cd backend
python manage.py runserver
celery -A config worker -l info
celery -A config beat -l info

# Frontend
cd frontend
npm run dev
```

### Django Admin
- URL: http://localhost:8000/admin/
- Default credentials (dev): admin / mofamofa
- Manage users, shows, episodes, comments

### API Documentation
- Swagger: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## When You Need Help

1. **Architecture Questions**: Read `architecture.md` for detailed diagrams
2. **AI Integration**: Check `FRONTEND_AI_USAGE_GUIDE.md` and `AGENTS.md`
3. **Deployment**: See `README.md` deployment section
4. **MoFA DataFlow**: See `MOFA_FLOW_MIGRATION.md`

## Git Workflow

- **Main Branch**: Production-ready code
- **Feature Branches**: Use `claude/feature-name-{session-id}` pattern
- **Commits**: Clear, descriptive messages
- **Push**: Always to feature branch first, PR to main

---

**Last Updated**: 2025-12-04
**Maintained By**: MoFA FM Team
**Questions?**: contact@mofa.ai
