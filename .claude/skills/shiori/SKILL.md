---
name: shiori
description: Rules for editing docs/index.html, the single-file travel handbook in this repo. Use whenever changing that file — layout, CSS tokens, the itinerary tables, the SVG figures, or the timeline script. Covers the dual publish targets (GitHub Pages serves the file raw; the Artifact tool wraps it), the verification commands, and the failure modes that source review cannot catch.
---

# docs/index.html を編集するときの決まり

このリポジトリは **1ファイルの静的サイト** です。`docs/index.html` が全て。
依存なし、ビルド工程なし、テストなし、フレームワークなし。`package.json` は**作らないこと**。

## 最重要：出力先が2つあり、要求が食い違う

同じファイルが2つの経路で配信されます。**両方で成立させる必要があります。**

| 配信先 | 仕組み | 帰結 |
|---|---|---|
| GitHub Pages | `docs/` をそのまま配信 | ファイルが**そのまま**HTML文書になる |
| Artifact ツール | `<!doctype>…<head></head><body>` で**包んでから**配信 | 自前の `<html>` 等は**二重になる** |

ここから決まりが出ます。

- `<head>` `<body>` タグは**書かない**（Artifact 側のラップと二重になる）。
- `<meta charset>` `<meta name="viewport">` `<title>` `<link rel=stylesheet>` は**書いてよい**。
  HTML5 のパース規則で暗黙の `<head>` に入るため、両経路で正しく働く。
- **`<!DOCTYPE html>` と `<html lang="ja">` の2行は必ず書く。**
  - doctype が無いと Pages 側が**互換モード（quirks mode）**になる。Artifact 側は自前の
    doctype を先に出すので、こちらの1行は無視されて害がない。
  - `<html lang="ja">` は**ラップされても効く**。HTML パーサは2つ目の `<html>` 開始タグを
    新しい要素にせず、**既に無い属性だけを既存の html 要素にマージする**ためで、
    `lang` が既存要素に付く。要素は重複しない。
  - 「Artifact がラップするから `<html>` は書けない」は**誤り**。実測で両経路とも
    `document.documentElement.lang === "ja"` / `getElementsByTagName('html').length === 1`
    になることを確認済み。推測で片方を諦めないこと。

## 検証コマンド（変更したら必ず通す）

```bash
# 1. タグの釣り合い・JS 構文・図の数値
python3 - <<'PY'
import re
s=open('docs/index.html',encoding='utf-8').read()
for t in ['div','tr','td','svg','section','table','ul','li','script','style']:
    o=len(re.findall(r'<%s[\s>]'%t,s)); c=len(re.findall(r'</%s>'%t,s))
    print(f"{t}: {'OK' if o==c else '*** MISMATCH %d/%d'%(o,c)}")
PY
python3 -c "import re;s=open('docs/index.html',encoding='utf-8').read();open('/tmp/t.js','w').write(re.search(r'<script>(.*)</script>',s,re.S).group(1))" && node --check /tmp/t.js

# 2. 実ブラウザ計測（ローカル配信 → Lighthouse）
(cd docs && python3 -m http.server 8801 &) ; sleep 2
CHROME_PATH=$(find /opt/pw-browsers -name chrome -type f | head -1) \
npx -y lighthouse http://localhost:8801/index.html \
  --only-categories=accessibility,performance,best-practices \
  --chrome-flags="--headless=new --no-sandbox" --output=json --output-path=/tmp/lh.json --quiet
```

**修正の前後で必ず両方を取り、件数の差分で語ること。**「良くなったはず」は不可。

## ソースを読んでも気づけない失敗（実際に起きたもの）

1. **コントラスト。** `--muted:#63768A` は白の上では 4.68 で通るが、
   `--ground:#EDF0F4` では 4.09、`--sunken:#E4E9EF` では 3.83 で落ちる。
   **トークンを1つ選び損ねると 100 箇所以上が同時に落ちる。**
   色を変えたら必ず「最も暗い背景トークン」との比を計算すること。
2. **ヒーローはテーマ非依存の暗い地。** `.hero` は `--night` 固定で、
   ライト/ダークで色が変わらない。**ここに載る文字にテーマ依存トークンを使ってはいけない。**
   ライトテーマの `--ember` を載せると 4.43 で落ちる。ヒーロー専用トークンを使うこと。
3. **`document.fonts.check()` は嘘をつく。** スタイルシートの取得に失敗していても `true` を返す。
   フォントが実際に来ているかは `requestfailed` イベントか `document.fonts` の中身で見る。
4. **このサンドボックスのブラウザは localhost にしか出られない。**
   `curl` はプロキシ経由で外に出られるので、両者の結果が食い違う。
   Web フォントの読込可否を**ブラウザで**検証しようとしても失敗するが、それは環境要因であって
   サイトの不具合ではない。混同しないこと。

## 触ってはいけない / 壊しやすい部分

- **`.itin` の `<td>` から `data-l` 属性を外さない。**
  760px 以下で表をカードに組み替える際、`td::before{content:attr(data-l)}` が唯一の見出しになる。
  外すとスマホで何の列か分からなくなる。**行を足したら全セルに `data-l` を付ける。**
- **該当なしのセルは `<td data-l="..."></td>` と空にする。** `—` を直接書かない。
  空セルはデスクトップで `:empty::after` がダッシュを出し、モバイルでは `display:none` で消える。
- **色は必ず素の `:root` で定義する。** `@media (prefers-color-scheme)` や `[data-theme]` の中
  **だけ**に色を書くと、テーマ未指定（既定）の閲覧者に適用されず、片方の地に他方の文字が出る。
  ダークの2ブロック（media クエリ版と `[data-theme="dark"]` 版）は**同じトークン集合**を持つこと。
- **図（SVG）の座標は実数値から計算する。** 棒の幅を目分量で置かない。
  変更したら、幅の合計と金額・時間の比が一致することをスクリプトで確かめる。
- **タイムライン帯のデータ（`var DAY`）は日別表と一致させる。**
  片方だけ直すと、表とリボンで運転時間が食い違う。次で照合できる:

```bash
python3 - <<'PY'
import re
s=open('docs/index.html',encoding='utf-8').read()
blk=re.search(r'var DAY = \{(.*?)\n  \};',s,re.S).group(1)
mm=lambda t:(lambda h,m:int(h)*60+int(m))(*t.split(':'))
for line in blk.strip().splitlines():
    k=line.strip().split(':')[0]
    segs=re.findall(r'\["(\d+:\d+)","(\d+:\d+)","(\w+)"\]',line)
    d=sum(mm(b)-mm(a) for a,b,t in segs if t=='drive')
    srt=sorted((mm(a),mm(b)) for a,b,t in segs)
    ov=any(srt[i][1]>srt[i+1][0] for i in range(len(srt)-1))
    print(f"{k}: 運転{d//60}h{d%60:02d} 重なり={ov}")
PY
```

## 使い回す部品

| 用途 | 書き方 |
|---|---|
| 情報の確度 | `<span class="c ok">確認済 08-16</span>` / `<span class="c">推定</span>` / `<span class="c chk">要確認</span>` |
| 地図導線 | `<a class="map" href="https://www.google.com/maps/search/?api=1&amp;query=<URLエンコード>">地図</a>` |
| 注記（深刻度つき） | `.note.warn`（警告）/ `.note.keep`（維持）/ `.note.warm`（宿・推奨） |
| 旅程の行種別 | `tr.go`（移動）/ `tr.eat`（食事）/ `tr.in`（宿にいる） |

**左罫（`border-left`）は深刻度を符号化する箇所だけに使う。**装飾で足さない。

## 内容側の決まり

- 事実には必ず確度バッジを付ける。営業時間・料金・空室は**推測で埋めない**。
- 宿や施設を載せる前に**営業しているか確認する**。過去に、閉館済みの宿が比較サイトに
  残っていて危うく提案しかけた（ホテル海風土／2025年1月閉館）。
- 数値（費用合計・運転時間・図の比率）は**電卓で検算してから書く**。
  切り下げ・切り上げで予算線をまたぐことがある。
