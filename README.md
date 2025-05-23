# Seeklyzer: AI-Powered Job Search and Resume Assessment Platform

Seeklyzer is an innovative AI-powered job search platform that transforms traditional recruitment processes through advanced natural language processing, semantic search, and automated resume assessment technologies. The platform integrates multiple AI models to provide intelligent job matching and comprehensive compatibility analysis for job seekers.

## Features

### 🔍 **Intelligent Job Search**
- **Natural Language Queries**: Search using conversational language instead of rigid keywords
- **Semantic Search**: Context-aware job matching beyond simple keyword matching
- **Dual Search Interface**: Both traditional filtering and AI-powered semantic search options

### 📊 **AI-Powered Resume Assessment**
- **Three-Tier Evaluation**: Comprehensive assessment across responsibilities, qualifications, and skills
- **Compatibility Scoring**: Automated scoring system with detailed explanations
- **Batch Assessment**: Evaluate compatibility with multiple jobs simultaneously

### 🔧 **Data Processing Pipeline**
- **Automated Data Collection**: Real-time job data fetching from multiple sources
- **AI-Enhanced Analysis**: Structured job requirement extraction using xAI Grok-3-mini-beta
- **Vector Store Creation**: Semantic search infrastructure with OpenAI embeddings

### 💼 **Resume Management**
- **PDF Processing**: Upload and parse PDF resumes
- **Text Extraction**: Clean text extraction and formatting
- **Resume Optimization**: Intelligent formatting and structure enhancement

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript with responsive design
- **Backend**: Python with Flask/Dash framework
- **AI Models**: 
  - OpenAI GPT (Natural language processing and filter extraction)
  - xAI Grok-3-mini-beta (Job analysis and resume assessment)
  - OpenAI Embeddings (Semantic vector generation)
- **Vector Database**: ChromaDB for persistent semantic search
- **Data Processing**: Pandas, BeautifulSoup, concurrent processing

## Setup Instructions

### 1. Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/seeklyzer.git
cd seeklyzer
```

2. **Create a virtual environment:**
```bash
# Windows
python -m venv venv
./venv/Scripts/activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install required packages:**
```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory with the following variables:
```env
# AI Model Configuration
XAI_API_KEY=your_xai_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. Directory Structure

Ensure the following directory structure exists:
```
seeklyzer-dash-app/
├── __pycache__/                      # Python cache files
├── assets/
│   └── dashAgGridComponentFunctions.js
├── data/
│   ├── chroma_db/                    # Vector store persistence
│   ├── formatted_resumes_files/      # Processed resume files
│   └── preprocessed_seek_jobs_files/ # Processed job data
├── pages/
│   ├── __pycache__/                  # Page cache files
│   ├── jobs.py                       # Job finder page
│   ├── resume.py                     # Resume tool page
│   └── scripts.py                    # Scripts page
├── .env                             # Environment variables
├── .gitignore                       # Git ignore file
├── app.py                           # Main application
├── components.py                    # Dash components
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── script_create_vector_store.py    # Vector store creation
├── script_seek_jobs_assessment_json_extraction.py  # Job assessment extraction
└── script_seek_jobs_fetching_preprocessing.py      # Data fetching and preprocessing
```

### 4. Running the Application

1. **Ensure your virtual environment is activated**

2. **Start the application:**
```bash
python app.py
```

3. **Access the application:**
   - Open your web browser and navigate to `http://127.0.0.1:8050/scripts`
   - Alternative access points:
     - Scripts: `http://127.0.0.1:8050/scripts`
     - Resume Tool: `http://127.0.0.1:8050/resume`
     - Job Finder: `http://127.0.0.1:8050/jobs`

## Usage Guide

### Data Processing Scripts

1. **Access the Scripts interface** at `/scripts`
2. **Run the three-step pipeline** in sequence:
   - **Step 1**: Fetch and preprocess job data from external APIs
   - **Step 2**: Extract structured assessment details using AI analysis
   - **Step 3**: Create vector store for semantic search capabilities

### Job Search

1. **Navigate to Job Finder** at `/jobs`
2. **Use natural language search**: "Remote Python developer jobs posted last week"
3. **Try semantic search**: "Looking for challenging machine learning roles"
4. **Apply filters** using the traditional search interface
5. **View detailed job information** through modal interfaces

### Resume Assessment

1. **Upload your resume** using the Resume Tool at `/resume`
2. **Parse and format** your resume for optimal processing
3. **Navigate to Job Finder** and click "Assess Resume"
4. **Select jobs** for compatibility analysis
5. **Review detailed scores** across responsibilities, qualifications, and skills

## API Keys Setup

### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Add to `.env` file as `OPENAI_API_KEY`

### xAI API Key
1. Visit [xAI Platform](https://x.ai/)
2. Create an account and access the API section
3. Generate an API key for Grok models
4. Add to `.env` file as `XAI_API_KEY`

## Configuration

### Model Parameters

You can adjust AI model parameters in the respective script files:

**OpenAI GPT Configuration:**
- Temperature: 0.0 (for consistent extraction)
- Max tokens: 2048
- Model: Latest GPT model available

**xAI Grok Configuration:**
- Model: "grok-3-mini-beta"
- Temperature: 0.0 (for analytical tasks)
- Max tokens: 4096

**Vector Store Settings:**
- Embedding model: text-embedding-ada-002
- Similarity search: k=10 results
- Distance metric: Cosine similarity

## Troubleshooting

### Common Issues

**1. API Key Errors:**
- Verify API keys are correctly set in `.env` file
- Check API key permissions and quotas
- Ensure keys are for the correct services

**2. Data Processing Failures:**
- Check internet connectivity for API data fetching
- Verify sufficient disk space for data storage
- Monitor API rate limits and adjust concurrent processing

**3. Vector Store Issues:**
- Ensure ChromaDB dependencies are properly installed
- Check file permissions for data directory
- Verify successful completion of previous pipeline steps

**4. Application Startup Problems:**
- Confirm virtual environment is activated
- Check all required packages are installed
- Verify port 8050 is not in use by other applications

## Acknowledgments

- **OpenAI** for GPT models and embedding services
- **xAI** for Grok language model capabilities
- **ChromaDB** for vector database infrastructure
- **LangChain** for AI model integration frameworks

---

**Note**: This application requires active API keys for OpenAI and xAI services. Costs may be incurred based on usage. Please monitor your API usage and set appropriate limits.
