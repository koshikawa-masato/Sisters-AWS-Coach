"""
Sisters-AWS-Coach - Learn AWS Certification with the Sisters!
Domain: aws.three-sisters.ai
"""

import streamlit as st
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Localization
from locales import LANGUAGES, UI_TEXT

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Sisters AWS Coach",
    page_icon="☁️",
    layout="wide"
)

# Paths
BASE_DIR = Path(__file__).parent.parent
QUESTIONS_DIR = BASE_DIR / "questions"
PROMPTS_DIR = BASE_DIR / "prompts"

# Character configurations
CHARACTERS = {
    "Botan": {"emoji": "🌸", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_BOTAN", "emSmWzY0c0xtx5IFMCVv")},
    "Kasho": {"emoji": "🎵", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_KASHO", "XrExE9yKIg1WjnnlVkGX")},
    "Yuri": {"emoji": "💻", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_YURI", "Pt5YrLNyu6d2s3s4CVMg")},
    "Ojisan": {"emoji": "👨", "voice_id": os.getenv("ELEVENLABS_VOICE_ID_USER", "scOwDtmlUjD3prqpp97I")},
}


# Initialize providers (cached for performance)
@st.cache_resource
def get_kimi():
    from llm import KimiLLM
    return KimiLLM()


@st.cache_resource
def get_tts():
    from tts import ElevenLabsTTS
    return ElevenLabsTTS()


def load_questions():
    """Load AWS questions from JSON file"""
    questions_file = QUESTIONS_DIR / "saa_questions.json"
    if questions_file.exists():
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("questions", [])
    return []


def get_character_prompt(character: str) -> str:
    """Load character-specific prompt from file"""
    prompt_file = PROMPTS_DIR / f"{character.lower()}_aws_prompt.txt"
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    # Default prompts if file doesn't exist
    default_prompts = {
        "Botan": "You are Botan, a cheerful and trendy language coach. Explain AWS concepts in a fun, casual way with modern slang. Keep it light and entertaining!",
        "Kasho": "You are Kasho, a professional and precise coach. Explain AWS concepts accurately and formally, focusing on exam-relevant details.",
        "Yuri": "You are Yuri, a tech-savvy analytical coach. Dive deep into technical details and explain the underlying mechanisms of AWS services.",
        "Ojisan": "You are Ojisan, a friendly American uncle with real-world IT experience. Explain AWS concepts using practical examples and dad jokes."
    }
    return default_prompts.get(character, default_prompts["Yuri"])


def generate_character_explanation(character: str, question: dict, user_answer: str, correct: bool, lang: str) -> str:
    """Generate character-specific explanation using LLM"""
    kimi = get_kimi()

    system_prompt = get_character_prompt(character)
    lang_name = "Japanese" if lang == "ja" else "English"

    q_text = question["question"].get(lang, question["question"]["en"])
    exp_text = question["explanation"].get(lang, question["explanation"]["en"])

    user_prompt = f"""
The user answered a question about AWS.

Question: {q_text}
User's Answer: {user_answer}
Correct Answer: {question['correct']}
Was correct: {correct}

Base explanation: {exp_text}

Please provide an explanation in {lang_name} that:
1. If correct: Praise briefly and reinforce why this is right
2. If incorrect: Gently explain why the answer was wrong
3. Add your own insights about this AWS concept
4. Keep it concise (2-3 sentences max)

Respond in {lang_name} only.
"""

    response = kimi.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=300
    )
    return response


def init_session_state():
    """Initialize session state"""
    defaults = {
        "current_question": 0,
        "score": 0,
        "answered": False,
        "selected_answer": None,
        "show_explanation": False,
        "character_explanation": None,
        "quiz_complete": False,
        "current_character": "Yuri",
        "language": "ja",
        "questions": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load questions if not loaded
    if not st.session_state.questions:
        st.session_state.questions = load_questions()


def render_sidebar():
    """Render sidebar with settings"""
    t = UI_TEXT[st.session_state.language]

    with st.sidebar:
        st.title("☁️ AWS Coach")

        # Language selection
        lang_options = list(LANGUAGES.keys())
        current_lang_name = [k for k, v in LANGUAGES.items() if v == st.session_state.language][0]
        selected_lang = st.selectbox(
            t["select_language"],
            lang_options,
            index=lang_options.index(current_lang_name)
        )
        st.session_state.language = LANGUAGES[selected_lang]

        st.divider()

        # Character selection
        st.subheader(t["select_character"])
        for char_name, char_info in CHARACTERS.items():
            char_label = t["characters"][char_name]
            if st.button(char_label, key=f"char_{char_name}", use_container_width=True):
                st.session_state.current_character = char_name
                st.session_state.character_explanation = None

        st.divider()

        # Score display
        st.metric(t["score"], f"{st.session_state.score}/{len(st.session_state.questions)}")

        # Restart button
        if st.button(t["restart"], use_container_width=True):
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.session_state.show_explanation = False
            st.session_state.character_explanation = None
            st.session_state.quiz_complete = False
            st.rerun()


def render_question():
    """Render current question"""
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
    for option_key, option_text in question["options"].items():
        is_selected = st.session_state.selected_answer == option_key

        # Show result colors after answering
        if st.session_state.answered:
            if option_key == question["correct"]:
                st.success(f"**{option_key}.** {option_text}")
            elif is_selected and option_key != question["correct"]:
                st.error(f"**{option_key}.** {option_text}")
            else:
                st.write(f"**{option_key}.** {option_text}")
        else:
            if st.button(f"**{option_key}.** {option_text}", key=f"opt_{option_key}", use_container_width=True):
                st.session_state.selected_answer = option_key
                st.rerun()

    # Check answer button
    if not st.session_state.answered and st.session_state.selected_answer:
        if st.button(t["check_answer"], type="primary", use_container_width=True):
            is_correct = st.session_state.selected_answer == question["correct"]
            if is_correct:
                st.session_state.score += 1
            st.session_state.answered = True
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
            st.info(f"{char_emoji} **{char}**: {st.session_state.character_explanation}")

            # TTS button
            if st.button(t["listen_explanation"], key="tts_btn"):
                try:
                    tts = get_tts()
                    voice_id = CHARACTERS[char]["voice_id"]
                    audio_data = tts.generate_speech(
                        st.session_state.character_explanation,
                        voice_id=voice_id
                    )
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                except Exception as e:
                    st.warning(f"TTS error: {e}")
        else:
            # Generate character explanation
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

    st.balloons()
    st.header(f"🎉 {t['quiz_complete']}")

    total = len(st.session_state.questions)
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

    if st.button(t["restart"], type="primary", use_container_width=True):
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.show_explanation = False
        st.session_state.character_explanation = None
        st.session_state.quiz_complete = False
        st.rerun()


def main():
    """Main application"""
    init_session_state()
    render_sidebar()

    t = UI_TEXT[st.session_state.language]

    # Main content
    st.title(t["app_title"])
    st.caption(t["app_subtitle"])

    render_question()


if __name__ == "__main__":
    main()
