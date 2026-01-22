import re
import time
from typing import List, Dict, Optional, Tuple

import requests
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup

from pathlib import Path
import base64

def img_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

BASE_URL = "https://www.onepiece-cardgame.com"
CARDLIST_URL = f"{BASE_URL}/cardlist/"
CHAR_LIMIT = 140

# ---------------------------
# 見た目（投稿ツール感CSS）
# ---------------------------
st.set_page_config(
    page_title="ONE PIECE CARD GAME Search Tool",
    page_icon="🃏",
    layout="centered"
)

def img_to_base64(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")

st.markdown("""
<style>
/* ====== App background ====== */
.stApp {
  background:
    radial-gradient(1200px 600px at 20% 0%, rgba(0, 180, 255, 0.16), transparent 60%),
    radial-gradient(900px 500px at 80% 10%, rgba(255, 77, 144, 0.10), transparent 55%),
    radial-gradient(900px 500px at 50% 100%, rgba(255, 215, 0, 0.06), transparent 55%),
    linear-gradient(180deg, #0b0f16 0%, #070a10 100%);
}

/* 横幅 & 上余白（見切れ防止） */
.block-container {
  max-width: 820px;
  padding-top: 2.2rem;
  padding-bottom: 3rem;
}

/* Streamlitの余計なUI */
header { background: transparent; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ====== Hero header ====== */
.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 6px 0 2px 0;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.hero img {
  width: min(40vw, 420px);
  height: auto;
  display: block;
  filter: drop-shadow(0 14px 28px rgba(0,0,0,0.45));
}

.hero .sub {
  font-size: 20px;
  letter-spacing: 0.18em;
  opacity: 0.78;
  text-transform: uppercase;
  text-align: center;
  margin-bottom: 30px;
}

/* 見出し */
h2, h3 {
  letter-spacing: 0.02em;
}

/* ===== Inputs ===== */
/* 外側コンテナ */
.stTextInput > div,
.stTextArea > div {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 !important;
}

/* 実際の input / textarea */
.stTextInput input,
.stTextArea textarea {
  border-radius: 30px !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  background: rgba(255,255,255,0.05) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02) !important;
  font-size: 16px !important;
  padding: 14px 16px !important;
}

.stTextInput div[data-baseweb="input"] {
  border: none !important;
  background: transparent !important;
}

/* 二重枠の根本対策（BaseWebの内側div） */
div[data-testid="stTextInput"] div[data-baseweb="input"] > div,
div[data-testid="stTextInput"] div[data-baseweb="input"] > div:focus-within {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div,
div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div:focus-within {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* ===== Global buttons (通常のCTA用) ===== */
/* primary だけグラデにする（secondary は “塗らない”） */
.stButton button[kind="primary"],
.stButton button[data-testid="baseButton-primary"] {
  width: 100%;
  border-radius: 30px;
  padding: 12px 14px;
  font-size: 16px;
  font-weight: 800;
  border: 0;
  background: linear-gradient(90deg, rgba(0,180,255,0.95), rgba(0,255,180,0.85));
  color: #071019;
  box-shadow: 0 10px 22px rgba(0,0,0,0.35);
}

.stButton button[kind="primary"]:hover,
.stButton button[data-testid="baseButton-primary"]:hover {
  filter: brightness(1.06);
}

/* secondary（デフォルト）を地味にする：アプリ全体の整合性も上がる */
.stButton button[kind="secondary"],
.stButton button[data-testid="baseButton-secondary"] {
  width: 100%;
  border-radius: 30px;
  padding: 12px 14px;
  font-size: 16px;
  font-weight: 800;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.88);
  box-shadow: 0 10px 22px rgba(0,0,0,0.20);
}

.stButton button[kind="secondary"]:hover,
.stButton button[data-testid="baseButton-secondary"]:hover {
  background: rgba(255,255,255,0.05);
}

.stButton button:hover {
  filter: brightness(1.06);
}

/* ===== OK/NG badge ===== */
.badge-ok, .badge-ng {
  display:inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 900;
  font-size: 12px;
  letter-spacing: 0.04em;
}
.badge-ok {
  background: rgba(76,175,80,0.16);
  border: 1px solid rgba(76,175,80,0.35);
}
.badge-ng {
  background: rgba(255,82,82,0.16);
  border: 1px solid rgba(255,82,82,0.35);
}

.small { opacity: 0.85; font-size: 12px; }

/* ============================================================
   Mode Switch (A/B)
   ============================================================ */

/* modeRow内は余白を詰める */
.modeRow { margin-top: 10px; }

/* modeRow内のボタンは“カード”風に大きく */
.modeRow button[kind="primary"],
.modeRow button[data-testid="baseButton-primary"],
.modeRow button[kind="secondary"],
.modeRow button[data-testid="baseButton-secondary"]{
  text-align: center !important;  /* 文字中央にしたいなら */
  padding: 18px 20px !important;
  border-radius: 999px !important;
  font-size: 20px !important;
  font-weight: 900 !important;
}

/* SPは縦積み + 幅100% */
@media (max-width: 700px) {
  .modeRow div[data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
    gap: 14px !important;
  }
  .modeRow div[data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
  }
}

/* PCは横並び gap狭め */
@media (min-width: 701px) {
  .modeRow div[data-testid="stHorizontalBlock"] {
    gap: 14px !important;
  }
}
            
/* カード画像のグリッドレイアウト */
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-start;
}

.card-item {
  /* デフォルト（PC）は3列 */
  width: calc(33.333% - 10px);
  box-sizing: border-box;
  margin-bottom: 15px;
  text-align: center;
}

.card-item img {
  width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.card-caption {
  font-size: 10px;
  margin-top: 5px;
  line-height: 1.2;
  opacity: 0.8;
}

/* スマホ（幅700px以下）では2列にする */
@media (max-width: 700px) {
  .card-item {
    width: calc(50% - 10px);
  }
}
            
</style>

""", unsafe_allow_html=True)


# ---------------------------
# ユーティリティ
# ---------------------------
CARDNO_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}-\d{3}\b")


def unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def sanitize_pack_text(s: str) -> str:
    # 表記ゆれが出る場合の軽い整形（必要なら増やせる）
    return re.sub(r"\s+", " ", s).strip()


def build_image_url(data_src: str) -> str:
    # ../images/... を https://www.onepiece-cardgame.com/images/... に変換
    src = data_src.replace("../", "").lstrip("./")
    return f"{BASE_URL}/{src}"


# ---------------------------
# 公式サイトから取得
# ---------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)  # 24hキャッシュ
def fetch_card_data(card_no: str) -> Dict:
    time.sleep(0.7)

    s = requests.Session()
    s.headers.update(
        {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"}
    )

    r0 = s.get(CARDLIST_URL, timeout=25)
    r0.raise_for_status()

    payload = {"freewords": card_no, "series": ""}
    r = s.post(CARDLIST_URL, data=payload, timeout=25)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    card_name: Optional[str] = None
    variants: List[Dict] = []   # ← 画像ごとの情報を持つ
    all_packs: List[str] = []

    for dl in soup.select("dl.modalCol"):
        spans = dl.select("dt .infoCol span")
        name_el = dl.select_one("dt .cardName")
        if not spans or not name_el:
            continue

        no_text = spans[0].get_text(strip=True)
        if no_text != card_no:
            continue

        if card_name is None:
            card_name = name_el.get_text(strip=True)

        # このdl（=この画像）に紐づく入手情報を取る
        pack_texts = []
        for gi in dl.select("dd .backCol .getInfo"):
            h3 = gi.select_one("h3")
            h3_text = h3.get_text(strip=True) if h3 else ""
            if h3_text and "入手情報" not in h3_text:
                continue

            gi_clone = BeautifulSoup(str(gi), "html.parser")
            h3c = gi_clone.select_one("h3")
            if h3c:
                h3c.decompose()
            txt = sanitize_pack_text(gi_clone.get_text(" ", strip=True))
            if txt:
                pack_texts.append(txt)

        pack_texts = unique_keep_order(pack_texts)
        all_packs.extend(pack_texts)

        # 画像URL（このdlの画像）
        img = dl.select_one("dd .frontCol img")
        image_url = None
        if img and img.get("data-src"):
            image_url = build_image_url(img["data-src"])

        # dl id（OP05-067 / OP05-067_p1 みたいな識別子）
        variant_id = dl.get("id", "")

        variants.append(
            {
                "variant_id": variant_id,
                "image_url": image_url,
                "packs": pack_texts,
            }
        )

    if not card_name:
        raise ValueError(f"カードが見つかりませんでした：{card_no}")

    # 投稿文用には全packを統合して重複除外
    all_packs = unique_keep_order(all_packs)

    # image_urlがNoneのものを除外
    variants = [v for v in variants if v.get("image_url")]

    return {
        "card_no": card_no,
        "card_name": card_name,
        "packs": all_packs,       # 投稿文用
        "variants": variants,     # 画像ごとのpack紐づけ用
    }

PREFIX_OPTIONS = ["OP", "ST", "P", "EB", "PRB"]
COLOR_OPTIONS = ["赤", "緑", "青", "紫", "黒", "黄", "mix"]

@st.cache_data(ttl=60 * 60, show_spinner=False)  # 1hキャッシュ（短めでOK）
def fetch_candidates_by_name_color(name: str, colors: List[str]) -> List[Dict]:
    """
    freewords(カード名) + colors[] で検索して
    候補一覧（card_no / card_name / thumb_url）を返す
    """
    time.sleep(0.6)

    s = requests.Session()
    s.headers.update(
        {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"}
    )

    # 1回GET（クッキー対策）
    r0 = s.get(CARDLIST_URL, timeout=25)
    r0.raise_for_status()

    payload = {"freewords": name.strip(), "series": ""}

    # colors[] を複数送る（requestsは list を value に入れると複数送信される）
    if colors:
        payload["colors[]"] = colors

    r = s.post(CARDLIST_URL, data=payload, timeout=25)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    candidates: List[Dict] = []
    seen_card_no = set()

    # サムネ a.modalOpen から、対応する dl.modalCol を引いて card_no/name を取得
    for a in soup.select("div.resultCol a.modalOpen"):
        target = a.get("data-src", "")  # 例 "#OP05-067" や "#OP05-067_p1"
        if not target.startswith("#"):
            continue

        dl = soup.select_one(f"dl.modalCol{target}")
        if not dl:
            continue

        spans = dl.select("dt .infoCol span")
        name_el = dl.select_one("dt .cardName")
        if not spans or not name_el:
            continue

        card_no = spans[0].get_text(strip=True)
        card_name = name_el.get_text(strip=True)

        query = name.strip()

        # ★ カード名でのみ絞る（部分一致）
        if query not in card_name:
            continue

        # 候補一覧はカード番号単位で1件に絞る（パラレルで増えすぎるのを防ぐ）
        if card_no in seen_card_no:
            continue
        seen_card_no.add(card_no)

        img = a.select_one("img")
        data_src = (img.get("data-src") or img.get("src")) if img else None
        thumb_url = build_image_url(data_src) if data_src else None

        candidates.append(
            {
                "card_no": card_no,
                "card_name": card_name,
                "thumb_url": thumb_url,
            }
        )

    return candidates


def build_post_text(deck_title: str, card_no: str, card_name: str, packs: List[str], comment: str, hashtag: str) -> str:
    lines = []
    if deck_title.strip():
        lines.append(f"デッキ構築メモ")
    else:
        lines.append("デッキ構築メモ")
    lines.append("")
    lines.append(f"{card_no} {card_name}")
    lines.append("")
    lines.append("▶︎ 収録パック")
    for p in packs:
        lines.append(f"・{p}")
    if comment.strip():
        lines.append("")
        lines.append(comment.strip())
    if hashtag.strip():
        lines.append(hashtag.strip())
    return "\n".join(lines)


def count_chars_for_x(text: str) -> int:
    # まずはシンプルに文字数（改行も1文字）
    return len(text)


# ---------------------------
# UI
# ---------------------------
logo_path = Path(__file__).parent / "assets" / "opcg_logo.jpeg"
logo_b64 = img_to_base64(logo_path)

st.markdown(f"""
<div class="hero">
  <img src="data:image/jpeg;base64,{logo_b64}" alt="ONE PIECE CARD GAME" />
  <div class="sub">ONE PIECE CARD GAME\n\nSearch Tool</div>
</div>
""", unsafe_allow_html=True)

# セッション状態初期化
if "step" not in st.session_state:
    st.session_state.step = 1
if "card_data" not in st.session_state:
    st.session_state.card_data = None
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "return_tab" not in st.session_state:
    st.session_state.return_tab = "A"  # "A" or "B"
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "A"

# ============================
# Step 1 / Step 2 の切り替え
# ============================

# -----------------------------
# Step1：検索（A or B）
# -----------------------------
if st.session_state.step == 1:
    st.markdown("<div class='section'>", unsafe_allow_html=True)

    # ===== モード切り替え（PC:横 / SP:縦） =====
    st.markdown("<div class='modeRow'>", unsafe_allow_html=True)

    isA = (st.session_state.search_mode == "A")
    isB = (st.session_state.search_mode == "B")

    colA, colB = st.columns(2, gap="small")

    with colA:
        if st.button(
            "[A] カード番号で検索",
            key="modeA_card",
            type="primary" if isA else "secondary",
            use_container_width=True,
        ):
            st.session_state.search_mode = "A"
            st.session_state.return_tab = "A"
            st.rerun()

    with colB:
        if st.button(
            "[B] カード名＋色で検索",
            key="modeB_card",
            type="primary" if isB else "secondary",
            use_container_width=True,
        ):
            st.session_state.search_mode = "B"
            st.session_state.return_tab = "B"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)




    st.divider()

    # -----------------------------
    # A) カード番号で検索
    # -----------------------------
    if st.session_state.search_mode == "A":
        st.subheader("Step 1A　カード番号で検索")

        # ▼ デッキ名はStep1では不要。接頭語＋番号だけにする
        c1, c2 = st.columns([1, 3], gap="small")

        with c1:
            prefix = st.selectbox(
                "接頭語",
                PREFIX_OPTIONS,
                index=PREFIX_OPTIONS.index(st.session_state.get("card_prefix", "OP")) if st.session_state.get("card_prefix", "OP") in PREFIX_OPTIONS else 0,
                key="card_prefix",
            )

        with c2:
            number_only = st.text_input(
                "カード番号（例：05-067）",
                value=st.session_state.get("card_number_only", "05-067"),
                placeholder="05-067",
                key="card_number_only",
            )

        # 組み立て（例：OP + 05-067 => OP05-067）
        card_no_norm = f"{prefix}{number_only}".strip().upper()

        # 状態を保持（次回も残す）
        st.session_state["card_no_full"] = card_no_norm

        if st.button("収録弾を検索する", type="primary", key="search_by_no"):
            st.session_state.return_tab = "A"

            # 入力バリデーション（番号だけチェック）
            if not re.fullmatch(r"\d{2}-\d{3}", number_only.strip()):
                st.error("番号の形式が違うかも（例：05-067）")
            else:
                with st.spinner("公式カードリストから検索中…"):
                    try:
                        data = fetch_card_data(card_no_norm)
                        st.session_state.card_data = data
                        st.session_state.step = 2
                        st.session_state.generated_text = ""
                        st.rerun()
                    except Exception as e:
                        st.session_state.card_data = None
                        st.error(f"検索に失敗：{e}")


    # -----------------------------
    # B) カード名＋色で候補検索
    # -----------------------------
    else:
        st.subheader("Step 1B　カード名＋色で検索 → 候補から選ぶ")

        name_q = st.text_input("カード名（例：ゾロ十郎）", value="", placeholder="ゾロ十郎", key="name_query")
        colors_q = st.multiselect("色（複数選択OK）", COLOR_OPTIONS, default=[], key="color_query")

        if st.button("候補を検索する", type="primary", key="search_by_name"):
            st.session_state.return_tab = "B"
            if not name_q.strip():
                st.error("カード名を入力してね。")
            else:
                with st.spinner("候補を検索中…"):
                    try:
                        st.session_state.candidates = fetch_candidates_by_name_color(name_q, colors_q)
                    except Exception as e:
                        st.session_state.candidates = []
                        st.error(f"候補検索に失敗：{e}")

        candidates = st.session_state.get("candidates", [])

        if candidates:
            st.caption(f"候補：{len(candidates)}件（選ぶとStep2へ）")
            cols = st.columns(3)

            for i, c in enumerate(candidates):
                with cols[i % 3]:
                    if c.get("thumb_url"):
                        st.image(c["thumb_url"], use_container_width=True)
                    st.markdown(f"**{c['card_no']}**")
                    st.caption(c["card_name"])

                    if st.button("これを選ぶ", key=f"pick_{c['card_no']}_{i}"):
                        st.session_state.return_tab = "B"
                        st.session_state.search_mode = "B"
                        st.session_state.card_no_input = c["card_no"]
                        st.session_state.deck_title = st.session_state.get("deck_title", "青紫ルフィ")

                        with st.spinner("選択カードを取得中…"):
                            data = fetch_card_data(c["card_no"])

                        st.session_state.card_data = data
                        st.session_state.step = 2
                        st.session_state.generated_text = ""
                        st.rerun()
        else:
            st.info("カード名と色を入れて検索すると、ここに候補が出るよ。")

    st.markdown("</div>", unsafe_allow_html=True)  # section end

# 画面幅を取得して列数を決める（スマホ=2, PC=3）
if "grid_cols" not in st.session_state:
    st.session_state.grid_cols = 3  # default

components.html(
    """
    <script>
      const w = window.innerWidth;
      const cols = (w <= 700) ? 2 : 3;
      // Streamlitへ値を渡す（query param方式）
      const url = new URL(window.location.href);
      if (url.searchParams.get("cols") !== String(cols)) {
        url.searchParams.set("cols", String(cols));
        window.history.replaceState({}, "", url.toString());
      }
    </script>
    """,
    height=0,
)

# URLの cols を読み取って session_state に反映
cols_param = st.query_params.get("cols")
if cols_param:
    try:
        st.session_state.grid_cols = int(cols_param[0])
    except:
        st.session_state.grid_cols = 3


# -----------------------------
# Step2：結果確認 & コメント入力 & 生成（Step2だけ表示）
# -----------------------------
if st.session_state.step == 2 and st.session_state.card_data:
    data = st.session_state.card_data
    deck_title = st.session_state.get("deck_title", "")

    st.subheader("Step 2　結果を見てコメントを作る")

    st.markdown(
        f"**{data['card_no']}**  **{data['card_name']}**  "
        f"<span class='small mono'>（収録 {len(data['packs'])} / 画像 {len(data.get('variants', []))}）</span>",
        unsafe_allow_html=True,
    )

    # 収録パック
    st.write("### ▶︎ 収録パック")
    if data["packs"]:
        for p in data["packs"]:
            st.markdown(f"- {p}")
    else:
        st.info("収録情報が取れなかった（構造変更の可能性あり）")

    # 画像
    st.write("### カード画像")
    variants = data.get("variants", [])

    if variants:
        # HTMLを組み立てる
        html_list = []
        html_list.append('<div class="card-grid">')
        
        for v in variants:
            url = v["image_url"]
            packs_for_img = v.get("packs", [])
            caption = " / ".join(packs_for_img) if packs_for_img else "（収録情報なし）"
            
            # f-stringを使わず、formatメソッドを使うことで波括弧の衝突を避けます
            item_html = '''
                <div class="card-item">
                    <img src="{img_url}" />
                    <div class="card-caption">{img_caption}</div>
                </div>
            '''.format(img_url=url, img_caption=caption)
            
            html_list.append(item_html)
            
        html_list.append('</div>')
        
        # リストを結合して一つの文字列にする
        full_html = "".join(html_list)
        
        # HTMLを表示
        st.markdown(full_html, unsafe_allow_html=True)
    else:
        st.info("画像が取れなかった（構造変更の可能性あり）")

    st.divider()

    deck_title = st.text_input(
        "デッキ名（任意・投稿用）",
        value=st.session_state.get("deck_title", ""),
        placeholder="例：青紫ルフィ",
        key="deck_title_step2",
    )
    st.session_state.deck_title = deck_title

    # コメント・ハッシュタグ
    comment = st.text_input("コメント（例：※ 再録多め。シングル買い検討ライン）", value="※ 再録多め。", key="comment_input")
    hashtag = st.text_input("ハッシュタグ（例：#ワンピースカード）", value="#ワンピースカード", key="hashtag_input")

    if st.button("投稿文を生成する", key="gen_post"):
        post = build_post_text(
            deck_title=deck_title.strip(),
            card_no=data["card_no"],
            card_name=data["card_name"],
            packs=data["packs"],
            comment=comment,
            hashtag=hashtag,
        )
        st.session_state.generated_text = post

    # 投稿文表示＋文字数チェック
    if st.session_state.generated_text:
        post = st.session_state.generated_text
        st.write("### 投稿用テキスト（コピーして使う）")
        st.text_area("出力", value=post, height=260, key="post_text_area")

        length = count_chars_for_x(post)
        if length <= CHAR_LIMIT:
            st.markdown(
                f"<span class='badge-ok'>OK</span>  <span class='mono'>{length} / {CHAR_LIMIT}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<span class='badge-ng'>NG</span>  <span class='mono'>{length} / {CHAR_LIMIT}（{length-CHAR_LIMIT} 文字オーバー）</span>",
                unsafe_allow_html=True,
            )

    st.divider()

    # 戻る（A/Bを確実に切り替え）
    colA, colB = st.columns(2)

    with colA:
        if st.button("Step1Aへ戻る", key="back_to_A"):
            st.session_state.step = 1
            st.session_state.return_tab = "A"
            st.session_state.search_mode = "A"
            st.session_state.card_data = None
            st.session_state.generated_text = ""
            st.rerun()

    with colB:
        if st.button("Step1Bへ戻る", key="back_to_B"):
            st.session_state.step = 1
            st.session_state.return_tab = "B"
            st.session_state.search_mode = "B"
            st.session_state.card_data = None
            st.session_state.generated_text = ""
            st.rerun()



    st.markdown("</div>", unsafe_allow_html=True)





