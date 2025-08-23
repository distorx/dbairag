# RAG SQL Query Notebook

A Jupyter-like notebook interface for executing natural language SQL queries against MSSQL databases using RAG (Retrieval-Augmented Generation).

## Features

- 🤖 **Natural Language to SQL**: Convert natural language queries to SQL using OpenAI GPT
- 📓 **Jupyter-like Interface**: Interactive notebook with cells for queries and responses
- 🗄️ **Connection Management**: Store and manage multiple MSSQL database connections
- 📊 **Dynamic Output**: Automatically detect and display results as text or tables
- 💾 **CSV Export**: Export table results to CSV files
- 🔒 **Secure Storage**: Connection strings stored in local SQLite database
- ⚡ **Fast Execution**: Asynchronous query execution with FastAPI backend

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with async support
- **PyMSSQL**: MSSQL database driver
- **LangChain + OpenAI**: RAG implementation for SQL generation
- **SQLite**: Local storage for connection strings

### Frontend
- **Angular 19/20**: Latest Angular framework
- **Tailwind CSS**: Utility-first CSS framework
- **TypeScript**: Type-safe development
- **RxJS**: Reactive programming

## Prerequisites

- Python 3.8+
- Node.js 18+
- npm 9+
- MSSQL Server (for database connections)
- OpenAI API key (optional, for enhanced SQL generation)

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd dbairag
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key (optional)
# OPENAI_API_KEY=your-key-here
```

### 3. Frontend Setup

```bash
cd frontend/rag-sql-app

# Install dependencies
npm install
```

## Running the Application

### Option 1: Using provided scripts

```bash
# Terminal 1 - Start Backend
./start-backend.sh

# Terminal 2 - Start Frontend
./start-frontend.sh
```

### Option 2: Manual start

#### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend/rag-sql-app
npm start
```

## Usage

1. **Open the application**: Navigate to http://localhost:4200

2. **Add a database connection**:
   - Click "Add New Connection"
   - Enter connection details:
     - Name: Friendly name for the connection
     - Connection String: MSSQL connection string
   - Test the connection
   - Save if successful

3. **Execute queries**:
   - Select a database connection
   - Add a new cell
   - Type your query in natural language (e.g., "Show all tables", "Count records in users table")
   - Press Run or Shift+Enter to execute
   - Results will appear below the query

4. **Export results**:
   - For table results, click "Export CSV" to download the data

## Connection String Format

```
Server=localhost;Database=mydb;User Id=username;Password=password;
```

For Windows Authentication:
```
Server=localhost;Database=mydb;Trusted_Connection=True;
```

## API Documentation

- FastAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
dbairag/
├── backend/
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── models.py      # Database models
│   │   ├── schemas.py     # Pydantic schemas
│   │   └── main.py        # FastAPI app
│   └── requirements.txt
├── frontend/
│   └── rag-sql-app/
│       ├── src/
│       │   └── app/
│       │       ├── components/    # Angular components
│       │       ├── services/      # Angular services
│       │       └── app.ts         # Main app component
│       └── package.json
└── README.md
```

## Environment Variables

### Backend (.env)
- `OPENAI_API_KEY`: OpenAI API key for enhanced SQL generation
- `DATABASE_URL`: SQLite database URL for connection storage
- `FRONTEND_URL`: Frontend URL for CORS configuration

## Security Notes

- Connection strings are stored in plain text in SQLite (encrypt in production)
- Use environment variables for sensitive configuration
- Implement proper authentication for production use
- Restrict database permissions for connection users

## Troubleshooting

### Backend Issues
- Ensure Python 3.8+ is installed
- Check that all dependencies are installed
- Verify MSSQL drivers are installed (pyodbc or pymssql)
- Check .env file configuration

### Frontend Issues
- Ensure Node.js 18+ is installed
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### Connection Issues
- Verify MSSQL server is running and accessible
- Check firewall settings
- Ensure connection string format is correct
- Test with SQL Server Management Studio first

## License

MIT