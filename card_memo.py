#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ONE PIECE CARD GAME 公式カードリストから
- 指定カード番号の「カード名」
- 収録パック（入手情報）
- 画像URL（通常/パラレル等、存在する分すべて）
を取得して

1) 投稿用テキストを標準出力
2) 画像URLは投稿文に入れず、標準出力に「別枠でプリント」
3) アーカイブとして「カード番号_カード名.txt」を作成

使い方：
  python3 card_memo.py

依存：
  pip install requests beautifulsoup4 lxml
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup


# ==========================
# ここだけ自分で指定する欄
# ==========================
deck_title = "青紫ルフィ"   # 【ここ】の部分
card_no = "OP06-118"       # 例：OP06-118
user_comment = "自引きするならThe BESTやけど、10~30円ぐらいで単体入手できるのでその方がコスパ良し。"  # 最後のコメント（自分で書く）
hashtag = "#ワンピースカード"  # 末尾ハッシュタグ
CHAR_LIMIT = 140           # 文字数チェック

# 出力先（同階層に archive フォルダ作る）
ARCHIVE_DIR = Path(__file__).parent / "archive"


# 公式カードリスト（検索）
BASE_URL = "https://www.onepiece-cardgame.com"
CARDLIST_URL = f"{BASE_URL}/cardlist/"


@dataclass
class CardVariant:
    """同一カード番号でも画像違い（通常/パラレル等）をまとめる単位"""
    variant_id: str                 # dl.modalCol の id（例: OP14-001 / OP14-001_p1）
    card_no: str
    card_name: str
    packs: List[str]                # 入手情報（重複排除して順序保持）
    image_url: Optional[str]        # 公式画像URL（?クエリ含む）


def _sanitize_filename(s: str) -> str:
    # mac/windowsでヤバい記号をざっくり除去
    s = re.sub(r'[\\/:*?"<>|]', "_", s)
    s = s.strip()
    return s


def _unique_keep_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _build_image_url(data_src: str) -> str:
    """
    例:
      ../images/cardlist/card/OP14-001.png?251225
    -> https://www.onepiece-cardgame.com/images/cardlist/card/OP14-001.png?251225
    """
    # 先頭の ../ を落とす
    src = data_src.lstrip("./")
    src = src.replace("../", "")
    return f"{BASE_URL}/{src}"


def fetch_variants_by_card_no(target_card_no: str, timeout: int = 20) -> List[CardVariant]:
    """
    公式カードリストのフリーワード検索で対象カード番号を引っ掛け、
    ページ内の dl.modalCol から
    - 収録(入手情報)
    - 画像(data-src)
    を抽出し、通常/パラレルなど存在する分すべて返す。
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
    )

    # 公式カードリストは form post を受ける前提の構造になってるので、
    # まずGETしてからPOST（クッキー等ある場合に備える）
    r0 = session.get(CARDLIST_URL, timeout=timeout)
    r0.raise_for_status()

    # フリーワード検索：カード番号
    # series（収録弾）を指定しない = ALLから拾える
    payload = {
        "freewords": target_card_no,
        "series": "",  # ALL
    }
    r = session.post(CARDLIST_URL, data=payload, timeout=timeout)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    variants: List[CardVariant] = []

    # ページ内に dl.modalCol がずらっと並ぶので、
    # infoCol の最初の <span> が card_no と一致するものだけ拾う
    for dl in soup.select("dl.modalCol"):
        info_spans = dl.select("dt .infoCol span")
        if not info_spans:
            continue

        no_text = info_spans[0].get_text(strip=True)
        if no_text != target_card_no:
            continue

        variant_id = dl.get("id", "").strip() or "(no-id)"

        # カード名
        name_el = dl.select_one("dt .cardName")
        card_name = name_el.get_text(strip=True) if name_el else ""

        # 入手情報（収録）
        # 「入手情報」ラベルはHTML上h3なので、ここはテキストだけ抽出する
        pack_texts = []
        for gi in dl.select("dd .backCol .getInfo"):
            # 備考(remarks)なども getInfo になってる場合があるので
            # 「入手情報」以外っぽいものは軽く除外（必要なら調整してOK）
            h3 = gi.select_one("h3")
            h3_text = h3.get_text(strip=True) if h3 else ""
            if h3_text and "入手情報" not in h3_text:
                # 例：備考
                continue

            # h3を除いた残りテキストを取る
            # BeautifulSoupでh3を一旦消してからテキスト化
            gi_clone = BeautifulSoup(str(gi), "lxml")
            h3_clone = gi_clone.select_one("h3")
            if h3_clone:
                h3_clone.decompose()
            text = gi_clone.get_text(" ", strip=True)
            if text:
                pack_texts.append(text)

        packs = _unique_keep_order(pack_texts)

        # 画像URL（data-src優先）
        img_el = dl.select_one("dd .frontCol img")
        image_url = None
        if img_el and img_el.get("data-src"):
            image_url = _build_image_url(img_el["data-src"])

        variants.append(
            CardVariant(
                variant_id=variant_id,
                card_no=no_text,
                card_name=card_name,
                packs=packs,
                image_url=image_url,
            )
        )

    # variantごとに packs が同じとは限らないのでそのまま返す
    # ただし card_name は基本同じなので先頭を基準にするのがおすすめ
    return variants


def build_post_text(deck_title_: str, card_no_: str, card_name_: str, packs: List[str], comment: str, hashtag_: str) -> str:
    lines = []
    lines.append("デッキ構築メモ")
    lines.append("")
    lines.append(f"")
    lines.append("")
    lines.append(f"{card_no_} {card_name_}")
    lines.append("")
    lines.append("▶︎ 収録パック")
    for p in packs:
        lines.append(f"・{p}")
    lines.append("")
    if comment:
        lines.append(comment)
    if hashtag_:
        lines.append(hashtag_)
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    variants = fetch_variants_by_card_no(card_no)

    if not variants:
        print(f"見つからない：{card_no}")
        return

    # 代表として先頭のカード名を使う
    card_name = variants[0].card_name or "(カード名不明)"

    # 収録パックは「全部のvariantのpackを合算」して重複排除（順序保持）
    all_packs: List[str] = []
    for v in variants:
        all_packs.extend(v.packs)
    all_packs = _unique_keep_order(all_packs)

    # 投稿テキスト生成（画像URLは入れない）
    text = build_post_text(deck_title, card_no, card_name, all_packs, user_comment, hashtag)
    length = len(text.replace("\n", ""))  # 改行はX上の見え方が微妙なので「簡易チェック」として除外
    ok = length <= CHAR_LIMIT
    over = max(0, length - CHAR_LIMIT)

    # --- 標準出力（投稿文） ---
    print("====== 投稿用テキスト ======")
    print(text)
    print("------ 文字数チェック（簡易：改行除外） ------")
    print(f"{length} / {CHAR_LIMIT} : " + ("OK" if ok else f"NG（{over}文字オーバー）"))

    # --- 画像URLは別枠でプリント（全部） ---
    print("\n====== 画像URL（存在する分すべて） ======")
    for i, v in enumerate(variants, start=1):
        print(f"[{i}] variant_id={v.variant_id}")
        if v.image_url:
            print(v.image_url)
        else:
            print("(画像URLなし)")
        print("")

    # --- アーカイブ保存（カード番号_カード名.txt） ---
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    filename = _sanitize_filename(f"{card_no}_{card_name}.txt")
    out_path = ARCHIVE_DIR / filename
    out_path.write_text(text, encoding="utf-8")
    print(f"✅ アーカイブ保存: {out_path}")


if __name__ == "__main__":
    main()
