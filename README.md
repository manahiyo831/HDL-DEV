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

- **ModelSim**: Intel FPGA Edition 20.1 以降
  - インストールパス: `C:\intelFPGA\20.1\modelsim_ase\win32aloem`
- **Python**: 3.7 以降

## セットアップ / Setup

### リポジトリのクローン

このリポジトリは `.claude/skills/` にシンボリックリンクを含んでいます。

**Windows環境:**
```bash
# 1. Git設定（初回のみ）
git config --global core.symlinks true

# 2. 開発者モードを有効化（推奨）
# 設定 → システム → 開発者向け → 「開発者モード」をON

# 3. クローン
git clone https://github.com/manahiyo831/HDL-DEV.git
cd HDL-DEV
```

**注意:** Windows開発者モードが無効の場合、管理者権限でGit操作を実行してください。
詳細は [SYMLINK_SETUP.md](SYMLINK_SETUP.md) を参照してください。

**Linux/Mac環境:**
```bash
git clone https://github.com/manahiyo831/HDL-DEV.git
cd HDL-DEV
```

### 依存関係のインストール

```bash
pip install -r requirements.txt
```

## 使い方

### 1. ソケット通信で高速イテレーション（推奨・NEW!）

**ModelSimを起動したまま** Pythonから制御することで、HDL修正後の再シミュレーションが超高速に。

#### 初回起動

**注意:** スクリプトはSKILL内に配置されているため、Pythonパスの調整が必要です：

```python
from pathlib import Path
import sys

# SKILLスクリプトへのパスを追加
sys.path.insert(0, str(Path(".claude/skills/modelsim-hdl-dev/scripts")))

from modelsim_controller import ModelSimController

# コントローラーを初期化
controller = ModelSimController(Path.cwd())

# ModelSim GUIをソケットサーバー付きで起動（一度だけ）
controller.start_gui_with_server(
    design_files=[Path("hdl/design/counter.v")],
    testbench_file=Path("hdl/testbench/counter_tb.v"),
    top_module="counter_tb",
    sim_time="1us"
)

# ModelSim GUIが開いて波形表示、ソケットサーバーが起動します
```

#### HDL修正後の再シミュレーション

HDLファイルを修正したら、**ModelSimを再起動せずに**：

```python
# 再コンパイル→再起動→実行→波形更新を一括実行
result = controller.quick_recompile_and_run(sim_time="1us")

if result['recompile']['success']:
    print("✓ SUCCESS: シミュレーション完了")
else:
    print("✗ FAILED: コンパイルエラー")
    for error in result['recompile']['errors']:
        print(f"  - {error}")
```

#### より細かい制御

```python
# 個別コマンド
controller.recompile(design_files=[...], testbench_file=...)
controller.restart()
controller.run("1us")
controller.refresh_waveform()

# 任意のTCLコマンド実行
controller.execute_tcl("wave zoom range 0ns 500ns")

# 終了時
controller.disconnect()
```

**利点:**
- ✓ ModelSim再起動不要で超高速イテレーション
- ✓ Pythonから柔軟に制御可能
- ✓ Claudeとの協働に最適
- ✓ 波形をリアルタイムで確認しながら開発

---

### 2. SKILLを使用したCLI方式（推奨）

modelsim-hdl-dev SKILLを有効化して、CLIスクリプトを使用します。

詳細は `.claude/skills/modelsim-hdl-dev/SKILL.md` を参照してください。

```bash
# ModelSim起動
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"

# 高速イテレーション
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py
```

### 4. Claudeとの協働ワークフロー

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

## ModelSimRunner API

### `__init__(modelsim_path: str)`
ModelSimランナーを初期化します。

**引数:**
- `modelsim_path`: ModelSimのインストールディレクトリ（デフォルト: `C:/intelFPGA/20.1/modelsim_ase/win32aloem`）

### `simulate(design_files, testbench_file, top_module, sim_time)`
完全な自動シミュレーションフローを実行します。

**引数:**
- `design_files`: 設計ファイルのリスト
- `testbench_file`: テストベンチファイル
- `top_module`: トップモジュール名
- `sim_time`: シミュレーション時間（例: "1us", "10ns", "100ps"）

**戻り値:**
```python
{
    "overall_success": bool,          # 全体の成功/失敗
    "tcl_script": str,                # 使用されたTCLスクリプト
    "log_file": str,                  # ログファイルパス
    "stdout": str,                    # 標準出力
    "stderr": str,                    # 標準エラー出力
    "log_analysis": {
        "success": bool,              # シミュレーション成功
        "errors": list,               # エラーメッセージ
        "warnings": list,             # 警告メッセージ
        "display_outputs": list,      # $display出力
        "raw_log": str                # 生ログ
    }
}
```

### `print_result(result)`
シミュレーション結果を見やすく表示します。

---

## ModelSimController API (NEW!)

### `__init__(project_root, modelsim_path, server_port)`
ModelSimコントローラーを初期化します。

**引数:**
- `project_root`: プロジェクトルートディレクトリ (例: `Path("d:/Claude/Ralph_loop")`)
- `modelsim_path`: ModelSimのインストールディレクトリ（デフォルト: `C:/intelFPGA/20.1/modelsim_ase/win32aloem`）
- `server_port`: ソケットサーバーのポート番号（デフォルト: 12345）

### `start_gui_with_server(design_files, testbench_file, top_module, sim_time, auto_connect, connect_delay)`
ModelSim GUIをソケットサーバー付きで起動します。

**引数:**
- `design_files`: 設計ファイルのリスト
- `testbench_file`: テストベンチファイル
- `top_module`: トップモジュール名
- `sim_time`: 初回シミュレーション時間（デフォルト: "1us"）
- `auto_connect`: 起動後に自動接続するか（デフォルト: True）
- `connect_delay`: 接続前の待機時間（秒）（デフォルト: 3.0）

**戻り値:** True（成功）/ False（失敗）

### `quick_recompile_and_run(design_files, testbench_file, sim_time, restart, refresh_wave)`
再コンパイル→再起動→実行→波形更新を一括実行します。

**引数:**
- `design_files`: 設計ファイル（Noneの場合は保存済みのものを使用）
- `testbench_file`: テストベンチファイル（Noneの場合は保存済みのものを使用）
- `sim_time`: シミュレーション時間（デフォルト: "1us"）
- `restart`: 再起動するか（デフォルト: True）
- `refresh_wave`: 波形を更新するか（デフォルト: True）

**戻り値:**
```python
{
    "success": bool,
    "message": str,
    "recompile": {...},    # 再コンパイル結果
    "restart": {...},      # 再起動結果
    "run": {...},          # 実行結果
    "wave_refresh": {...}  # 波形更新結果
}
```

### その他のメソッド
- `connect(max_retries, retry_delay)`: サーバーに接続
- `disconnect()`: サーバーから切断
- `is_connected()`: 接続状態を確認
- `ping()`: サーバーに ping
- `recompile(design_files, testbench_file)`: 再コンパイル
- `restart()`: シミュレーション再起動
- `run(time)`: シミュレーション実行
- `refresh_waveform()`: 波形更新
- `execute_tcl(tcl_code)`: 任意のTCLコマンド実行
- `shutdown_server()`: サーバー停止（ModelSimは継続）

---

## ModelSimClient API (NEW!)

低レベルAPI。より細かい制御が必要な場合に使用。

### 主要メソッド
- `connect(max_retries, retry_delay)`: サーバーに接続（リトライあり）
- `disconnect()`: 切断
- `ping()`: 接続確認
- `recompile(design_files, testbench_file)`: 再コンパイル
- `restart_simulation()`: シミュレーション再起動
- `run_simulation(time)`: シミュレーション実行
- `refresh_waveform()`: 波形更新
- `execute_tcl(tcl_code)`: TCLコマンド実行
- `shutdown_server()`: サーバー停止

**使用例:**
```python
import sys
from pathlib import Path

# SKILLスクリプトへのパスを追加
sys.path.insert(0, str(Path(".claude/skills/modelsim-hdl-dev/scripts")))

from modelsim_client import ModelSimClient

with ModelSimClient(port=12345) as client:
    if client.ping():
        result = client.recompile(
            design_files=["hdl/design/counter.v"],
            testbench_file="hdl/testbench/counter_tb.v"
        )
        if result['success']:
            client.restart_simulation()
            client.run_simulation("1us")
            client.refresh_waveform()
```

---

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

### エラー: "ModelSim not found"
- ModelSimのインストールパスを確認してください
- `ModelSimRunner`の初期化時にパスを指定してください

### シミュレーションが失敗する
- ログファイルを確認: `results/logs/sim_*.log`
- トランスクリプトを確認: `sim/transcript`
- エラーメッセージを読んで、設計を修正してください

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
