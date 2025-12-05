"""
Sisters-AWS-Coach - Learn AWS Certification with the Sisters!
Domain: aws.three-sisters.ai

v2: Supports both Offline (fixed questions) and Online (real-time generation) modes
"""

import streamlit as st
import os
import json
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv

# Localization
from src.locales import LANGUAGES, UI_TEXT

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Sisters AWS Coach",
    page_icon="☁️",
    layout="wide"
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = BASE_DIR / "questions"
PROMPTS_DIR = BASE_DIR / "prompts"

# Character configurations
CHARACTERS = {
    "Botan": {"emoji": "🌸", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_BOTAN", "emSmWzY0c0xtx5IFMCVv"), "difficulty": "beginner"},
    "Kasho": {"emoji": "🎵", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_KASHO", "XrExE9yKIg1WjnnlVkGX"), "difficulty": "intermediate"},
    "Yuri": {"emoji": "💻", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_YURI", "Pt5YrLNyu6d2s3s4CVMg"), "difficulty": "advanced"},
    "Ojisan": {"emoji": "👨", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_USER", "scOwDtmlUjD3prqpp97I"), "difficulty": "practical"},
}

# Mode descriptions
MODE_INFO = {
    "offline": {
        "ja": "固定問題（100問/キャラクター）",
        "en": "Fixed questions (100/character)"
    },
    "online": {
        "ja": "AIリアルタイム生成（無限）",
        "en": "AI real-time generation (unlimited)"
    }
}


# Initialize providers (cached for performance)
@st.cache_resource
def get_bedrock():
    from src.llm import BedrockLLM
    return BedrockLLM()


@st.cache_resource
def get_tts():
    from src.tts import ElevenLabsTTS
    return ElevenLabsTTS()


@st.cache_resource
def get_question_generator():
    from src.question_generator import QuestionGenerator
    return QuestionGenerator()


def load_questions(character: str = "Yuri"):
    """Load character-specific AWS questions from JSON file (offline mode)"""
    questions_file = QUESTIONS_DIR / f"{character.lower()}_questions.json"
    if questions_file.exists():
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("questions", [])

    fallback_file = QUESTIONS_DIR / "saa_questions.json"
    if fallback_file.exists():
        with open(fallback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("questions", [])
    return []


def get_character_prompt(character: str) -> str:
    """Load character-specific prompt from file"""
    prompt_file = PROMPTS_DIR / f"{character.lower()}_aws_prompt.txt"
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    default_prompts = {
        "Botan": "You are Botan, a cheerful coach. Explain AWS concepts with analogies.",
        "Kasho": "You are Kasho, a professional coach. Focus on costs and business.",
        "Yuri": "You are Yuri, a technical coach. Dive deep into technical details.",
        "Ojisan": "You are Ojisan, an experienced engineer. Share practical wisdom."
    }
    return default_prompts.get(character, default_prompts["Yuri"])


def generate_character_explanation(character: str, question: dict, user_answer: str, correct: bool, lang: str) -> str:
    """Generate character-specific explanation using LLM"""
    llm = get_bedrock()
    system_prompt = get_character_prompt(character)
    lang_name = "Japanese" if lang == "ja" else "English"

    # Handle both offline (dict with lang keys) and online (plain string) formats
    if isinstance(question.get("question"), dict):
        q_text = question["question"].get(lang, question["question"].get("en", ""))
        exp_text = question.get("explanation", {}).get(lang, question.get("explanation", {}).get("en", ""))
    else:
        q_text = question.get("question", "")
        exp_text = question.get("explanation", "")

    correct_answer = question.get("correct", "")

    user_prompt = f"""
The user answered a question about AWS.

Question: {q_text}
User's Answer: {user_answer}
Correct Answer: {correct_answer}
Was correct: {correct}

Base explanation: {exp_text}

Please provide an explanation in {lang_name} that:
1. If correct: Praise briefly and reinforce why this is right
2. If incorrect: Gently explain why the answer was wrong
3. Add your own insights about this AWS concept
4. Keep it concise (2-3 sentences max)

Respond in {lang_name} only.
"""

    response = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=300
    )
    return response


def reset_quiz_state():
    """Reset quiz state when character or mode changes"""
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.total_answered = 0
    st.session_state.answered = False
    st.session_state.selected_answer = None
    st.session_state.show_explanation = False
    st.session_state.character_explanation = None
    st.session_state.quiz_complete = False
    st.session_state.current_online_question = None
    st.session_state.answer_start_time = None


def get_user_id() -> str:
    """Get or create user ID for tracking progress"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
    return st.session_state.user_id


def get_option_text(option_value, lang: str) -> str:
    """Get option text for current language"""
    if isinstance(option_value, dict):
        return option_value.get(lang, option_value.get("en", str(option_value)))
    return str(option_value)


def record_answer_to_db(question: dict, is_correct: bool, answer_time: float = None):
    """Record answer to database for weakness analysis"""
    try:
        from src.database import record_answer
        user_id = get_user_id()
        character = st.session_state.current_character
        tags = question.get("tags", [question.get("category", "General")])
        if isinstance(tags, str):
            tags = [tags]

        # Get question text for hash
        q_text = question.get("question", "")
        if isinstance(q_text, dict):
            q_text = q_text.get("ja", q_text.get("en", ""))

        record_answer(
            user_id=user_id,
            character=character,
            tags=tags,
            is_correct=is_correct,
            question_text=q_text,
            answer_time_sec=answer_time,
            language=st.session_state.language,
            mode=st.session_state.quiz_mode
        )
    except Exception as e:
        print(f"Error recording answer: {e}")


def init_session_state():
    """Initialize session state"""
    defaults = {
        "current_question": 0,
        "score": 0,
        "total_answered": 0,
        "answered": False,
        "selected_answer": None,
        "show_explanation": False,
        "character_explanation": None,
        "quiz_complete": False,
        "current_character": "Yuri",
        "previous_character": "Yuri",
        "language": "ja",
        "questions": [],
        "quiz_mode": "offline",  # "offline" or "online"
        "current_online_question": None,
        "answer_start_time": None,
        "online_question_count": 10,  # Questions per online session
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load questions for offline mode
    if st.session_state.quiz_mode == "offline" and not st.session_state.questions:
        st.session_state.questions = load_questions(st.session_state.current_character)


def render_sidebar():
    """Render sidebar with settings"""
    t = UI_TEXT[st.session_state.language]
    lang = st.session_state.language

    with st.sidebar:
        st.title("☁️ AWS Coach")
        if lang == "en":
            st.caption("*Ace AWS with AI Family!*")
        else:
            st.caption("*AIファミリーと合格へ!*")

        # Language selection
        lang_options = list(LANGUAGES.keys())
        current_lang_name = [k for k, v in LANGUAGES.items() if v == st.session_state.language][0]
        selected_lang = st.selectbox(
            t["select_language"],
            lang_options,
            index=lang_options.index(current_lang_name)
        )
        if LANGUAGES[selected_lang] != st.session_state.language:
            st.session_state.language = LANGUAGES[selected_lang]
            st.rerun()

        st.divider()

        # Mode selection (v2 feature)
        st.subheader("Mode" if lang == "en" else "モード")
        mode_options = ["offline", "online"]
        mode_labels = [MODE_INFO[m][lang] for m in mode_options]
        current_mode_idx = mode_options.index(st.session_state.quiz_mode)

        selected_mode_label = st.radio(
            "Quiz Mode" if lang == "en" else "クイズモード",
            mode_labels,
            index=current_mode_idx,
            help="Offline: Fixed 100 questions per character\nOnline: AI generates new questions each time"
        )
        new_mode = mode_options[mode_labels.index(selected_mode_label)]
        if new_mode != st.session_state.quiz_mode:
            st.session_state.quiz_mode = new_mode
            reset_quiz_state()
            if new_mode == "offline":
                st.session_state.questions = load_questions(st.session_state.current_character)
            st.rerun()

        st.divider()

        # Character selection
        st.subheader(t["select_character"])
        for char_name, char_info in CHARACTERS.items():
            char_label = t["characters"][char_name]
            is_current = st.session_state.current_character == char_name
            button_type = "primary" if is_current else "secondary"
            if st.button(char_label, key=f"char_{char_name}", use_container_width=True, type=button_type):
                if st.session_state.current_character != char_name:
                    st.session_state.current_character = char_name
                    reset_quiz_state()
                    if st.session_state.quiz_mode == "offline":
                        st.session_state.questions = load_questions(char_name)
                    st.rerun()

        st.divider()

        # Score display
        if st.session_state.quiz_mode == "offline":
            total = len(st.session_state.questions)
        else:
            total = st.session_state.online_question_count

        st.metric(t["score"], f"{st.session_state.score}/{st.session_state.total_answered}")

        if st.session_state.total_answered > 0:
            accuracy = (st.session_state.score / st.session_state.total_answered) * 100
            st.progress(accuracy / 100, text=f"Accuracy: {accuracy:.0f}%")

        # Restart button
        if st.button(t["restart"], use_container_width=True):
            reset_quiz_state()
            if st.session_state.quiz_mode == "offline":
                st.session_state.questions = load_questions(st.session_state.current_character)
            st.rerun()

        # Stats button (v2 feature)
        st.divider()
        if st.button("My Stats" if lang == "en" else "学習統計", use_container_width=True):
            st.session_state.show_stats = True
            st.rerun()


def render_online_question():
    """Render question in online mode (real-time generation)"""
    t = UI_TEXT[st.session_state.language]
    lang = st.session_state.language
    char = st.session_state.current_character
    char_emoji = CHARACTERS[char]["emoji"]

    # Check if session complete
    if st.session_state.total_answered >= st.session_state.online_question_count:
        st.session_state.quiz_complete = True
        render_quiz_complete()
        return

    # Generate new question if needed
    if st.session_state.current_online_question is None and not st.session_state.answered:
        with st.spinner(f"{char_emoji} Generating question..." if lang == "en" else f"{char_emoji} 問題を生成中..."):
            try:
                generator = get_question_generator()
                user_id = get_user_id()

                question = generator.generate_question(
                    character=char,
                    user_id=user_id,
                    language=lang
                )

                if question:
                    st.session_state.current_online_question = question
                    st.session_state.answer_start_time = time.time()
                else:
                    st.error("Failed to generate question. Please try again.")
                    return
            except Exception as e:
                st.error(f"Error: {e}")
                return

    question = st.session_state.current_online_question
    if not question:
        return

    # Question header
    q_num = st.session_state.total_answered + 1
    st.header(f"{char_emoji} Question {q_num}/{st.session_state.online_question_count}")

    tags = question.get("tags", [])
    if tags:
        st.caption(f"Tags: {', '.join(tags)}")

    # Question text
    q_text = question.get("question", "")
    st.markdown(f"### {q_text}")

    # Options
    st.write("")
    options = question.get("options", {})
    for option_key, option_value in options.items():
        option_text = get_option_text(option_value, lang)
        is_selected = st.session_state.selected_answer == option_key

        if st.session_state.answered:
            correct = question.get("correct", "")
            if option_key == correct:
                st.success(f"**{option_key}.** {option_text}")
            elif is_selected and option_key != correct:
                st.error(f"**{option_key}.** {option_text}")
            else:
                st.write(f"**{option_key}.** {option_text}")
        else:
            button_type = "primary" if is_selected else "secondary"
            label = f"✓ **{option_key}.** {option_text}" if is_selected else f"**{option_key}.** {option_text}"
            if st.button(label, key=f"opt_{option_key}", use_container_width=True, type=button_type):
                st.session_state.selected_answer = option_key
                st.rerun()

    # Show selected answer
    if st.session_state.selected_answer and not st.session_state.answered:
        st.info(f"Selected: **{st.session_state.selected_answer}**" if lang == "en" else f"選択中: **{st.session_state.selected_answer}**")

    # Check answer button
    if not st.session_state.answered and st.session_state.selected_answer:
        if st.button(t["check_answer"], type="primary", use_container_width=True):
            correct = question.get("correct", "")
            is_correct = st.session_state.selected_answer == correct

            # Calculate answer time
            answer_time = None
            if st.session_state.answer_start_time:
                answer_time = time.time() - st.session_state.answer_start_time

            # Update score
            if is_correct:
                st.session_state.score += 1
            st.session_state.total_answered += 1
            st.session_state.answered = True

            # Record to database
            record_answer_to_db(question, is_correct, answer_time)

            st.rerun()

    # Show explanation after answering
    if st.session_state.answered:
        correct = question.get("correct", "")
        is_correct = st.session_state.selected_answer == correct

        if is_correct:
            st.success(f"### {t['correct']}")
        else:
            st.error(f"### {t['incorrect']}")
            st.write(f"{t['correct_answer']}: **{correct}**")

        # Base explanation
        exp_text = question.get("explanation", "")
        if exp_text:
            with st.expander(t["explanation"], expanded=True):
                st.write(exp_text)

        # Character explanation button
        if st.session_state.character_explanation:
            with st.expander(f"{char_emoji} {char} の解説" if lang == "ja" else f"{char_emoji} {char}'s Explanation", expanded=True):
                st.write(st.session_state.character_explanation)

            # TTS button
            if st.button(t["listen_explanation"], key="tts_btn"):
                try:
                    tts = get_tts()
                    voice_id = CHARACTERS[char]["voice_id"]

                    # Show progress bar during TTS generation
                    progress_text = "Generating audio..." if lang == "en" else "音声を生成中..."
                    progress_bar = st.progress(0, text=progress_text)
                    progress_bar.progress(20, text=progress_text)

                    audio_data = tts.generate_speech(
                        st.session_state.character_explanation,
                        voice_id=voice_id
                    )

                    progress_bar.progress(100, text="Done!" if lang == "en" else "完了！")

                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")

                    progress_bar.empty()
                except Exception as e:
                    st.warning(f"TTS error: {e}")
        else:
            if st.button(f"{char_emoji} {t['show_explanation']}", key="gen_exp"):
                with st.spinner("Generating explanation..."):
                    explanation = generate_character_explanation(
                        char,
                        question,
                        st.session_state.selected_answer,
                        is_correct,
                        lang
                    )
                    st.session_state.character_explanation = explanation
                    st.rerun()

        # Next question button
        st.write("")
        if st.button(t["next_question"], type="primary", use_container_width=True):
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.session_state.character_explanation = None
            st.session_state.current_online_question = None
            st.session_state.answer_start_time = None
            st.rerun()


def render_offline_question():
    """Render question in offline mode (fixed questions)"""
    t = UI_TEXT[st.session_state.language]
    lang = st.session_state.language

    questions = st.session_state.questions
    if not questions:
        st.error("No questions loaded!")
        return

    if st.session_state.quiz_complete:
        render_quiz_complete()
        return

    q_idx = st.session_state.current_question
    question = questions[q_idx]

    # Question header
    char = st.session_state.current_character
    char_emoji = CHARACTERS[char]["emoji"]
    st.header(f"{char_emoji} {t['question']} {q_idx + 1}/{len(questions)}")
    st.caption(f"Category: {question['category']}")

    # Question text
    q_text = question["question"].get(lang, question["question"]["en"])
    st.markdown(f"### {q_text}")

    # Options
    st.write("")
    for option_key, option_value in question["options"].items():
        option_text = get_option_text(option_value, lang)
        is_selected = st.session_state.selected_answer == option_key

        if st.session_state.answered:
            if option_key == question["correct"]:
                st.success(f"**{option_key}.** {option_text}")
            elif is_selected and option_key != question["correct"]:
                st.error(f"**{option_key}.** {option_text}")
            else:
                st.write(f"**{option_key}.** {option_text}")
        else:
            button_type = "primary" if is_selected else "secondary"
            label = f"✓ **{option_key}.** {option_text}" if is_selected else f"**{option_key}.** {option_text}"
            if st.button(label, key=f"opt_{option_key}", use_container_width=True, type=button_type):
                st.session_state.selected_answer = option_key
                st.rerun()

    # Show selected answer
    if st.session_state.selected_answer and not st.session_state.answered:
        st.info(f"Selected: **{st.session_state.selected_answer}**" if lang == "en" else f"選択中: **{st.session_state.selected_answer}**")

    # Check answer button
    if not st.session_state.answered and st.session_state.selected_answer:
        if st.button(t["check_answer"], type="primary", use_container_width=True):
            is_correct = st.session_state.selected_answer == question["correct"]
            if is_correct:
                st.session_state.score += 1
            st.session_state.total_answered += 1
            st.session_state.answered = True

            # Record to database
            record_answer_to_db(question, is_correct)

            st.rerun()

    # Show explanation after answering
    if st.session_state.answered:
        is_correct = st.session_state.selected_answer == question["correct"]

        if is_correct:
            st.success(f"### {t['correct']}")
        else:
            st.error(f"### {t['incorrect']}")
            st.write(f"{t['correct_answer']}: **{question['correct']}**")

        # Base explanation
        exp_text = question["explanation"].get(lang, question["explanation"]["en"])
        with st.expander(t["explanation"], expanded=True):
            st.write(exp_text)

        # Character explanation
        if st.session_state.character_explanation:
            char = st.session_state.current_character
            char_emoji = CHARACTERS[char]["emoji"]
            with st.expander(f"{char_emoji} {char} の解説" if lang == "ja" else f"{char_emoji} {char}'s Explanation", expanded=True):
                st.write(st.session_state.character_explanation)

            if st.button(t["listen_explanation"], key="tts_btn"):
                try:
                    tts = get_tts()
                    voice_id = CHARACTERS[char]["voice_id"]

                    # Show progress bar during TTS generation
                    progress_text = "Generating audio..." if lang == "en" else "音声を生成中..."
                    progress_bar = st.progress(0, text=progress_text)
                    progress_bar.progress(20, text=progress_text)

                    audio_data = tts.generate_speech(
                        st.session_state.character_explanation,
                        voice_id=voice_id
                    )

                    progress_bar.progress(100, text="Done!" if lang == "en" else "完了！")

                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")

                    progress_bar.empty()
                except Exception as e:
                    st.warning(f"TTS error: {e}")
        else:
            if st.button(f"{CHARACTERS[st.session_state.current_character]['emoji']} {t['show_explanation']}", key="gen_exp"):
                with st.spinner("Generating explanation..."):
                    explanation = generate_character_explanation(
                        st.session_state.current_character,
                        question,
                        st.session_state.selected_answer,
                        is_correct,
                        lang
                    )
                    st.session_state.character_explanation = explanation
                    st.rerun()

        # Next question button
        st.write("")
        if st.button(t["next_question"], type="primary", use_container_width=True):
            if q_idx + 1 >= len(questions):
                st.session_state.quiz_complete = True
            else:
                st.session_state.current_question += 1
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.session_state.show_explanation = False
            st.session_state.character_explanation = None
            st.rerun()


def render_quiz_complete():
    """Render quiz completion screen"""
    t = UI_TEXT[st.session_state.language]
    lang = st.session_state.language

    st.balloons()
    st.header(f"🎉 {t['quiz_complete']}")

    total = st.session_state.total_answered
    score = st.session_state.score
    percentage = (score / total * 100) if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t["score"], f"{score}/{total}")
    with col2:
        st.metric("Percentage", f"{percentage:.0f}%")
    with col3:
        if percentage >= 70:
            st.success("PASS!")
        else:
            st.warning("Keep studying!")

    # Show weakness analysis (v2 feature)
    try:
        from src.database import get_weaknesses, get_strengths
        user_id = get_user_id()

        st.divider()
        col_weak, col_strong = st.columns(2)

        with col_weak:
            st.subheader("Weak Areas" if lang == "en" else "苦手分野")
            weaknesses = get_weaknesses(user_id)
            if weaknesses:
                for w in weaknesses[:3]:
                    st.write(f"- **{w['tag']}**: {w['accuracy_rate']*100:.0f}% ({w['total_count']} questions)")
            else:
                st.write("No data yet" if lang == "en" else "データなし")

        with col_strong:
            st.subheader("Strong Areas" if lang == "en" else "得意分野")
            strengths = get_strengths(user_id)
            if strengths:
                for s in strengths[:3]:
                    st.write(f"- **{s['tag']}**: {s['accuracy_rate']*100:.0f}% ({s['total_count']} questions)")
            else:
                st.write("No data yet" if lang == "en" else "データなし")
    except Exception as e:
        pass  # Database not available

    st.divider()
    if st.button(t["restart"], type="primary", use_container_width=True):
        reset_quiz_state()
        if st.session_state.quiz_mode == "offline":
            st.session_state.questions = load_questions(st.session_state.current_character)
        st.rerun()


def render_stats():
    """Render user statistics page (v2 feature)"""
    t = UI_TEXT[st.session_state.language]
    lang = st.session_state.language

    st.header("Learning Statistics" if lang == "en" else "学習統計")

    if st.button("Back" if lang == "en" else "戻る"):
        st.session_state.show_stats = False
        st.rerun()

    try:
        from src.database import get_user_stats, get_answer_history
        user_id = get_user_id()
        stats = get_user_stats(user_id)

        # Overall stats
        st.subheader("Overall" if lang == "en" else "全体")
        overall = stats.get("overall", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions" if lang == "en" else "総問題数",
                     overall.get("total_questions", 0))
        with col2:
            st.metric("Correct" if lang == "en" else "正解数",
                     overall.get("correct_count", 0))
        with col3:
            accuracy = overall.get("overall_accuracy", 0) or 0
            st.metric("Accuracy" if lang == "en" else "正答率",
                     f"{accuracy*100:.1f}%")

        st.divider()

        # By character
        st.subheader("By Character" if lang == "en" else "キャラクター別")
        by_char = stats.get("by_character", {})
        if by_char:
            cols = st.columns(len(by_char))
            for i, (char, data) in enumerate(by_char.items()):
                with cols[i]:
                    emoji = CHARACTERS.get(char, {}).get("emoji", "")
                    st.write(f"**{emoji} {char}**")
                    st.write(f"Questions: {data.get('questions', 0)}")
                    acc = data.get('accuracy', 0) or 0
                    st.write(f"Accuracy: {acc*100:.0f}%")
        else:
            st.write("No data yet" if lang == "en" else "データなし")

        st.divider()

        # Weaknesses and Strengths
        col_weak, col_strong = st.columns(2)

        with col_weak:
            st.subheader("Weak Areas" if lang == "en" else "苦手分野")
            weaknesses = stats.get("weaknesses", [])
            if weaknesses:
                for w in weaknesses:
                    st.write(f"- **{w['tag']}**: {w['accuracy_rate']*100:.0f}% ({w['total_count']} Q)")
            else:
                st.write("No weak areas detected!" if lang == "en" else "苦手分野は検出されていません")

        with col_strong:
            st.subheader("Strong Areas" if lang == "en" else "得意分野")
            strengths = stats.get("strengths", [])
            if strengths:
                for s in strengths:
                    st.write(f"- **{s['tag']}**: {s['accuracy_rate']*100:.0f}% ({s['total_count']} Q)")
            else:
                st.write("Keep practicing!" if lang == "en" else "練習を続けましょう")

        st.divider()

        # Recent history
        st.subheader("Recent History" if lang == "en" else "最近の履歴")
        history = get_answer_history(user_id, limit=10)
        if history:
            for h in history:
                icon = "✅" if h['is_correct'] else "❌"
                tags = ", ".join(h['tags']) if h['tags'] else "N/A"
                st.write(f"{icon} [{h['character']}] {tags}")
        else:
            st.write("No history yet" if lang == "en" else "履歴なし")

    except Exception as e:
        st.error(f"Error loading stats: {e}")
        st.write("Database may not be initialized. Try answering some questions first.")


def main():
    """Main application"""
    init_session_state()
    render_sidebar()

    t = UI_TEXT[st.session_state.language]
    lang = st.session_state.language

    # Check if showing stats page
    if st.session_state.get("show_stats", False):
        render_stats()
        return

    # Main content
    st.title(t["app_title"])

    # Show mode indicator
    mode = st.session_state.quiz_mode
    mode_text = MODE_INFO[mode][lang]
    st.caption(f"{t['app_subtitle']} | Mode: {mode_text}")

    # Render appropriate question mode
    if mode == "online":
        render_online_question()
    else:
        render_offline_question()


if __name__ == "__main__":
    main()
