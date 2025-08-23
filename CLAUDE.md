# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG SQL Query Notebook - A Jupyter-like notebook interface for executing natural language SQL queries against MSSQL databases using RAG (Retrieval-Augmented Generation).

## Architecture

### Backend (FastAPI + Python)
- **Framework**: FastAPI with async support
- **Database**: SQLite for connection storage, MSSQL for data queries
- **RAG**: LangChain + OpenAI for natural language to SQL conversion
- **Key Files**:
  - `backend/app/main.py`: FastAPI application entry point
  - `backend/app/routers/`: API endpoints (connections, queries)
  - `backend/app/services/`: Business logic (MSSQL, RAG services)
  - `backend/app/models.py`: SQLAlchemy models
  - `backend/app/schemas.py`: Pydantic schemas

### Frontend (Angular 19/20 + Tailwind)
- **Framework**: Angular 19/20 with standalone components
- **Styling**: Tailwind CSS
- **Key Components**:
  - `ConnectionManagerComponent`: Database connection management
  - `NotebookCellComponent`: Individual notebook cells (prompt/response)
- **Services**:
  - `ApiService`: HTTP communication with backend
  - `NotebookService`: Notebook state management

## Development Commands

### Backend
```bash
# Install dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with custom env file
cp .env.example .env  # Then edit .env
uvicorn app.main:app --reload
```

### Frontend
```bash
# Install dependencies
cd frontend/rag-sql-app
npm install

# Run development server
npm start  # or ng serve

# Build for production
npm run build  # or ng build --prod

# Run tests
npm test  # or ng test

# Lint
npm run lint  # or ng lint
```

### Quick Start Scripts
```bash
# Start backend (includes venv setup)
./start-backend.sh

# Start frontend
./start-frontend.sh
```

## Key Design Patterns

### Backend Patterns
1. **Async/Await**: All database operations use async SQLAlchemy
2. **Service Layer**: Business logic separated into services (MSSQLService, RAGService)
3. **Dependency Injection**: FastAPI's Depends for database sessions
4. **Schema Validation**: Pydantic models for request/response validation

### Frontend Patterns
1. **Standalone Components**: Angular 19/20 standalone component architecture
2. **Reactive Programming**: RxJS observables for state management
3. **Service-based State**: NotebookService manages notebook state
4. **Component Communication**: EventEmitters for parent-child communication

## API Endpoints

- `GET /api/connections`: List all connections
- `POST /api/connections`: Create new connection
- `PUT /api/connections/{id}`: Update connection
- `DELETE /api/connections/{id}`: Delete connection
- `POST /api/connections/{id}/test`: Test connection
- `POST /api/queries/execute`: Execute natural language query
- `GET /api/queries/history/{connection_id}`: Get query history

## Important Considerations

### Security
- Connection strings are stored in plain text in SQLite (should be encrypted in production)
- Add authentication/authorization for production deployment
- Validate and sanitize all SQL queries
- Use environment variables for sensitive configuration

### Performance
- Queries execute asynchronously to prevent blocking
- Results are paginated in frontend (100 rows initially)
- Large result sets can be exported to CSV

### Error Handling
- Backend returns structured error responses
- Frontend displays errors in notebook cells
- Connection testing before saving

### RAG Configuration
- OpenAI API key is optional (falls back to pattern matching)
- LangChain used for prompt engineering
- SQL generation optimized for MSSQL syntax

## Testing Approach

### Backend Testing
```python
# Test files should be in backend/tests/
# Run with: pytest
```

### Frontend Testing
```bash
# Test files are in *.spec.ts files
# Run with: npm test
```

## Deployment Notes

1. Set production environment variables
2. Use proper database encryption for connection strings
3. Configure CORS for production domain
4. Set up reverse proxy (nginx) for serving both frontend and backend
5. Use production builds (`ng build --prod`, `uvicorn` without --reload)
6. Implement rate limiting and authentication

## Common Tasks

### Adding a New API Endpoint
1. Create route in `backend/app/routers/`
2. Add schema in `backend/app/schemas.py`
3. Implement service logic in `backend/app/services/`
4. Update Angular service in `frontend/rag-sql-app/src/app/services/api.service.ts`

### Adding a New Component
1. Create component in `frontend/rag-sql-app/src/app/components/`
2. Ensure it's standalone with proper imports
3. Add to parent component's imports array

### Modifying Database Schema
1. Update models in `backend/app/models.py`
2. Database migrations are automatic on startup (development)
3. For production, use Alembic for migrations