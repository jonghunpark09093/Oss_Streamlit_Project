import base64
import json
import streamlit as st
from pathlib import Path

STUDENT_ID   = "2021204039"
STUDENT_NAME = "박종훈"

# ─────────────────────────────────────────────
#  사용자 계정 (아이디: 비밀번호)
# ─────────────────────────────────────────────
USERS = {
    "admin": "Nfl2025!",
    "nfl":   "GoChiefs#7",
}

# ─────────────────────────────────────────────
#  캐싱 - 파일 I/O를 최초 1회만 수행
#  Streamlit은 사용자 인터랙션마다 전체 스크립트를 재실행하므로
#  @st.cache_data 없이는 매 렌더링마다 파일을 반복 읽게 됨
# ─────────────────────────────────────────────
@st.cache_data
def load_image_base64(filename: str) -> str:
    path = Path(__file__).parent / "images" / filename
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_data
def load_questions() -> list:
    path = Path(__file__).parent / "data" / "questions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_teams() -> dict:
    path = Path(__file__).parent / "data" / "teams.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
#  세션 상태 초기화
# ─────────────────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,
        "username":  "",
        "page":      "login",   # login | intro | quiz | result
        "current_q": 0,
        "answers":   {},        # {문항번호: 선택텍스트} — 위젯 key와 별도 보관
        "scores":    {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────
#  공통 헤더 - 학번/이름 표시 (필수 항목)
# ─────────────────────────────────────────────
def show_header():
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(90deg, #1a1a2e, #16213e);
            padding: 10px 18px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.82rem;
            color: #aaa;
        '>
            🏈 NFL 팀 추천 테스트 &nbsp;|&nbsp;
            학번: <b style='color:#f0f0f0'>{STUDENT_ID}</b>
            &nbsp;·&nbsp;
            이름: <b style='color:#f0f0f0'>{STUDENT_NAME}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  페이지 1: 로그인
# ─────────────────────────────────────────────
def _player_img_html(filename: str) -> str:
    b64 = load_image_base64(filename)
    ext = filename.rsplit(".", 1)[-1]
    return f"""
    <div style='
        height: 540px;
        overflow: hidden;
        border-radius: 12px;
    '>
        <img src="data:image/{ext};base64,{b64}"
             style='width:100%; height:100%; object-fit:cover; border-radius:12px;'>
    </div>
    """


def page_login():
    left_col, center_col, right_col = st.columns([1, 1.4, 1])

    with left_col:
        st.markdown(_player_img_html("player_left.jpg"), unsafe_allow_html=True)

    with center_col:
        show_header()
        st.title("🏈 나에게 맞는 NFL 팀은?")
        st.markdown(
            "10가지 성향 질문에 답하면 "
            "당신과 가장 잘 맞는 **NFL 팀**을 추천해드립니다!"
        )
        st.divider()

        st.subheader("🔐 로그인")
        with st.form("login_form"):
            username  = st.text_input("아이디")
            password  = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            if USERS.get(username) == password:
                st.session_state.logged_in = True
                st.session_state.username  = username
                st.session_state.page      = "intro"
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

        st.caption("테스트 계정  |  아이디: admin  /  비밀번호: Nfl2025!")

    with right_col:
        st.markdown(_player_img_html("player_right.jpg"), unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  페이지 2: 테스트 소개
# ─────────────────────────────────────────────
def page_intro():
    # 두 캐싱 함수 모두 미리 호출 → 이후 quiz/result에서 파일 I/O 없이 재사용
    questions = load_questions()
    load_teams()

    st.title("🏈 NFL 팀 추천 테스트")
    st.markdown(f"안녕하세요, **{st.session_state.username}** 님! 👋")
    st.divider()

    st.info(
        "**테스트 안내**\n\n"
        f"- 총 **{len(questions)}문항** (객관식 4지선다)\n"
        "- 각 보기는 NFL 팀들과 점수로 연결되어 있습니다\n"
        "- 모든 문항이 끝나면 가장 높은 점수의 팀을 추천해드립니다\n"
        "- 8개 팀 중 당신과 가장 잘 맞는 팀을 찾아보세요!"
    )

    st.markdown("##### 추천 후보 팀")
    teams = load_teams()
    cols  = st.columns(4)
    for i, (_, team) in enumerate(teams.items()):
        cols[i % 4].markdown(
            f"{team['emoji']} {team['name'].split()[-1]}"
        )

    st.divider()
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("✅ 테스트 시작!", type="primary", use_container_width=True):
            st.session_state.page      = "quiz"
            st.session_state.current_q = 0
            st.session_state.answers   = {}
            st.session_state.scores    = {}
            st.rerun()
    with col2:
        if st.button("로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ─────────────────────────────────────────────
#  페이지 3: 퀴즈 풀이
# ─────────────────────────────────────────────
def _calc_scores(questions: list, answers: dict) -> dict:
    """저장된 answers dict로 점수를 한 번에 계산"""
    scores = {}
    for q_idx, q in enumerate(questions):
        ans = answers.get(q_idx)
        if ans:
            texts = [o["text"] for o in q["options"]]
            if ans in texts:
                for team_key, pts in q["options"][texts.index(ans)]["scores"].items():
                    scores[team_key] = scores.get(team_key, 0) + pts
    return scores


def page_quiz():
    st.markdown(
        """
        <style>
        div[role="radiogroup"] label {
            font-size: 1.15rem !important;
            padding: 6px 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    questions = load_questions()
    idx       = st.session_state.current_q
    total     = len(questions)

    st.progress(idx / total, text=f"진행 상황: {idx} / {total}")
    st.markdown(f"#### Q{idx + 1}. {questions[idx]['question']}")
    st.divider()

    options  = questions[idx]["options"]
    opt_text = [o["text"] for o in options]

    # 이전에 저장된 답이 있으면 index로 복원 (뒤로가기 시 선택 유지)
    saved       = st.session_state.answers.get(idx)
    default_idx = opt_text.index(saved) if saved in opt_text else None

    if idx == 7:
        radio_col, info_col = st.columns([3, 2])
        with radio_col:
            selected = st.radio("보기를 선택하세요:", opt_text, index=default_idx, key=f"q_{idx}")
        with info_col:
            st.markdown(
                """
                <div style='
                    background: #1a1a2e;
                    border-left: 4px solid #e8962e;
                    border-radius: 8px;
                    padding: 16px 18px;
                    font-size: 0.9rem;
                    line-height: 1.7;
                '>
                    <b style='color:#e8962e; font-size:1rem'>🏈 쿼터백(QB)이란?</b><br><br>
                    공격 전체를 지휘하는 핵심 포지션입니다.<br><br>
                    <b style='color:#ccc'>모바일 QB</b><br>
                    발이 빠르고 직접 달리는 플레이도 능숙. 패스+런 이중위협.<br><br>
                    <b style='color:#ccc'>포켓 QB</b><br>
                    라인 보호 구역(포켓) 안에서 정확한 패스에 집중하는 클래식 스타일.
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        selected = st.radio("보기를 선택하세요:", opt_text, index=default_idx, key=f"q_{idx}")

    st.divider()
    col_prev, col_next = st.columns(2)

    with col_prev:
        if idx > 0:
            if st.button("← 이전", use_container_width=True):
                if selected:
                    st.session_state.answers[idx] = selected
                st.session_state.current_q -= 1
                st.rerun()

    with col_next:
        label = "결과 보기 🏆" if idx + 1 >= total else "다음 ➡️"
        if st.button(label, type="primary", disabled=(selected is None), use_container_width=True):
            st.session_state.answers[idx] = selected
            if idx + 1 >= total:
                st.session_state.scores = _calc_scores(questions, st.session_state.answers)
                st.session_state.page   = "result"
            else:
                st.session_state.current_q += 1
            st.rerun()

    if selected is None:
        st.caption("보기를 선택해야 다음으로 넘어갈 수 있습니다.")


# ─────────────────────────────────────────────
#  페이지 4: 결과
# ─────────────────────────────────────────────
def page_result():
    teams  = load_teams()
    scores = st.session_state.scores

    # 최고 점수 계산 및 동점 팀 목록 추출
    top_score  = max(scores.values())
    top_keys   = [k for k, v in scores.items() if v == top_score and k in teams]
    is_tie     = len(top_keys) > 1

    if is_tie:
        st.title("🏆 당신과 잘 맞는 NFL 팀들!")
        st.warning(f"**{len(top_keys)}개 팀이 {top_score}점으로 동점**입니다! 모두 당신과 잘 맞는 팀이에요.")
    else:
        st.title("🏆 추천 NFL 팀 결과!")
    st.divider()

    # 결과 카드 (동점이면 카드 여러 개, 단독이면 1개)
    for best_key in top_keys:
        best       = teams[best_key]
        card_color = best.get("card_color", best["color"])

        try:
            logo_b64  = load_image_base64(f"logo_{best_key}.png")
            logo_html = (
                f"<img src='data:image/png;base64,{logo_b64}' "
                f"style='width:130px; height:130px; object-fit:contain;'>"
            )
        except Exception:
            logo_html = f"<div style='font-size:4rem'>{best['emoji']}</div>"

        st.markdown(
            f"""
            <div style='
                background: {card_color}22;
                border: 2px solid {card_color};
                border-radius: 14px;
                padding: 24px 30px;
                display: flex;
                align-items: center;
                gap: 28px;
                margin-bottom: 20px;
            '>
                <div style='flex: 0 0 auto;'>
                    {logo_html}
                </div>
                <div style='flex: 1; text-align: left;'>
                    <div style='
                        font-size: 2rem;
                        font-weight: 800;
                        color: #ffffff;
                        margin-bottom: 6px;
                    '>{best["name"]}</div>
                    <div style='color: #aaa; font-size: 0.9rem'>
                        📍 {best["city"]} &nbsp;·&nbsp; {best["conference"]}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f"**팀 소개** &nbsp; {best['description']}")
        st.success(f"💡 **추천 이유** &nbsp; {best['reason']}")
        if is_tie and best_key != top_keys[-1]:
            st.divider()

    # 전체 점수 순위
    with st.expander("📊 전체 팀 점수 보기"):
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (key, score) in enumerate(sorted_scores, 1):
            if key in teams:
                t = teams[key]
                bar = "█" * score + "░" * (20 - score)
                st.markdown(
                    f"`{rank}위` {t['emoji']} **{t['name']}** &nbsp; "
                    f"`{score}점` &nbsp; `{bar}`"
                )

    # 팀 선정 기준 설명
    with st.expander("🏈 8개 팀 선정 근거 및 점수 산정 기준"):
        st.markdown("""
**[ 팀 선정 원칙 ]**

NFL 32팀 중 아래 기준으로 8팀을 선발했습니다.
- 팀 정체성이 뚜렷하고 서로 겹치지 않을 것
- AFC/NFC, 대도시/소도시, 선벨트/혹한 지역 등 다양성 확보
- NFL 비팬도 이름을 알 수 있는 브랜드 인지도

---

**[ 팀별 선정 근거 ]**

🔴 **Kansas City Chiefs (KC)**
- 근거: 최근 5년 슈퍼볼 4회 진출. Andy Reid 감독은 NFL 역대 최고 전략가 중 하나로 평가. Mahomes의 정밀 패싱이 핵심.
- 테마: 전략적, 승리지향, 패싱 오펜스

🌉 **San Francisco 49ers (SF)**
- 근거: 2023 시즌 런패스 균형 지표(DVOA) 상위권. Shanahan 시스템은 팀워크와 포지션 순환이 핵심.
- 테마: 균형, 팀워크, 시스템 중심

⭐ **Dallas Cowboys (DAL)**
- 근거: Forbes 기준 NFL 최고 가치 팀($9.2B, 2023). "America's Team" 별명, AT&T 스타디움은 NFL 최대 규모.
- 테마: 화려함, 엔터테인먼트, 대도시

🧀 **Green Bay Packers (GB)**
- 근거: NFL 유일 팬 소유 비영리 구단. 인구 10만의 소도시에서 NFL 최고 팬 충성도 보유. Favre→Rodgers로 이어지는 레전드 QB 계보.
- 테마: 전통, 팬 유대감, 클래식

⚙️ **Pittsburgh Steelers (PIT)**
- 근거: NFL 최다 타이 슈퍼볼 우승(6회). Steel Curtain 수비 유산, 강력한 런+수비 정체성 유지.
- 테마: 강인함, 수비, 공업 도시

🐬 **Miami Dolphins (MIA)**
- 근거: 2023년 NFL 최다 득점 오펜스. 따뜻한 기후와 South Beach 문화, 스피드 중심 플레이.
- 테마: 스피드, 화려함, 선벨트

🦬 **Buffalo Bills (BUF)**
- 근거: ESPN 팬 충성도 지수 최상위권. Bills Mafia 문화, 버팔로 혹한 홈 어드밴티지 유명.
- 테마: 팬 열정, 악천후, 소도시 근성

🏴‍☠️ **Las Vegas Raiders (LV)**
- 근거: NFL에서 가장 독특한 팀 문화(검정+은 컬러, Black Hole 팬섹션). 라스베이거스 Allegiant Stadium은 NFL 최신 실내 경기장.
- 테마: 반항적, 독특함, 화려한 도시

---

**[ 점수 2점 vs 1점 기준 ]**

- **2점**: 해당 특성이 팀의 핵심 정체성 → 그 팀을 설명할 때 가장 먼저 언급되는 특징
- **1점**: 해당 특성과 연관성이 있으나 부차적 → 공유하지만 대표 이미지는 아님

예시:
- KC + "전략적이고 냉철" = **2점** → Andy Reid의 전략, Mahomes의 정밀함이 팀의 핵심
- KC + "공격적이고 승부욕 강함" = **1점** → 공격적이긴 하나 이미지는 "폭발력"보다 "정교함"
- PIT + "강력한 런닝 게임" = **2점** → Steel Curtain 이후 수십 년간 팀 정체성의 핵심
- DAL + "대도시 선호" = **2점** → NFL 최고가치팀, 엔터테인먼트 문화의 상징
- GB + "팬과의 유대감" = **2점** → 팬이 구단주인 유일한 팀, 팬 = 팀 자체
        """)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 테스트하기", type="primary", use_container_width=True):
            st.session_state.page      = "quiz"
            st.session_state.current_q = 0
            st.session_state.answers   = {}
            st.session_state.scores    = {}
            st.rerun()
    with col2:
        if st.button("🏠 처음으로", use_container_width=True):
            st.session_state.page      = "intro"
            st.session_state.current_q = 0
            st.session_state.answers   = {}
            st.session_state.scores    = {}
            st.rerun()


# ─────────────────────────────────────────────
#  메인
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="NFL 팀 추천 테스트",
        page_icon="🏈",
        layout="wide",
    )

    init_session()

    if not st.session_state.logged_in:
        page_login()
        return

    page = st.session_state.page
    if page == "intro":
        page_intro()
    elif page == "quiz":
        page_quiz()
    elif page == "result":
        page_result()


if __name__ == "__main__":
    main()
