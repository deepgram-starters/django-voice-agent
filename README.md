# Django Voice Agent Starter

Get started using Deepgram's Voice Agent capabilities with this Python Django demo app. This application demonstrates how to integrate Deepgram's services to build a voice-controlled agent.

## What is Deepgram?
> Please leave this section unchanged.

[Deepgram's](https://deepgram.com/) voice AI platform provides APIs for speech-to-text, text-to-speech, and full speech-to-speech voice agents. Over 200,000+ developers use Deepgram to build voice AI products and features.

## Sign-up to Deepgram

> Please leave this section unchanged, unless providing a UTM on the URL.

Before you start, it's essential to generate a Deepgram API key to use in this project. [Sign-up now for Deepgram and create an API key](https://console.deepgram.com/signup?jump=keys).

## Prerequisites

- Python 3.8 or higher
- pip for package installation
- A [Deepgram API Key](https://console.deepgram.com/signup?jump=keys)

## Quickstart

Follow these steps to get started with this starter application.

### 1. Clone the repository

```bash
git clone https://github.com/deepgram-starters/django-voice-agent.git
cd django-voice-agent
```
(Assuming `django-voice-agent` is the correct repository name, please update if different)

### 2. Install dependencies

Install the project dependencies using pip:

```bash
pip install -r requirements.txt
```

### 3. Configure your environment

Copy the `sample.env` file to a new file named `.env`:

```bash
cp sample.env .env
```

Open the `.env` file and add your Deepgram API Key:

```
DEEPGRAM_API_KEY=YOUR_DEEPGRAM_API_KEY_HERE
# Add any other environment variables required by your Django application
```

### 4. Run the application

Start the Django development server:

```bash
python manage.py runserver 8080
```
Or, if you are using the `flask run` command from `deepgram.toml` (though this is a Django app):
```bash
flask run -p 8080
```
(Note: The `deepgram.toml` specifies `flask run -p 8080`. For a Django app, `python manage.py runserver 8080` is standard. Please clarify which is correct if needed.)

Once running, you can [access the application in your browser](http://localhost:8080/).

## Getting Help

We love to hear from you so if you have questions, comments or find a bug in the project, let us know! You can either:

- [Open an issue in this repository](https://github.com/deepgram-starters/django-voice-agent/issues/new) (Update `django-voice-agent` if your repository name is different)
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
