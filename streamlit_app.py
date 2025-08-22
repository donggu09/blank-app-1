import streamlit as st
import random
from streamlit_extras.let_it_rain import rain

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="⚾ 숫자 야구 게임 (Hard Mode)",
    page_icon="⚾",
    layout="centered"
)

# --- 게임 설정 ---
DIFFICULTY_LEVELS = {
    "Easy": {"digits": 3, "attempts": 10, "duplicates": False},
    "Normal": {"digits": 4, "attempts": 12, "duplicates": False},
    "Hard": {"digits": 4, "attempts": 10, "duplicates": True},
}

# --- 게임 핵심 로직 ---
def generate_secret_number(digits, allow_duplicates):
    """설정에 맞는 비밀 숫자를 생성합니다."""
    if allow_duplicates:
        # 중복 허용
        return [str(random.randint(0, 9)) for _ in range(digits)]
    else:
        # 중복 없음
        numbers = list('0123456789')
        random.shuffle(numbers)
        return numbers[:digits]

def check_guess(secret, guess):
    """중복 숫자를 고려하여 스트라이크와 볼을 정확히 계산합니다."""
    strikes = 0
    balls = 0
    secret_copy = list(secret)
    guess_copy = list(guess)
    
    # 스트라이크 먼저 계산
    for i in range(len(guess_copy)):
        if guess_copy[i] == secret_copy[i]:
            strikes += 1
            # 확인된 숫자는 None으로 바꿔 중복 계산 방지
            secret_copy[i] = None
            guess_copy[i] = None
            
    # 볼 계산
    for i in range(len(guess_copy)):
        if guess_copy[i] is not None and guess_copy[i] in secret_copy:
            balls += 1
            # 확인된 숫자는 찾아내서 None으로 바꿈
            secret_copy.remove(guess_copy[i])
            
    return strikes, balls

# --- 게임 상태 초기화 ---
def init_game(difficulty):
    """선택한 난이도로 새 게임을 시작합니다."""
    settings = DIFFICULTY_LEVELS[difficulty]
    st.session_state.difficulty = difficulty
    st.session_state.digits = settings["digits"]
    st.session_state.secret_number = generate_secret_number(settings["digits"], settings["duplicates"])
    st.session_state.history = []
    st.session_state.attempts_left = settings["attempts"]
    st.session_state.game_over = False
    st.session_state.user_input = ""

# --- 사이드바 UI ---
st.sidebar.title("⚙️ 게임 설정")
selected_difficulty = st.sidebar.selectbox(
    "난이도를 선택하세요:",
    options=list(DIFFICULTY_LEVELS.keys()),
    key="difficulty_selector"
)

with st.sidebar.expander("📖 게임 규칙 보기"):
    st.markdown("""
    1.  컴퓨터가 비밀 숫자를 정합니다.
        - **Easy**: 서로 다른 3자리 숫자
        - **Normal**: 서로 다른 4자리 숫자
        - **Hard**: **중복될 수 있는** 4자리 숫자
    2.  숫자를 추측하여 입력합니다.
    3.  컴퓨터가 힌트를 줍니다:
        - **S (스트라이크)**: 숫자와 위치 모두 정답
        - **B (볼)**: 숫자는 맞지만 위치가 틀림
        - **OUT**: 맞는 숫자가 하나도 없음
    4.  주어진 기회 안에 정답을 맞히면 승리!
    5.  **힌트 버튼**을 누르면 기회 1개를 소모하여 정답에 포함된 숫자 하나를 알 수 있습니다.
    """)

# --- 메인 UI 렌더링 ---
st.title("⚾ 숫자 야구 게임 (v2.0)")
st.markdown(f"현재 난이도: **{selected_difficulty}** | {DIFFICULTY_LEVELS[selected_difficulty]['digits']}자리 숫자")

# 게임 시작 버튼
if 'secret_number' not in st.session_state or st.session_state.difficulty != selected_difficulty:
    if st.button("새 게임 시작하기", type="primary", use_container_width=True):
        init_game(selected_difficulty)
        st.rerun()
else:
    # --- 게임 진행 중 UI ---
    
    # 입력 폼
    with st.form(key="guess_form"):
        user_guess = st.text_input(
            f"{st.session_state.digits}자리 숫자를 입력하세요:",
            max_chars=st.session_state.digits,
            key="user_input",
            placeholder="예: 123" if st.session_state.digits == 3 else "예: 1234"
        )
        submit_button = st.form_submit_button(label="✔️ 추측하기", use_container_width=True)

    # 입력 처리 로직
    if submit_button and not st.session_state.game_over:
        is_valid = True
        if len(user_guess) != st.session_state.digits or not user_guess.isdigit():
            st.warning(f"{st.session_state.digits}자리 숫자를 정확히 입력해주세요.")
            is_valid = False
        elif not DIFFICULTY_LEVELS[st.session_state.difficulty]["duplicates"] and len(set(user_guess)) != st.session_state.digits:
            st.warning("서로 다른 숫자를 입력해야 합니다.")
            is_valid = False
        
        if is_valid:
            st.session_state.attempts_left -= 1
            strikes, balls = check_guess(st.session_state.secret_number, list(user_guess))
            
            result_text = f"{strikes}S {balls}B" if strikes > 0 or balls > 0 else "OUT"
            
            st.session_state.history.append({"guess": user_guess, "result": result_text, "strikes": strikes})

            if strikes == st.session_state.digits or st.session_state.attempts_left == 0:
                st.session_state.game_over = True
            st.rerun()

    # --- 정보 표시 (남은 기회, 힌트 버튼) ---
    if not st.session_state.game_over:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="남은 기회", value=f"{st.session_state.attempts_left} 번")
        with col2:
            if st.button("💡 힌트 보기 (기회 -1)", use_container_width=True):
                if st.session_state.attempts_left > 1:
                    st.session_state.attempts_left -= 1
                    # 아직 플레이어가 맞히지 못한 숫자 중 하나를 힌트로 줌
                    revealed_numbers = {char for record in st.session_state.history for char in record['guess']}
                    unrevealed = [num for num in set(st.session_state.secret_number) if num not in revealed_numbers]
                    hint = random.choice(unrevealed) if unrevealed else random.choice(list(set(st.session_state.secret_number)))
                    st.info(f"💡 **힌트:** 정답에 숫자 **'{hint}'** 가 포함되어 있습니다.")
                else:
                    st.warning("기회가 부족하여 힌트를 사용할 수 없습니다.")

    # --- 추측 기록 ---
    if st.session_state.history:
        st.markdown("---")
        st.subheader("📖 나의 추측 기록")
        for record in reversed(st.session_state.history):
            if record['strikes'] == st.session_state.digits:
                st.success(f"**{record['guess']}** ➔ 🎉 **정답!**")
            elif "OUT" in record['result']:
                 st.error(f"**{record['guess']}** ➔ **{record['result']}**")
            else:
                st.info(f"**{record['guess']}** ➔ **{record['result']}**")
        st.markdown("---")

    # --- 게임 종료 화면 ---
    if st.session_state.game_over:
        secret_num_str = "".join(st.session_state.secret_number)
        if st.session_state.history and st.session_state.history[-1]['strikes'] == st.session_state.digits:
            st.success(f"### 🎉 **정답입니다!** 비밀 숫자는 **{secret_num_str}** 이었습니다!")
            st.balloons()
            rain(emoji="🎉", font_size=54, falling_speed=5, animation_length="5s")
        else:
            st.error(f"### 惜しい... 게임 오버!")
            st.error(f"정답은 **{secret_num_str}** 이었습니다.")

        if st.button("이 난이도로 다시하기", use_container_width=True):
            init_game(st.session_state.difficulty)
            st.rerun()