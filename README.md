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

## なぜこのアプリを作ったか / Why We Built This

### 日本語

「AWSの資格勉強、正直つまらない...」

そう感じたことはありませんか？分厚い参考書、単調な問題集、一人で黙々と勉強する孤独感。私たちも同じでした。

だからこそ、**楽しく、飽きずに、続けられる**学習ツールを作りました。4人の個性豊かなAIキャラクターが、あなたの学習パートナーになります。正解しても不正解でも、キャラクターが励ましてくれる。音声で解説を聞けるから、通勤中でも学習できる。

**「勉強」を「会話」に変える。** それがSisters AWS Coachのコンセプトです。

### English

"Studying for AWS certification is honestly boring..."

Have you ever felt that way? Thick textbooks, monotonous practice tests, the loneliness of studying alone. We felt the same.

That's why we built a learning tool that's **fun, engaging, and sustainable**. Four unique AI characters become your learning partners. Whether you answer correctly or incorrectly, they encourage you. Listen to explanations via voice, so you can study even during your commute.

**Turn "studying" into "conversation."** That's the concept behind Sisters AWS Coach.

---

## 誰に向いているか / Who Is This For

### 日本語

- AWS SAA資格を目指しているが、勉強が続かない人
- 一人で勉強するのが苦手な人
- 参考書を読むより、対話形式で学びたい人
- 通勤時間や隙間時間を活用したい人
- 英語でも日本語でも学習したい人

### English

- Anyone preparing for AWS SAA who struggles to keep studying
- Those who find it hard to study alone
- People who prefer interactive learning over reading textbooks
- Those who want to utilize commute time or spare moments
- Anyone who wants to learn in both English and Japanese

---

## AWSで作る、AWSの学習ツール / Built on AWS, For AWS

### 日本語

このアプリは、**AWS自体を活用して構築**されています。AWSを学びながら、AWSの技術に触れる。それがこのプロジェクトの特徴です。

| 使用しているAWSサービス | 用途 |
|------------------------|------|
| **Amazon Bedrock** | Claude AIによる問題生成・解説 |
| **Bedrock Knowledge Base** | RAGによる最新AWS情報の取得 |

AWSの資格を取るなら、AWSで動くアプリで学ぶ。これ以上の説得力はありません。

### English

This app is **built using AWS itself**. Learn AWS while experiencing AWS technology firsthand. That's what makes this project unique.

| AWS Service Used | Purpose |
|-----------------|---------|
| **Amazon Bedrock** | Question generation & explanations via Claude AI |
| **Bedrock Knowledge Base** | RAG for up-to-date AWS information |

If you're getting AWS certified, learn with an app that runs on AWS. There's no better proof of concept.

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
