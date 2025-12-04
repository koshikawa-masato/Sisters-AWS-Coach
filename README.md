# Sisters AWS Coach

Learn AWS Certification with the Sisters!

## Overview

An interactive AWS certification study tool featuring four unique AI characters who explain AWS concepts in their own style.

## Characters

- 🌸 **Botan** - Fun & casual explanations
- 🎵 **Kasho** - Precise & professional
- 💻 **Yuri** - Technical deep dives
- 👨 **Ojisan** - Real-world experience

## Features

- AWS SAA (Solutions Architect Associate) quiz questions
- Character-based explanations via LLM
- Text-to-Speech for listening practice
- Bilingual support (Japanese / English)

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
cd src
streamlit run app.py
```

## Domain

- Production: https://aws.three-sisters.ai

## Tech Stack

- Streamlit (Web UI)
- Kimi LLM (Explanations)
- ElevenLabs (TTS)
