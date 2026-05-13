import base64          # 이미지 파일을 HTML에 직접 삽입하기 위한 base64 인코딩
import json             # questions.json, teams.json 파일 파싱
import streamlit as st  # 웹 앱 프레임워크
from pathlib import Path  # 플랫폼 독립적인 파일 경로 처리

# ─────────────────────────────────────────────
#  학생 정보 - 과제 필수 표시 항목
# ─────────────────────────────────────────────
STUDENT_ID   = "2021204039"
STUDENT_NAME = "박종훈"

# ─────────────────────────────────────────────
#  사용자 계정 - 로그인 비교 기준값
#  실제 서비스라면 DB나 환경변수에 저장해야 하지만,
#  과제 범위 내에서는 코드 내 dict로 관리
# ─────────────────────────────────────────────
USERS = {
    "admin": "Nfl2025!",   # 테스트용 기본 계정
    "nfl":   "GoChiefs#7", # 추가 테스트 계정
}

# ─────────────────────────────────────────────
#  캐싱 함수 - @st.cache_data 적용
#
#  Streamlit은 버튼 클릭, 라디오 선택 등 모든 인터랙션마다
#  스크립트 전체를 처음부터 재실행한다.
#  @st.cache_data를 붙이면 최초 1회 실행 결과를 메모리에 저장하고,
#  이후 동일 인자로 호출 시 저장값을 즉시 반환하여 파일 I/O를 생략한다.
# ─────────────────────────────────────────────
@st.cache_data
def load_image_base64(filename: str) -> str:
    """
    images/ 폴더의 이미지를 base64 문자열로 변환.
    HTML <img src="data:image/...;base64,..."> 형태로 삽입하기 위해 사용.
    이미지 인코딩은 비용이 크므로 캐싱 효과가 가장 뚜렷하다.
    """
    path = Path(__file__).parent / "images" / filename
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_data
def load_questions() -> list:
    """
    data/questions.json 로딩.
    10개 문항과 각 보기별 팀 점수 정보를 담고 있다.
    퀴즈 진행 중 매 렌더링마다 파일을 읽지 않도록 캐싱.
    """
    path = Path(__file__).parent / "data" / "questions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_teams() -> dict:
    """
    data/teams.json 로딩.
    8개 팀의 이름, 컬러, 소개, 추천 이유 등 정보를 담고 있다.
    결과 화면에서 매 렌더링마다 파일을 읽지 않도록 캐싱.
    """
    path = Path(__file__).parent / "data" / "teams.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
#  세션 상태 초기화
#  session_state는 Streamlit의 전역 상태 저장소.
#  페이지 재실행 시에도 값이 유지되므로 로그인 상태,
#  현재 페이지, 퀴즈 진행 상황 등을 저장하는 데 사용.
# ─────────────────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,   # 로그인 여부 - False면 로그인 화면만 접근 가능
        "username":  "",      # 로그인한 사용자 아이디
        "page":      "login", # 현재 페이지: login | intro | quiz | result
        "current_q": 0,       # 현재 문항 번호 (0-indexed)
        "answers":   {},      # {문항번호(int): 선택한 보기 텍스트(str)}
                              # 위젯 key는 미렌더링 시 자동 소멸하므로
                              # 별도 dict에 수동 저장하여 뒤로가기 기능 구현
        "scores":    {},      # {팀코드: 누적점수} - 결과 계산용
    }
    # 이미 초기화된 키는 덮어쓰지 않음 (페이지 재실행 시 상태 보존)
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────
#  공통 헤더 - 학번/이름 배너
#  과제 요건: 앱 첫 화면에 반드시 표시
#  로그인 화면의 중앙 컬럼 최상단에 위치하며,
#  로그인 이후 화면에서는 표시하지 않음
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
    """
    선수 이미지를 고정 높이 컨테이너에 꽉 차게 표시하는 HTML 생성.
    object-fit: cover로 비율을 유지하면서 영역을 채운다.
    base64 인코딩된 이미지를 HTML에 직접 삽입하여 외부 URL 없이 표시.
    """
    b64 = load_image_base64(filename)
    ext = filename.rsplit(".", 1)[-1]  # 확장자 추출 (jpg / png)
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
    # 3컬럼 레이아웃: [선수 이미지 | 로그인 폼 | 선수 이미지]
    # layout="wide" 설정 덕분에 양쪽 이미지가 넓게 표시됨
    left_col, center_col, right_col = st.columns([1, 1.4, 1])

    with left_col:
        st.markdown(_player_img_html("player_left.jpg"), unsafe_allow_html=True)

    with center_col:
        show_header()  # 학번/이름 배너 (과제 필수 항목)
        st.title("🏈 나에게 맞는 NFL 팀은?")
        st.markdown(
            "10가지 성향 질문에 답하면 "
            "당신과 가장 잘 맞는 **NFL 팀**을 추천해드립니다!"
        )
        st.divider()

        st.subheader("🔐 로그인")
        # st.form: 내부 위젯 변경 시 즉시 rerun되지 않고
        # 제출 버튼을 눌러야만 처리됨 → 불필요한 rerun 방지
        with st.form("login_form"):
            username  = st.text_input("아이디")
            password  = st.text_input("비밀번호", type="password")  # 입력값 마스킹
            submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            # USERS dict에서 아이디로 조회 후 비밀번호 일치 여부 확인
            if USERS.get(username) == password:
                print(f"[LOGIN] 로그인 성공 - 사용자: {username}")
                # 로그인 성공: 상태 저장 후 intro 페이지로 이동
                st.session_state.logged_in = True
                st.session_state.username  = username
                st.session_state.page      = "intro"
                st.rerun()  # 즉시 페이지 재실행으로 화면 전환
            else:
                print(f"[LOGIN] 로그인 실패 - 사용자: {username}")
                # 로그인 실패: 오류 메시지 출력 (페이지는 유지)
                st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

        st.caption("테스트 계정  |  아이디: admin  /  비밀번호: Nfl2025!")

    with right_col:
        st.markdown(_player_img_html("player_right.jpg"), unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  페이지 2: 테스트 소개
# ─────────────────────────────────────────────
def page_intro():
    # 퀴즈/결과 페이지에서 쓸 데이터를 여기서 미리 캐시에 올림
    # → 이후 load_questions(), load_teams() 호출 시 파일 I/O 없이 재사용
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

    # 추천 후보 팀 목록을 4열 그리드로 표시
    st.markdown("##### 추천 후보 팀")
    teams = load_teams()
    cols  = st.columns(4)
    for i, (_, team) in enumerate(teams.items()):
        cols[i % 4].markdown(
            f"{team['emoji']} {team['name'].split()[-1]}"  # 팀명 마지막 단어만 표시
        )

    st.divider()
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("✅ 테스트 시작!", type="primary", use_container_width=True):
            # 이전 테스트 기록 초기화 후 퀴즈 시작
            st.session_state.page      = "quiz"
            st.session_state.current_q = 0
            st.session_state.answers   = {}
            st.session_state.scores    = {}
            st.rerun()
    with col2:
        if st.button("로그아웃", use_container_width=True):
            # session_state 전체 삭제 → 로그인 화면으로 복귀
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ─────────────────────────────────────────────
#  페이지 3: 퀴즈 풀이
# ─────────────────────────────────────────────

def _calc_scores(questions: list, answers: dict) -> dict:
    """
    저장된 answers dict를 순회하며 팀별 점수를 합산.

    answers = {0: "공격적이고 승부욕이 강하다", 1: "뜨겁고 강렬한 여름", ...}
    각 보기의 "scores" 필드에는 {"KC": 2, "PIT": 2, "LV": 1} 형태로
    팀별 점수가 정의되어 있으며, 해당 값을 누적 합산한다.

    마지막 문항 완료 시 단 1회만 호출되어 최종 scores를 계산한다.
    """
    scores = {}
    for q_idx, q in enumerate(questions):
        ans = answers.get(q_idx)  # 해당 문항의 선택 텍스트
        if ans:
            texts = [o["text"] for o in q["options"]]
            if ans in texts:
                # 선택된 보기의 팀별 점수를 누적
                for team_key, pts in q["options"][texts.index(ans)]["scores"].items():
                    scores[team_key] = scores.get(team_key, 0) + pts
    return scores


def page_quiz():
    # 라디오 버튼 글씨 크기를 CSS로 확대 (기본값 1rem → 1.15rem)
    # Streamlit이 제공하는 직접적인 글씨 크기 옵션이 없으므로
    # unsafe_allow_html로 커스텀 스타일 주입
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
    idx       = st.session_state.current_q  # 현재 문항 번호 (0-indexed)
    total     = len(questions)              # 전체 문항 수 (10)

    # 진행률 = 현재 문항 번호 / 전체 문항 수 (0.0 ~ 1.0)
    st.progress(idx / total, text=f"진행 상황: {idx} / {total}")
    st.markdown(f"#### Q{idx + 1}. {questions[idx]['question']}")
    st.divider()

    options  = questions[idx]["options"]
    opt_text = [o["text"] for o in options]

    # 뒤로가기로 돌아왔을 때 이전 선택을 라디오에 복원
    # session_state.answers에 저장된 텍스트를 index로 변환하여 default로 지정
    # (Streamlit 위젯 key는 미렌더링 시 자동 소멸하므로 별도 저장 필요)
    saved       = st.session_state.answers.get(idx)
    default_idx = opt_text.index(saved) if saved in opt_text else None

    # 8번 문항(idx=7)에만 쿼터백 설명 패널 표시
    # NFL에 익숙하지 않은 사용자를 위한 포지션 안내
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
        # 나머지 문항은 라디오만 표시
        selected = st.radio("보기를 선택하세요:", opt_text, index=default_idx, key=f"q_{idx}")

    st.divider()
    col_prev, col_next = st.columns(2)

    with col_prev:
        # 첫 번째 문항에서는 이전 버튼 미표시
        if idx > 0:
            if st.button("← 이전", use_container_width=True):
                # 현재 선택값을 answers에 저장 후 이전 문항으로 이동
                if selected:
                    st.session_state.answers[idx] = selected
                print(f"[QUIZ] Q{idx+1} → Q{idx} 이전으로 이동")
                st.session_state.current_q -= 1
                st.rerun()

    with col_next:
        # 마지막 문항에서는 "결과 보기"로 버튼 레이블 변경
        label = "결과 보기 🏆" if idx + 1 >= total else "다음 ➡️"
        # 보기를 선택하지 않으면 버튼 비활성화
        if st.button(label, type="primary", disabled=(selected is None), use_container_width=True):
            st.session_state.answers[idx] = selected  # 현재 답변 저장
            print(f"[QUIZ] Q{idx+1} 선택: {selected}")

            if idx + 1 >= total:
                # 마지막 문항: 전체 answers로 최종 점수 계산 후 결과 페이지로
                st.session_state.scores = _calc_scores(questions, st.session_state.answers)
                st.session_state.page   = "result"
                print(f"[RESULT] 퀴즈 완료 - 점수: {st.session_state.scores}")
            else:
                # 다음 문항으로 이동
                st.session_state.current_q += 1
            st.rerun()

    if selected is None:
        st.caption("보기를 선택해야 다음으로 넘어갈 수 있습니다.")



# ─────────────────────────────────────────────
#  페이지 4: 결과
# ─────────────────────────────────────────────
def page_result():
    teams  = load_teams()
    scores = st.session_state.scores  # _calc_scores()가 계산한 팀별 점수

    # 최고 점수 추출 후 동점 팀 전체를 리스트로 수집
    # 단독 1위면 카드 1개, 동점이면 카드 여러 개 표시
    top_score = max(scores.values())
    top_keys  = [k for k, v in scores.items() if v == top_score and k in teams]
    is_tie    = len(top_keys) > 1

    if is_tie:
        st.title("🏆 당신과 잘 맞는 NFL 팀들!")
        st.warning(f"**{len(top_keys)}개 팀이 {top_score}점으로 동점**입니다! 모두 당신과 잘 맞는 팀이에요.")
    else:
        st.title("🏆 추천 NFL 팀 결과!")
    st.divider()

    # 동점 팀 수만큼 반복하여 결과 카드 렌더링
    for best_key in top_keys:
        best = teams[best_key]

        # card_color: 팀 고유 컬러 사용
        # DAL(Cowboys)처럼 로고와 팀 컬러가 유사할 경우
        # teams.json의 "card_color" 필드로 별도 카드 색상 지정 가능
        card_color = best.get("card_color", best["color"])

        # 팀 로고 이미지 로딩 (images/logo_{팀코드}.png)
        # 파일이 없으면 예외 처리 후 이모지로 대체
        try:
            logo_b64  = load_image_base64(f"logo_{best_key}.png")
            logo_html = (
                f"<img src='data:image/png;base64,{logo_b64}' "
                f"style='width:130px; height:130px; object-fit:contain;'>"
            )
        except Exception:
            logo_html = f"<div style='font-size:4rem'>{best['emoji']}</div>"

        # 결과 카드: flexbox로 [로고 | 팀명+정보] 좌우 배치
        # background에 팀 컬러 + 22(hex, ~13% 투명도)로 은은한 배경 적용
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

    # 전체 팀 점수 순위 (접기/펼치기)
    with st.expander("📊 전체 팀 점수 보기"):
        # 점수 내림차순 정렬
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (key, score) in enumerate(sorted_scores, 1):
            if key in teams:
                t = teams[key]
                # 텍스트 막대 그래프: 최대 20칸 (10문항 × 최대 2점)
                # "█" * score: 획득 점수만큼 채운 블록
                # "░" * (20 - score): 나머지 빈 블록
                bar = "█" * score + "░" * (20 - score)
                st.markdown(
                    f"`{rank}위` {t['emoji']} **{t['name']}** &nbsp; "
                    f"`{score}점` &nbsp; `{bar}`"
                )

    # 팀 선정 기준 설명 (접기/펼치기)
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
            # 퀴즈 관련 상태 초기화 후 첫 문항부터 재시작
            st.session_state.page      = "quiz"
            st.session_state.current_q = 0
            st.session_state.answers   = {}
            st.session_state.scores    = {}
            st.rerun()
    with col2:
        if st.button("🏠 처음으로", use_container_width=True):
            # 소개 화면으로 복귀 (로그인 상태는 유지)
            st.session_state.page      = "intro"
            st.session_state.current_q = 0
            st.session_state.answers   = {}
            st.session_state.scores    = {}
            st.rerun()


# ─────────────────────────────────────────────
#  메인 진입점
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="NFL 팀 추천 테스트",
        page_icon="🏈",
        layout="wide",  # 로그인 화면 양쪽 이미지를 위해 wide 레이아웃 사용
    )

    init_session()

    # 로그인 여부로 접근 가능 페이지 제한
    if not st.session_state.logged_in:
        page_login()
        return

    # 로그인 후 page 상태에 따라 화면 분기
    page = st.session_state.page
    if page == "intro":
        page_intro()
    elif page == "quiz":
        page_quiz()
    elif page == "result":
        page_result()


if __name__ == "__main__":
    main()
