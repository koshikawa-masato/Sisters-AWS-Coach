"""
AWS Bedrock LLM Provider for Sisters-AWS-Coach
Uses Claude via Bedrock Converse API for question generation
"""

import os
import json
import re
from typing import Optional, Dict, Any
import boto3
from dotenv import load_dotenv

load_dotenv()


class BedrockLLM:
    """AWS Bedrock LLM provider using Converse API"""

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        self.kb_id = os.getenv("BEDROCK_KB_ID")

        # Get AWS credentials from environment
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # Initialize Bedrock clients
        if aws_access_key and aws_secret_key:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            self.agent_client = boto3.client(
                "bedrock-agent-runtime",
                region_name=self.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            # Use default credential chain (IAM role, ~/.aws/credentials, etc.)
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region
            )
            self.agent_client = boto3.client(
                "bedrock-agent-runtime",
                region_name=self.region
            )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text response from Bedrock"""
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_prompt}]
                    }
                ],
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature
                }
            )

            # Extract text from response
            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])

            if content and len(content) > 0:
                return content[0].get("text", "")
            return ""

        except Exception as e:
            print(f"Bedrock API error: {e}")
            return f"Error: {str(e)}"

    def retrieve_from_kb(self, query: str, num_results: int = 3) -> str:
        """Retrieve relevant context from Knowledge Base"""
        if not self.kb_id:
            return ""

        try:
            response = self.agent_client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": num_results
                    }
                }
            )

            # Extract text from retrieval results
            contexts = []
            for result in response.get("retrievalResults", []):
                content = result.get("content", {}).get("text", "")
                if content:
                    contexts.append(content[:1000])  # Limit each context

            return "\n\n---\n\n".join(contexts)

        except Exception as e:
            print(f"Knowledge Base retrieval error: {e}")
            return ""

    def generate_question(
        self,
        character: str,
        prompt_content: str,
        focus_tags: Optional[list] = None,
        language: str = "ja"
    ) -> Optional[Dict[str, Any]]:
        """Generate a quiz question using character-specific prompt with RAG"""

        user_prompt_parts = []

        # Retrieve context from Knowledge Base if available
        if focus_tags and self.kb_id:
            query = f"What is AWS {' '.join(focus_tags)}?"
            context = self.retrieve_from_kb(query)
            if context:
                if language == "en":
                    user_prompt_parts.append(f"Use the following AWS documentation as reference:\n\n{context}\n")
                else:
                    user_prompt_parts.append(f"以下のAWS公式ドキュメントの情報を参考にして問題を作成してください:\n\n{context}\n")

        if focus_tags:
            if language == "en":
                user_prompt_parts.append(f"Focus on these topics: {', '.join(focus_tags)}")
            else:
                user_prompt_parts.append(f"特に以下のタグに関連する問題を出題してください: {', '.join(focus_tags)}")

        if language == "en":
            user_prompt_parts.append("Generate the question, options, and explanation in English.")
            user_prompt_parts.append("Output in JSON format.")
        else:
            user_prompt_parts.append("日本語で問題を生成してください。")
            user_prompt_parts.append("必ずJSON形式で出力してください。")

        user_prompt = "\n".join(user_prompt_parts)

        # For English mode, add instruction to output in English
        system_prompt = prompt_content
        if language == "en":
            system_prompt += "\n\nIMPORTANT: Generate all output (question, options, explanation) in English. The character's personality should still shine through, but the content must be in English."

        response = self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,
            temperature=0.8
        )

        # Parse JSON from response
        return self._parse_question_json(response)

    def _parse_question_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from response"""
        try:
            # Try to find JSON in markdown code block
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return None

            question_data = json.loads(json_str)

            # Validate required fields
            required_fields = ["question", "options", "correct", "tags", "explanation"]
            for field in required_fields:
                if field not in question_data:
                    print(f"Missing required field: {field}")
                    return None

            # Validate options structure
            if not isinstance(question_data["options"], dict):
                return None

            # Ensure correct answer is valid
            if question_data["correct"] not in question_data["options"]:
                return None

            return question_data

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response was: {response[:500]}...")
            return None
        except Exception as e:
            print(f"Error parsing question: {e}")
            return None

    def generate_explanation(
        self,
        character: str,
        prompt_content: str,
        question_text: str,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
        language: str = "ja"
    ) -> str:
        """Generate character-specific explanation for an answer"""

        if language == "en":
            user_prompt = f"""
The user answered an AWS quiz question.

Question: {question_text}
User's answer: {user_answer}
Correct answer: {correct_answer}
Was correct: {"Yes" if is_correct else "No"}

Generate a 2-3 sentence explanation in English, in the character's voice.
- If correct: Briefly praise and supplement why it's correct
- If incorrect: Kindly explain and describe why the correct answer is right
"""
        else:
            user_prompt = f"""
ユーザーがAWSの問題に回答しました。

問題: {question_text}
ユーザーの回答: {user_answer}
正解: {correct_answer}
正解したか: {"はい" if is_correct else "いいえ"}

日本語で、キャラクターらしい解説を2-3文で生成してください。
- 正解なら: 簡潔に褒めて、なぜ正解かを補足
- 不正解なら: 優しく説明して、正解の理由を説明
"""

        # For English mode, add instruction to output in English
        system_prompt = prompt_content
        if language == "en":
            system_prompt += "\n\nIMPORTANT: Generate all output in English. The character's personality should still shine through, but the content must be in English."

        return self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.7
        )
