# Django Voice Agent Starter

Conversational voice agent powered by Deepgram with Django Channels.

## Features

- Real-time voice conversation via WebSocket
- Speech-to-text (STT) and text-to-speech (TTS) streaming
- Minimal Django setup with no database
- Django Channels for WebSocket support
- Simple metadata API endpoint

## Prerequisites

- Python 3.8+
- Deepgram API key ([get one here](https://console.deepgram.com/signup))

## Setup

1. Clone the repository:
```bash
git clone https://github.com/deepgram-starters/django-voice-agent.git
cd django-voice-agent
```

2. Initialize and update the frontend submodule:
```bash
git submodule init
git submodule update
```

3. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Create a `.env` file with your Deepgram API key:
```bash
cp .env.example .env
# Edit .env and add your DEEPGRAM_API_KEY
```

## Running the Application

Start the Django development server with Daphne (ASGI server):

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Or use the Django development server:

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## API Endpoints

### HTTP Endpoints

- `GET /api/metadata` - Get application metadata

### WebSocket Endpoints

- `ws://localhost:8000/agent/stream` - Voice agent stream
  1. Connect to WebSocket
  2. Send configuration as JSON: `{"stt_model": "nova-2", "tts_model": "aura-asteria-en", "language": "en"}`
  3. Send audio data as binary frames (user speech)
  4. Receive audio data as binary frames (agent speech)

## Project Structure

```
django-voice-agent/
├── config/              # Django configuration
│   ├── settings.py      # Minimal settings (no database)
│   ├── urls.py          # HTTP URL routing
│   ├── asgi.py          # ASGI config with Channels
│   └── wsgi.py          # WSGI config
├── starter/             # Main application
│   ├── views.py         # HTTP views
│   ├── urls.py          # HTTP URL patterns
│   ├── consumers.py     # WebSocket consumers
│   └── routing.py       # WebSocket URL patterns
├── frontend/            # Frontend (git submodule)
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── deepgram.toml        # Application metadata
```

## Learn More

- [Deepgram API Documentation](https://developers.deepgram.com/)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Django Documentation](https://docs.djangoproject.com/)

## License

MIT License - see LICENSE file for details
