# 2026-
旅行しおり用

しおり本体は `docs/index.html`（1ファイル・ビルド不要）。

## Cloudflare で公開する

`wrangler.jsonc` が `docs/` をそのまま配信する設定になっている（Cloudflare Workers の静的アセット配信・無料枠で足りる）。

### 初回だけ（Cloudflare ダッシュボードで行う）

1. https://dash.cloudflare.com/ にログイン（アカウントが無ければ無料で作成）。
2. 左メニュー **Compute (Workers) → Workers & Pages** → **Create** → **Import a repository**。
3. GitHub を連携し、`junk6-wq/2026nenmatu` を選ぶ。
4. 設定はこれだけ確認して **Deploy**：
   - Project name: `matsushima-shiori`（`wrangler.jsonc` の `name` と揃える）
   - Production branch: `main`
   - Build command: **空欄**
   - Deploy command: `npx wrangler deploy`（既定値のまま）
   - Root directory: `/`（既定値のまま）
5. 数十秒で `https://matsushima-shiori.<アカウント名>.workers.dev` に公開される。

以後は `main` に push / マージするたびに自動で再公開される。
`main` 以外のブランチの push ではプレビュー URL が作られる。

### 任意

- **見られる人を限定したい**：Workers & Pages → プロジェクト → Settings → Domains & Routes で
  workers.dev の **Cloudflare Access** を有効にし、許可するメールアドレスを登録する（50人まで無料）。
- **独自ドメイン**：同じ画面の **Add → Custom domain**（ドメインが Cloudflare 管理下にある必要あり）。
- **検索に載せたい**：既定では `docs/_headers` で `noindex` にしている。載せるならその行を消す。

### 手元から直接出す場合

```bash
npx wrangler login     # ブラウザで Cloudflare にログイン
npx wrangler deploy    # docs/ を公開
npx wrangler dev       # http://localhost:8787 で確認
```
