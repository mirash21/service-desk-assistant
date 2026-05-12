# Service Desk Assistant Bot

AI-powered service desk assistant bot with advanced RAG (Retrieval-Augmented Generation), analytics, and comprehensive admin panel.

## Features

- 🤖 **Multi-modal input**: Text, voice messages, and images
- 🧠 **Advanced RAG System**: Semantic search with context-aware responses using Supabase + pgvector
- 🎙️ **Voice Support**: Speech-to-text (STT) and text-to-speech (TTS) via Yandex SpeechKit with intelligent caching
- 📸 **Image Processing**: Automatic image analysis and description extraction
- 📚 **Smart Document Indexing**: Automatic indexing of .docx and .txt files with category support
- ❓ **Unanswered Questions Tracking**: Automatic logging for knowledge base improvement
- 💬 **Multiple Response Modes**: text, rag (with context), and voice modes
- 🔄 **Webhook Integration**: Real-time message processing via MAX Messenger API
- 👤 **User Preferences**: Personalized responses based on interaction history
- 📊 **Comprehensive Admin Panel**: Streamlit-based interface with full analytics
  - 📈 **Chat History**: Complete conversation tracking with context
  - 📉 **RAG Quality Analytics**: Automated evaluation of answer quality with metrics
  - 👥 **User Activities**: Real-time monitoring of user interactions and engagement
  - 📄 **Document Management**: Advanced document table with categories and filtering
  - 📊 **Analytics Dashboard**: Visual insights into system performance and usage
- ⚡ **Performance Optimization**: RAG query caching and optimized chunk lengths
- 🔍 **Context-Aware Responses**: Chat history integration for better conversation flow

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ MAX         │────▶│ Webhook      │────▶│ Message     │
│ Messenger   │     │ Server       │     │ Handler     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌───────────────────────────┼──────────────────┐
                    ▼                           ▼                  ▼
            ┌──────────────┐          ┌──────────────┐   ┌──────────────┐
            │ Yandex AI    │          │ Supabase     │   │ File         │
            │ (GPT/STT/TTS)│          │ (Vector DB)  │   │ Handler      │
            └──────────────┘          └──────────────┘   └──────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- MAX Bot Token
- Yandex Cloud API Key & Folder ID
- Supabase Project URL & Anon Key

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Fill in your credentials in `.env`:
```env
MAX_BOT_TOKEN=your_max_bot_token
YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_folder_id
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
WEBHOOK_URL=https://your-domain.com/webhook
```

### Running with Docker

```bash
# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f max-bot-webhook

# Stop
docker compose down
```

### Running Admin Panel

The admin panel provides comprehensive analytics and management:

```bash
# Install admin panel dependencies
cd admin_panel
pip install -r requirements.txt

# Start Streamlit admin panel
streamlit run app.py
```

Access the admin panel at `http://localhost:8501`

### Database Migrations

Apply necessary database migrations for new features:

```bash
# Apply chat history migration
python scripts/apply_chat_history_migration.py

# Apply RAG quality metrics migration
python scripts/apply_rag_quality_migration.py
```

### Manual Setup (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot
python main.py
```

## Usage

### Commands

- `/start` - Show welcome message
- `/mode [text|rag|voice]` - Switch response mode
- `/index` - Index documents from `data/` folder
- `/stats` - Show knowledge base statistics
- `/unanswered` - View unanswered questions log
- `/help` - Show help message

### Admin Panel

Access the admin panel at `http://localhost:8501` (or your configured port):

```bash
# Start admin panel
cd admin_panel && streamlit run app.py
```

**Admin Panel Features:**
- **📄 Documents Page**: Manage indexed documents with categories, view metadata, and re-index
- **📈 Analytics Page**: View system statistics, usage patterns, and performance metrics
- **👥 Activities Page**: Monitor real-time user activities, session tracking, and engagement metrics
- **🔍 RAG Quality Analytics**: Evaluate answer quality with automated testing and detailed reports

### Response Modes

- **text**: Simple text responses
- **rag**: Responses with context from indexed documents
- **voice**: Voice responses (text-to-speech)

### Adding Documents

1. Place `.docx` or `.txt` files in the `data/` directory
2. Send `/index` command to the bot
3. Documents will be chunked, embedded, and stored in Supabase

## Project Structure

```
service-desk-assistant/
├── handlers/                    # Message and command handlers
│   └── message_handler.py
├── services/                    # External API services
│   ├── yandex_service.py        # Yandex AI (GPT, STT, TTS)
│   ├── supabase_service.py      # Vector database operations
│   ├── voice_manager.py         # TTS caching and voice management
│   └── unanswered_logger.py     # Unanswered questions tracking
├── utils/                       # Utility functions
│   ├── logger.py                # Logging configuration
│   ├── file_handler.py          # File download and processing
│   ├── temp_manager.py          # Temporary file cleanup
│   ├── prompt_builder.py        # Dynamic prompt construction
│   ├── document_validator.py    # Document validation and categorization
│   └── rag_cache.py             # RAG query caching system
├── rag/                         # RAG system components
│   └── supabase_manager.py      # Document indexing, search, and chat history
├── admin_panel/                 # Streamlit admin interface
│   ├── app.py                   # Main admin panel application
│   ├── api/                     # API endpoints
│   │   └── rag_api.py           # RAG analytics API
│   ├── components/              # Reusable UI components
│   │   └── document_table.py    # Document management table
│   └── pages/                   # Admin panel pages
│       ├── 1_📄_Documents.py    # Document management
│       ├── 2_📈_Analytics.py    # System analytics
│       ├── 3_👥_Activities.py   # User activity monitoring
│       └── 4_🔍_RAG_Quality_Analytics.py  # RAG quality evaluation
├── data/                        # Data directory (mounted as volume)
│   ├── tts_cache/               # Cached TTS audio files
│   ├── unanswered_questions.json # Log of unanswered questions
│   ├── user_preferences.json    # User preference storage
│   ├── rag_analytics/           # RAG evaluation results
│   └── test_questions.json      # Test questions for RAG evaluation
├── migrations/                  # Database migrations
│   ├── 002_create_chat_history.sql
│   └── create_rag_quality_metrics_table.sql
├── scripts/                     # Utility and optimization scripts
│   ├── rag_quality_analytics.py # RAG quality evaluation script
│   ├── rag_analytics_api.py     # Analytics API server
│   ├── optimize_chunk_lengths.py # Chunk optimization utility
│   ├── add_categories_to_documents.py # Document categorization
│   └── apply_*_migration.py     # Migration application scripts
├── temp/                        # Temporary files (auto-cleaned)
├── config.py                    # Configuration constants
├── main.py                      # Application entry point
├── webhook_server.py            # Webhook HTTP server
├── manage_unanswered.py         # Tool for managing unanswered questions
├── test_rag.py                  # RAG system testing utility
└── docker-compose.yml           # Docker orchestration
```

## Monitoring

### Health Check

```bash
curl http://localhost:8081/health
```

Response:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "temp_directory_size_mb": 12.3,
  "timestamp": 1777316400.0
}
```

### Logs

```bash
# View logs
docker compose logs max-bot-webhook

# Follow logs
docker compose logs -f max-bot-webhook

# Filter errors
docker compose logs max-bot-webhook | grep ERROR
```

## Troubleshooting

### Voice Messages Not Working

1. Check ffmpeg is installed in container:
```bash
docker exec max-bot-webhook which ffmpeg
```

2. Verify Yandex API key has SpeechKit permissions

3. Check logs for STT errors:
```bash
docker compose logs max-bot-webhook | grep "STT"
```

4. Check TTS cache directory permissions:
```bash
ls -la data/tts_cache/
```

### Document Indexing Fails

1. Ensure documents are in `data/` directory
2. Check Supabase connection:
```bash
curl -H "apikey: YOUR_ANON_KEY" https://YOUR_PROJECT.supabase.co/rest/v1/documents?select=count
```

3. Verify vector extension is installed:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Image Processing Issues

1. Verify image files are properly attached in MAX Messenger
2. Check logs for image processing errors:
```bash
docker compose logs max-bot-webhook | grep "image"
```

3. Ensure Yandex Vision API is enabled in your Yandex Cloud account

### Unanswered Questions Not Logged

1. Check if `data/unanswered_questions.json` exists and is writable
2. Verify unanswered logger service is initialized:
```bash
docker compose logs max-bot-webhook | grep "unanswered"
```

3. Use `/unanswered` command to view logged questions

### Webhook Not Receiving Messages

1. Verify webhook URL is accessible from internet
2. Check MAX Bot webhook configuration
3. Test endpoint:
```bash
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### RAG Quality Issues

1. Run RAG quality analytics to identify problems:
```bash
python scripts/rag_quality_analytics.py
```

2. Check RAG cache status:
```bash
ls -la data/rag_analytics/
```

3. Optimize chunk lengths for better retrieval:
```bash
python scripts/optimize_chunk_lengths.py
```

4. Review quality metrics in admin panel under "RAG Quality Analytics"

### Admin Panel Not Working

1. Ensure Streamlit is installed:
```bash
pip install streamlit
```

2. Check if admin panel is running:
```bash
ps aux | grep streamlit
```

3. Verify admin panel dependencies:
```bash
cd admin_panel && pip install -r requirements.txt
```

4. Check admin panel logs for errors

### Chat History Not Tracking

1. Verify chat_history table exists in Supabase:
```sql
SELECT * FROM chat_history LIMIT 5;
```

2. Apply migration if needed:
```bash
python scripts/apply_chat_history_migration.py
```

3. Check message handler logs:
```bash
docker compose logs max-bot-webhook | grep "chat_history"
```

## Performance Tuning

### RAG Query Caching

Enable RAG caching to improve response times for repeated queries:
```python
# In utils/rag_cache.py
# Cache is automatically enabled
# Configure TTL in config.py
RAG_CACHE_TTL = 3600  # seconds
```

Check cache statistics:
```bash
python -c "from utils.rag_cache import rag_cache; print(rag_cache.get_stats())"
```

### Vector Search Optimization

Adjust IVFFlat index parameters in `rag/supabase_manager.py`:
```python
# Increase lists for better accuracy (slower search)
CREATE INDEX ... WITH (lists = 200);

# Decrease lists for faster search (lower accuracy)
CREATE INDEX ... WITH (lists = 50);
```

### Chunk Length Optimization

Optimize document chunk lengths for better retrieval:
```bash
# Run optimization script
python scripts/optimize_chunk_lengths.py

# Apply recommended settings
# Check results in admin panel -> RAG Quality Analytics
```

### Temporary File Cleanup

Modify cleanup intervals in `main.py`:
```python
# Clean every 30 minutes (default)
schedule_periodic_cleanup(interval_seconds=1800)

# Clean every hour
schedule_periodic_cleanup(interval_seconds=3600)
```

### Database Indexes

Ensure proper indexes are created:
```bash
# Apply chat history migration
python scripts/apply_chat_history_migration.py

# Apply RAG quality metrics migration
python scripts/apply_rag_quality_migration.py
```

## Security Notes

- ⚠️ Never commit `.env` file to version control
- 🔒 Use HTTPS for webhook endpoints in production
- 🛡️ Rotate API keys regularly
- 📝 Monitor access logs for suspicious activity

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

### Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Patent use
- ✅ Private use
- ❌ Liability
- ❌ Warranty
- ℹ️ License and copyright notice
- ℹ️ State changes

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
