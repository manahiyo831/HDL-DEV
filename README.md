# HDL Auto-Simulation with Claude

ClaudeがHDLコードを生成し、ModelSimで自動的にシミュレーションして結果を確認するループ環境


## 概要

このプロジェクトは、以下のワークフローを自動化します：

```
Claude → HDL生成 → ModelSim実行 → 結果解析 → Claude → 修正 → ...
```

## ディレクトリ構造

```
HDL-DEV/
├── .claude/skills/
│   └── modelsim-hdl-dev/   # SKILL (全自動化スクリプト含む)
├── hdl/                    # HDL設計ファイル
│   ├── design/             # 設計ファイル (.v, .vhd)
│   └── testbench/          # テストベンチファイル
└── sim/                    # ModelSim作業ディレクトリ
    ├── work/               # コンパイル済みライブラリ
    └── transcript          # ModelSim実行ログ
```

## 必要な環境

- **OS**: Windows 11
  - 本プロジェクトは Windows 11 環境で開発・テストされています
- **ModelSim**: Intel FPGA Starter Edition 20.1 (2020.1) 以降
  - インストールパス: `C:\intelFPGA\20.1\modelsim_ase\win32aloem`
  - 本プロジェクトでは Intel FPGA Starter Edition 20.1 を使用
- **Python**: 3.7 以降

## セットアップ / Setup

### リポジトリのクローン

```bash
git clone https://github.com/manahiyo831/HDL-DEV.git
cd HDL-DEV
```

### 依存関係のインストール

```bash
pip install -r requirements.txt
```

## 使い方

### 1. SKILLを使用したCLI方式（推奨）

modelsim-hdl-dev SKILLを有効化して、CLIスクリプトを使用します。

**完全なドキュメント:** `.claude/skills/modelsim-hdl-dev/SKILL.md`

#### クイックスタート

```bash
# Step 1: ModelSim起動（初回のみ）
python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim_server.py

# Step 2: 接続確認
python .claude/skills/modelsim-hdl-dev/scripts/connection_check.py

# Step 3: デザインロード
python .claude/skills/modelsim-hdl-dev/scripts/load_module.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"

# Step 4: HDL修正後の高速イテレーション
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50

# Step 5: 波形解析
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "counter_tb/count" "unsigned"
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py "wave"
```

**利点:**
- ✓ ModelSim再起動不要で超高速イテレーション
- ✓ シンプルなCLIインターフェース
- ✓ Claudeとの協働に最適
- ✓ 波形をリアルタイムで確認しながら開発

---

### 2. Claudeとの協働ワークフロー

1. **要件を伝える**
   - 例: "8ビットの全加算器を作成してシミュレーションしてください"

2. **Claudeが設計を生成**
   - `hdl/design/adder.v` に設計ファイルを作成
   - `hdl/testbench/adder_tb.v` にテストベンチを作成

3. **Claudeが自動でGUIシミュレーションを起動**
   - SKILLのCLIスクリプトを使用（詳細はSKILL.md参照）
   - ModelSim GUIが開き、波形が表示されます

4. **波形を見ながら確認**
   - リアルタイムで信号の動作を確認
   - 必要なら追加シミュレーション: `run 1us`
   - 問題があればClaudeにフィードバック

5. **修正と再シミュレーション**
   - Claudeが設計を修正
   - GUIで `restart -f` してから `run 1us` で再実行


## サンプルコード

### カウンタ設計 ([hdl/design/counter.v](hdl/design/counter.v))

8ビットカウンタの実装例が含まれています。
- クロック、リセット、イネーブル信号
- 同期リセット
- カウント出力

### カウンタテストベンチ ([hdl/testbench/counter_tb.v](hdl/testbench/counter_tb.v))

テストベンチの書き方の例：
- クロック生成
- リセットシーケンス
- イネーブル制御
- 結果の検証（PASS/FAIL判定）
- タイムアウト保護

## トラブルシューティング

### シミュレーションが失敗する
- トランスクリプトを確認: `sim/transcript`
- エラーメッセージを読んで、設計を修正してください
- または: `python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50`

### 波形ファイルを見たい
波形ファイルの表示はSKILL内のスクリプトを使用:
```bash
python .claude/skills/modelsim-hdl-dev/scripts/view_waveform.py
python .claude/skills/modelsim-hdl-dev/scripts/view_waveform.py --list
```

詳細はSKILL.mdを参照してください。

**波形ビューアの使い方:**
- すべての信号が自動的に追加されます
- `Ctrl+0` でズームフル
- 波形をクリックしてカーソル移動
- 右クリックメニューで信号の表示形式変更（16進数、2進数など）

## ログファイルの読み方

### 成功例
```
# === Counter Testbench Start ===
# ...
# PASS: Counter is functioning
# ** Note: $finish
# Errors: 0, Warnings: 0
```

### 失敗例
```
# ** Error: (vlog-xxx) ...
# Errors: 1, Warnings: 0
```

## Tips

1. **シミュレーション時間の設定**
   - 短すぎると検証が不十分
   - 長すぎるとシミュレーションに時間がかかる
   - テストベンチに`$finish`を入れて自動終了させる

2. **テストベンチの書き方**
   - PASSの条件を明確に
   - エラーケースもテスト
   - タイムアウトを設定

3. **デバッグ**
   - `$display`で中間結果を出力
   - 波形ファイルを確認
   - ログファイルの全体を読む

## ライセンス

このプロジェクトはClaudeとの協働作業の一環として作成されました。
