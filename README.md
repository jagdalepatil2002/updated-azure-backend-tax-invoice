# Tax Analyzer Backend - Enhanced Version

A robust Flask-based REST API for analyzing IRS tax notices using AI-powered text extraction and analysis.

## 🚀 Features

### 🔍 Enhanced PDF Text Extraction
- **Multi-strategy extraction**: Standard text, layout-preserved, and OCR fallback
- **OCR support**: Handles scanned documents using Tesseract
- **Image enhancement**: Automatic image processing for better OCR accuracy
- **Intelligent validation**: Checks text quality and meaningfulness

### 🤖 AI-Powered Analysis
- **Gemini AI integration**: Advanced document analysis and structure extraction
- **Comprehensive data extraction**: Notice type, amounts, dates, contact info
- **Structured JSON output**: Consistent, parseable results
- **Error handling**: Robust retry logic and fallback responses

### 👥 User Management
- **User registration and authentication**: Secure password hashing
- **Analysis history**: Track previous document analyses
- **Data validation**: Input validation and sanitization

### 🏗️ Production Ready
- **Azure deployment optimized**: Pre-configured for Azure App Service
- **Database integration**: PostgreSQL with connection pooling
- **Logging and monitoring**: Comprehensive error tracking
- **Security**: CORS configuration and input validation

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL database
- Gemini API key
- Azure account (for deployment)

## 🛠️ Local Development

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/updated-azure-backend-tax-invoice.git
cd updated-azure-backend-tax-invoice
```

### 2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows - Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### 5. Configure environment variables
```bash
cp .env.template .env
# Edit .env with your actual values
```

### 6. Run the application
```bash
python app.py
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - User login

### Document Analysis
- `POST /summarize` - Analyze tax notice PDF

### User Management
- `GET /history/<user_id>` - Get user's analysis history

### Health Check
- `GET /` - Application health status

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `FLASK_ENV` | Flask environment | No |
| `SECRET_KEY` | Flask secret key | No |
| `PORT` | Application port | No |

## ☁️ Azure Deployment

### 1. Configure Azure App Service
- Set Python 3.9 runtime
- Configure startup command: `startup.sh`
- Set environment variables

### 2. Set Environment Variables in Azure
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
GEMINI_API_KEY=your_gemini_api_key
FLASK_ENV=production
```

### 3. Deploy using GitHub Actions
- Push to main branch
- GitHub Actions will automatically deploy

## 📊 Project Structure

```
updated-azure-backend-tax-invoice/
├── app.py                 # Main Flask application
├── pdf_extractor.py       # Enhanced PDF text extraction
├── gemini_api.py         # Gemini API integration
├── requirements.txt      # Python dependencies
├── startup.sh           # Azure startup script
├── web.config           # Azure web configuration
├── .env.template        # Environment variables template
├── .github/
│   └── workflows/
│       └── azure-deploy.yml  # GitHub Actions deployment
└── README.md            # Project documentation
```

## 🔍 PDF Processing Features

### Extraction Strategies
1. **Standard Text Extraction**: Fast extraction for text-based PDFs
2. **Layout-Preserved Extraction**: Maintains document structure
3. **OCR Fallback**: Handles scanned documents and images
4. **Enhanced OCR**: Image preprocessing for better accuracy

### Text Quality Validation
- Minimum length requirements
- Alphanumeric character ratio analysis
- Tax document keyword detection
- Meaningful content verification

## 🛡️ Security Features

- Password hashing using Werkzeug
- Input validation and sanitization
- CORS configuration for frontend integration
- SQL injection prevention with parameterized queries

## 📈 Performance Optimizations

- Database connection pooling
- Image enhancement for better OCR
- Efficient PDF processing
- Compressed API responses

## 📝 License

This project is licensed under the MIT License.
