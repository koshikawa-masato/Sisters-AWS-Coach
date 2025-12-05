# Sisters AWS Coach

**3姉妹+おじさんと一緒にAWS資格を学ぼう！**
**Learn AWS Certification with 3 Sisters + Uncle!**

---

## 概要 / Overview

### 日本語

AWS SAA (Solutions Architect Associate) 資格試験の学習を、4人のユニークなAIキャラクターがサポートするインタラクティブ学習ツールです。

各キャラクターが自分らしいスタイルでAWSの概念を解説し、音声で聞くこともできます。日本語・英語のバイリンガル対応。

### English

An interactive AWS certification study tool featuring four unique AI characters who explain AWS concepts in their own style.

Each character provides explanations with their unique personality, with text-to-speech support. Fully bilingual (Japanese/English).

---

## キャラクター / Characters

| Character | Emoji | Style |
|-----------|-------|-------|
| **Botan** | 🌸 | カジュアルで楽しい解説 / Fun & casual explanations |
| **Kasho** | 🎵 | 正確でプロフェッショナル / Precise & professional |
| **Yuri** | 💻 | 技術的な深掘り / Technical deep dives |
| **Ojisan** | 👨 | 実務経験に基づくアドバイス / Real-world experience |

---

## 機能 / Features

### 日本語

- **オフラインモード**: 400問の事前作成問題（各キャラクター100問）
- **AI リアルタイム生成**: AWS Bedrockを使用した問題の動的生成
- **キャラクター別解説**: LLMによるキャラクターらしい解説
- **音声読み上げ (TTS)**: ElevenLabsによる高品質な音声
- **バイリンガル対応**: 日本語/英語の完全切り替え
- **タグフィルター**: 特定のAWSサービスに集中して学習

### English

- **Offline Mode**: 400 pre-generated questions (100 per character)
- **AI Real-time Generation**: Dynamic question generation using AWS Bedrock
- **Character Explanations**: LLM-powered explanations in each character's voice
- **Text-to-Speech (TTS)**: High-quality voice via ElevenLabs
- **Bilingual Support**: Full Japanese/English toggle
- **Tag Filtering**: Focus on specific AWS services

---

## 技術スタック / Tech Stack

| Component | Technology |
|-----------|------------|
| Web UI | Streamlit |
| LLM | AWS Bedrock (Claude) |
| TTS | ElevenLabs |
| RAG | Bedrock Knowledge Base (optional) |

---

## セットアップ / Setup

```bash
# 仮想環境を作成 / Create virtual environment
python -m venv venv
source venv/bin/activate

# 依存関係をインストール / Install dependencies
pip install -r requirements.txt

# 環境変数を設定 / Configure environment
cp .env.example .env
# .envを編集してAPIキーを設定 / Edit .env with your API keys

# 実行 / Run
streamlit run src/app.py
```

---

## 環境変数 / Environment Variables

```bash
# AWS Bedrock
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_KB_ID=your_knowledge_base_id  # Optional

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_MODEL=eleven_multilingual_v2
```

---

## 学習モード / Learning Modes

### オフラインモード / Offline Mode
- インターネット接続不要（TTS除く）
- 400問の事前作成問題
- 高速なレスポンス

### AI リアルタイム生成 / AI Real-time Generation
- AWS Bedrockを使用
- 無限の問題バリエーション
- Bedrock Knowledge Baseによる最新情報（オプション）

---

## ドメイン / Domain

- Production: https://aws.three-sisters.ai

---

## ライセンス / License

Private - All Rights Reserved

---

## 関連プロジェクト / Related Projects

- [AI-Vtuber-Project](https://github.com/koshikawa-masato/AI-Vtuber-Project) - LINE Bot
- [Sisters-On-WhatsApp](https://github.com/koshikawa-masato/Sisters-On-WhatsApp) - WhatsApp Bot
