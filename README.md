# HappyCow Scraper - Enhanced Version

An advanced web scraper for extracting restaurant data from HappyCow.net with AI-powered extraction, built for the Vegan Voyager project.

## 🚀 Features Implemented

### ✅ Configuration Management (T1)
- **Environment Variables**: Load configuration from `.env` file using `python-dotenv`
- **CLI Arguments**: Override config with command-line options
- **Flexible Settings**: Configure delays, workers, test mode, and more

### ✅ Resume Capability (T2)
- **Duplicate Detection**: Check Supabase before scraping to avoid re-processing
- **Smart Skipping**: Skip existing restaurants and track skipped count
- **Efficient Processing**: Reduces redundant work on subsequent runs

### ✅ Configurable Concurrency (T3)
- **Semaphore Control**: Limit concurrent workers with `asyncio.Semaphore`
- **Batch Processing**: Process restaurants in batches with delays
- **Rate Limiting**: Respect server limits with human-like delays

### ✅ Data Quality Audit (T4)
- **Field Completeness**: Analyze extraction success rates
- **Quality Reports**: Generate detailed audit reports with recommendations
- **Rich Output**: Beautiful console reports with color coding

### ✅ Test Suite (T5)
- **Pytest Integration**: Comprehensive test coverage
- **HTML Fixtures**: Test extraction with realistic HTML samples
- **Mock Testing**: Unit tests with mocked dependencies

### ✅ Pagination Support (T6)
- **Infinite Scroll**: Handle dynamic content loading
- **Load More Buttons**: Automatically click pagination controls
- **Multi-page Support**: Extract all restaurants from paginated listings

### ✅ Blocking Detection (T7)
- **CAPTCHA Detection**: Identify blocking attempts
- **Exponential Backoff**: Intelligent retry with increasing delays
- **Error Handling**: Graceful handling of rate limits and blocks

## 📁 Project Structure

```
hc-scraper/
├── config.py              # Configuration management
├── scraper.py             # Main scraper with enhancements
├── cli.py                 # Command-line interface
├── audit.py               # Data quality audit script
├── tests/
│   └── test_scraper.py    # Test suite
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── .env.example          # Environment variables template
```

## 🛠️ Setup & Installation

### 1. Environment Setup

```bash
# Clone or navigate to project directory
cd hc-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Configuration

Create a `.env` file with your settings:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# LLM Configuration
USE_LOCAL_LLM=true
OLLAMA_MODEL=llama2
OPENAI_API_KEY=your-openai-key-here

# Scraping Configuration
MAX_WORKERS=3
MIN_DELAY=2.0
MAX_DELAY=5.0
BATCH_DELAY=8.0
TEST_MODE=true
MAX_RESTAURANTS_PER_CITY=3

# Logging
LOG_LEVEL=INFO
```

### 3. Database Setup

Follow the instructions in `supabase_setup.md` to set up your Supabase database schema.

## 🚀 Usage

### Command Line Interface

```bash
# Basic usage (test mode with default cities)
python cli.py

# Scrape specific cities
python cli.py --cities "Austin,Portland,San Francisco"

# Full scrape with custom settings
python cli.py --no-test --workers 5 --max-restaurants 50

# List available cities
python cli.py --list-cities

# Custom logging
python cli.py --log-level DEBUG
```

### Available CLI Options

- `--cities`: Comma-separated list of cities to scrape
- `--workers`: Number of concurrent workers (default: 3)
- `--test`: Enable test mode (limit restaurants per city)
- `--no-test`: Disable test mode (scrape all restaurants)
- `--max-restaurants`: Maximum restaurants per city
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--list-cities`: Show available cities and exit

### Data Quality Audit

```bash
# Run audit on sample of restaurants
python audit.py

# The audit will:
# - Analyze field completeness rates
# - Identify data quality issues
# - Generate improvement recommendations
# - Save detailed report to JSON file
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scraper.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 📊 Monitoring & Maintenance

### Data Quality Monitoring

The audit script provides insights into:
- **Field Completeness**: Which fields are being extracted successfully
- **Extraction Accuracy**: Success rates for different data types
- **Quality Issues**: Missing critical fields, inconsistent data
- **Recommendations**: Specific improvements for better extraction

### Performance Monitoring

Monitor scraper performance through:
- **Logging**: Detailed logs with timing and success rates
- **Statistics**: Track scraped, saved, and skipped restaurant counts
- **Error Tracking**: Monitor blocking, timeouts, and extraction failures

### Maintenance Tasks

1. **Regular Audits**: Run `python audit.py` weekly to monitor data quality
2. **Configuration Tuning**: Adjust delays and workers based on performance
3. **Test Updates**: Update test fixtures when HappyCow changes layouts
4. **Database Cleanup**: Remove duplicates and outdated entries periodically

## 🔧 Configuration Options

### Scraping Behavior

- `MAX_WORKERS`: Concurrent processing limit (1-10 recommended)
- `MIN_DELAY`/`MAX_DELAY`: Request delay range in seconds
- `BATCH_DELAY`: Delay between batches of restaurants
- `TEST_MODE`: Limit restaurants per city for testing

### LLM Configuration

- `USE_LOCAL_LLM`: Use Ollama locally vs OpenAI API
- `OLLAMA_MODEL`: Local model name (llama2, mistral, etc.)
- `OPENAI_API_KEY`: API key for OpenAI GPT models

### Database Settings

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Anonymous key for database access

## 🛡️ Error Handling

The scraper includes robust error handling for:

- **Network Issues**: Automatic retries with exponential backoff
- **Blocking Detection**: CAPTCHA and rate limit detection
- **Database Errors**: Graceful handling of connection issues
- **Extraction Failures**: Fallback strategies for parsing errors

## 🤝 Contributing

When making changes:

1. **Update Tests**: Add tests for new functionality
2. **Run Audit**: Ensure data quality isn't degraded
3. **Update Documentation**: Keep README and docstrings current
4. **Test Configuration**: Verify all config options work correctly

## 📝 License

This project is for educational and personal use. Please respect HappyCow's terms of service and implement appropriate rate limiting.

---

**Note**: This is a personal-use tool. Always respect website terms of service and implement responsible scraping practices. 