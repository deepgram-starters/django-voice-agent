# Django Voice Agent Starter

Get started using Deepgram's Voice Agent capabilities with this Python Django demo app. This application demonstrates how to integrate Deepgram's services to build a voice-controlled agent.

## What is Deepgram?

[Deepgram's](https://deepgram.com/) voice AI platform provides APIs for speech-to-text, text-to-speech, and full speech-to-speech voice agents. Over 200,000+ developers use Deepgram to build voice AI products and features.

## Sign-up to Deepgram

Before you start, it's essential to generate a Deepgram API key to use in this project. [Sign-up now for Deepgram and create an API key](https://console.deepgram.com/signup?jump=keys).

## Prerequisites

- Python 3.8 or higher
- pip for package installation
- A [Deepgram API Key](https://console.deepgram.com/signup?jump=keys)

## Quickstart

Follow these steps to get started with this starter application.

### Clone the repository

1. Go to Github and [clone](https://github.com/deepgram-starters/django-voice-agent.git)

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your Deepgram API key:
```bash
export DEEPGRAM_API_KEY=your_api_key_here
```

## Running the Application

Start the application server:

```bash
python app.py
```

Then open your browser and go to:

```
http://localhost:3000
```

- Allow microphone access when prompted.
- Speak into your microphone to interact with the Deepgram Voice Agent.
- You should hear the agent's responses played back in your browser.

## Testing

Test the application with:

```bash
pytest -v test_app.py
```

## Getting Help

We love to hear from you so if you have questions, comments or find a bug in the project, let us know! You can either:

- [Open an issue in this repository](https://github.com/deepgram-starters/django-voice-agent/issues/new)
- [Join the Deepgram Github Discussions Community](https://github.com/orgs/deepgram/discussions)
- [Join the Deepgram Discord Community](https://discord.gg/deepgram)

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](./CONTRIBUTING.md) for more details on how to submit pull requests, report issues, and suggest enhancements.

## Code of Conduct

This project and everyone participating in it is governed by the [Deepgram Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Security

If you discover a security vulnerability, please follow our [Security Policy](./SECURITY.md) to report it. Please do not report security vulnerabilities on the public GitHub issue tracker.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Author

[Deepgram](https://deepgram.com)
