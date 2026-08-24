#!/usr/bin/env python3
"""docs/index.html の構造検証。依存なし・ビルドなしのまま回せることを優先している。

  python3 scripts/check.py

CI と手元で同じものを走らせる。失敗したら非ゼロで終了する。
"""
import re
import sys
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "docs" / "index.html"
PAIRED = ["div", "tr", "td", "th", "svg", "section", "table", "thead", "tbody",
          "tfoot", "ul", "li", "dl", "dt", "dd", "h1", "h2", "h3", "script",
          "style", "figure", "figcaption", "main", "footer", "canvas", "p"]

errors = []


def fail(msg):
    errors.append(msg)


def main():
    s = SRC.read_text(encoding="utf-8")

    # 1. 開始/終了タグの釣り合い
    for t in PAIRED:
        o = len(re.findall(r"<%s[\s>]" % t, s))
        c = len(re.findall(r"</%s>" % t, s))
        if o != c:
            fail(f"タグ不均衡 <{t}>: 開始{o} 終了{c}")

    # 2. 2つの配信先の両方で成立させるための必須行
    #    doctype が無いと GitHub Pages 側が互換モードになる
    if not s.lstrip().startswith("<!DOCTYPE html>"):
        fail("先頭に <!DOCTYPE html> が無い（Pages 側が互換モードになる）")
    if '<html lang="ja">' not in s[:200]:
        fail('<html lang="ja"> が無い（ラップされても属性はマージされるので必ず書く）')
    for forbidden in ["<head>", "<body>"]:
        if forbidden in s:
            fail(f"{forbidden} を書いてはいけない（Artifact 側のラップと二重になる）")

    # 3. dt/dd は必ず dl の直下に置く
    if s.count("<div><dt>"):
        fail("<dt>/<dd> が <div> 直下にある。<dl> で包むこと")

    # 4. 旅程表はモバイルでカードに組み替わる。全 <td> に data-l が要る
    for tbl in re.findall(r'<table class="itin">.*?</table>', s, re.S):
        for td in re.findall(r"<td\b[^>]*>", tbl):
            if "data-l=" not in td:
                fail(f"itin の <td> に data-l が無い: {td[:60]}")
                break

    # 5. 色トークンは素の :root に定義する。片方のテーマにしか無い色を作らない
    root = re.search(r"^:root\{(.*?)\}", s, re.S | re.M)
    if not root:
        fail(":root のトークン定義が見つからない")
    else:
        defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", root.group(1)))
        used = set(re.findall(r"var\((--[a-z0-9-]+)", s))
        missing = used - defined
        if missing:
            fail(f"素の :root に無いトークンを var() で参照: {sorted(missing)}")
        mq = re.search(r'@media \(prefers-color-scheme:dark\)\{\s*'
                       r':root:not\(\[data-theme="light"\]\)\{(.*?)\}\s*\}', s, re.S)
        dk = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', s, re.S)
        if not mq or not dk:
            fail("ダークテーマのブロックが2つ揃っていない")
        else:
            a = set(re.findall(r"(--[a-z0-9-]+)\s*:", mq.group(1)))
            b = set(re.findall(r"(--[a-z0-9-]+)\s*:", dk.group(1)))
            if a != b:
                fail(f"ダーク2ブロックのトークン集合が不一致: {sorted(a ^ b)}")

    # 6. タイムライン帯のデータが日別表と矛盾しないこと（重なり・はみ出し）
    blk = re.search(r"var DAY = \{(.*?)\n  \};", s, re.S)
    if not blk:
        fail("var DAY のタイムラインデータが見つからない")
    else:
        def mm(t):
            h, m = t.split(":")
            return int(h) * 60 + int(m)
        for line in blk.group(1).strip().splitlines():
            key = line.strip().split(":")[0]
            segs = re.findall(r'\["(\d+:\d+)","(\d+:\d+)","(\w+)"\]', line)
            if not segs:
                continue
            span = sorted((mm(a), mm(b)) for a, b, _ in segs)
            for i in range(len(span) - 1):
                if span[i][1] > span[i + 1][0]:
                    fail(f"{key}: タイムラインの区間が重なっている")
                    break
            if span[0][0] < 8 * 60 or span[-1][1] > 21 * 60:
                fail(f"{key}: 区間が 8:00–21:00 の帯からはみ出している")

    if errors:
        print("NG")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK  ({SRC.relative_to(SRC.parent.parent)}: {len(s.encode()):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
