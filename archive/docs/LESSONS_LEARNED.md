# ModelSim自動シミュレーション - 学習記録

このドキュメントは、ModelSim自動シミュレーション環境を構築する際に学んだこと、遭遇した問題、解決方法を記録しています。

## 構築したシステム

ClaudeがHDLコードを生成し、ModelSimで自動的にシミュレーションして結果を確認するループ環境。

```
Claude → HDL生成 → ModelSim実行 → 結果解析 → Claude → 修正 → ...
```

## 遭遇した問題と解決方法

### 0. TCL JSON変換エラーの修正 (2026-01-16)

**問題:**
`wave radix unsigned /pwm_generator_tb/duty` コマンドを実行した際、TCLソケットサーバーがJSON変換時にクラッシュする問題が発生しました。

**エラーメッセージ:**
```
Error: list element in quotes followed by ":" instead of space
    while executing
"llength $value"
    (procedure "dict_to_json" line 4)
```

**原因:**
`modelsim_socket_server.tcl` の `dict_to_json` プロシージャで、`llength $value` を実行する際に、コロン(`:`)を含む値（例: `"unsigned:/pwm_generator_tb/duty"`）が不正なTCLリスト形式として解釈され、エラーが発生していました。TCLのリストパーサーは、引用符で囲まれた要素の後にはスペースを期待しますが、コロンがあるとパースエラーになります。

**解決策:**
`dict_to_json` プロシージャで `llength` コマンドを `catch` ブロックで囲み、エラーを捕捉するようにしました。`llength` が失敗した場合は、その値を文字列として扱います。

```tcl
# 修正前
if {[llength $value] > 1} {

# 修正後
if {[catch {llength $value} len]} {
    # Invalid list format (e.g., contains unescaped colons)
    # Treat as plain string
    lappend parts "\"$key\": \"[escape_json_string $value]\""
} elseif {$len > 1} {
```

**教訓:**
- TCLの `llength` は、不正なリスト形式の値に対してエラーを投げる
- すべての外部入力に対しては `catch` でエラーハンドリングを行うべき
- `catch {command} result_var` パターンは、コマンドの成功/失敗とその結果を同時に取得できる

---

### 1. TCLスクリプトのエラーチェック構文

**問題:**
```tcl
if {$? != 0} {
    puts "ERROR: Design compilation failed"
    quit -f
}
```
このシェルスタイルの構文はModelSim TCLでは動作しない。
エラー: `unknown option "$"`

**解決方法:**
ModelSim TCLでは`catch`コマンドを使用してエラーをチェックする。

```tcl
if {[catch {vlog -work work design.v}]} {
    puts "ERROR: Design compilation failed"
    quit -f
}
```

**学習:**
- TCLのエラーハンドリングは`catch {コマンド}`で行う
- 戻り値は0（成功）または1（失敗）
- `$?`はシェルスクリプトの構文であり、TCLでは使えない

---

### 2. $finish実行時の終了ダイアログ

**問題:**
テストベンチで`$finish`を実行すると、ModelSim GUIが「終了しますか？」ダイアログを表示して、ユーザーの確認を待ってしまう。

**解決方法:**
シミュレーション開始後に`onfinish stop`コマンドを実行する。

```tcl
vsim work.counter_tb
onfinish stop  # $finish時に終了せず停止する
```

**学習:**
- `onfinish stop`: $finish時に停止（ダイアログなし）
- `onfinish exit`: $finish時に終了（デフォルト動作）
- `onfinish ask`: $finish時に確認ダイアログ表示

---

### 3. 波形ウィンドウが自動的に前面に来ない

**問題:**
シミュレーション完了後、波形ウィンドウが他のウィンドウの後ろに隠れてしまい、ユーザーが手動でタブを切り替える必要がある。

**解決方法:**
TCLスクリプトで波形ウィンドウを前面に持ってくるコマンドを実行。

```tcl
# 波形を全体表示
wave zoom full

# 波形ウィンドウを前面に表示
view wave
raise .main_pane.wave
```

**学習:**
- `view wave`: 波形ウィンドウをアクティブにする
- `raise .main_pane.wave`: 波形ペインを最前面に持ってくる
- `.main_pane.wave`はModelSim GUIのTk/Tclウィジェットパス

---

### 4. 信号の表示形式設定（2進数→10進数）

**問題:**
`configure wave -radix decimal`コマンドがエラーになる。
`radix`コマンドを波形追加後に実行しても表示形式が変わらない。

**試した解決方法（失敗）:**
```tcl
# エラーを回避するためcatchで囲む
catch {radix signal unsigned /counter_tb/dut/count}
```

**結果:**
- コマンドはエラーを出さずに実行された（戻り値1で成功）
- しかし、実際の波形表示は2進数のまま変わらなかった

**根本原因（判明）:**
ModelSimでは`radix`コマンドの実行タイミングが重要：
- **波形追加後に`radix`コマンドを実行しても効果なし**
- **表示形式は`add wave -radix <format>`で波形追加時に指定する必要がある**

**解決方法:**
```tcl
# ✓ 正しい方法: 波形追加時に形式を指定
add wave -radix unsigned /counter_tb/dut/count
add wave -radix hex /counter_tb/dut/addr
add wave -radix binary -r /*

# ✗ 間違った方法: 追加後に変更しようとする
add wave -r /*
radix -unsigned /counter_tb/dut/count  # 効果なし！
```

**フォーマット変更方法:**
追加後に形式を変えたい場合は、波形を削除して再追加が必要：
```tcl
delete wave *
add wave -radix unsigned /counter_tb/dut/count
add wave -r /*
wave zoom full
```

**実装された Python API:**
```python
# 方法1: 初期追加時に形式指定（推奨）
controller.add_waves_with_format(
    signal_formats={"/counter_tb/dut/count": "unsigned"},
    default_format="binary"
)

# 方法2: 追加後に形式変更（波形を再追加）
controller.change_wave_format({
    "/counter_tb/dut/count": "hex"
})

# 方法3: quick_recompile_and_run()で直接
controller.quick_recompile_and_run(sim_time="1us")
# ... 次に形式変更
controller.change_wave_format({"/counter_tb/dut/count": "unsigned"})
```

**利用可能な形式:**
- `binary` - 2進数（デフォルト）: 8'b00001010
- `hex` - 16進数: 8'h0A
- `unsigned` - 符号なし10進数: 10
- `signed` - 符号付き10進数: -6 or 10
- `octal` - 8進数: 8'o012
- `ascii` - ASCII文字: 'A'

**現在の状態:**
**✅ 解決済み（2026-01-14）**

以下の機能を`modelsim_controller.py`に実装：
- `add_waves_with_format()` - 波形追加時に形式指定
- `change_wave_format()` - 波形を削除して再追加
- `get_common_signal_formats()` - 利用可能な形式のリスト取得

**参考資料:**
- ModelSim User Manual - Wave Window Commands
- SKILLドキュメント: `references/api-reference.md`
- 実装例: `references/workflow-guide.md`

---

### 5. ログファイルの出力先

**問題:**
`-logfile`オプションでログファイルを指定しても、実際には`transcript`ファイルにしか出力されない。

**解決方法:**
`transcript file`コマンドを使用する。

```tcl
# シミュレーション開始後に実行
vsim work.counter_tb
transcript file /path/to/logfile.log
```

**学習:**
- `vsim -logfile`オプションは起動時のログのみ
- シミュレーション中のログは`transcript file`で設定
- デフォルトのtranscriptファイルは`sim/transcript`

---

### 6. パスのエスケープ（Windows環境）

**問題:**
Windowsのバックスラッシュ`\`がBash tool（Git Bash）で正しく処理されない。

**解決方法:**
Pythonスクリプト内でパスをforward slash `/`に変換する。

```python
# パスをModelSim用に変換
design_files_str = " ".join([str(f).replace("\\", "/") for f in design_files])
waveform_file_str = str(waveform_file).replace("\\", "/")
```

**学習:**
- ModelSimはWindows上でもforward slashを受け付ける
- Bash tool経由でコマンド実行する場合は特に重要
- Pythonの`Path`オブジェクトは`str()`で文字列化してから変換

---

## ベストプラクティス

### TCLスクリプトの構造

```tcl
# 1. ライブラリの作成・マッピング
if {[catch {vlib work}]} {
    echo "ERROR: Failed to create work library"
    return
}
vmap work work

# 2. コンパイル（エラーチェック付き）
if {[catch {vlog design.v}]} {
    echo "ERROR: Compilation failed"
    return
}

# 3. シミュレーション開始
vsim work.testbench

# 4. $finish時の動作設定
onfinish stop

# 5. 波形設定
view wave
add wave -r /*
configure wave -namecolwidth 200
configure wave -valuecolwidth 100
configure wave -timelineunits ns

# 6. シミュレーション実行
run 1us

# 7. 波形表示
wave zoom full
view wave
raise .main_pane.wave
```

### Pythonスクリプトのパス処理

```python
from pathlib import Path

# Pathオブジェクトを使う
project_root = Path(__file__).parent.parent
hdl_dir = project_root / "hdl" / "design"

# ModelSimに渡す際はforward slashに変換
hdl_dir_str = str(hdl_dir).replace("\\", "/")
```

### ディレクトリ構造

```
project/
├── hdl/
│   ├── design/        # 設計ファイル
│   └── testbench/     # テストベンチ
├── sim/               # ModelSim作業ディレクトリ
│   ├── work/          # コンパイル済みライブラリ
│   └── transcript     # デフォルトログ
├── scripts/           # 自動化スクリプト
│   ├── simulate_gui.py
│   ├── modelsim_runner.py
│   └── *.tcl          # 自動生成TCLスクリプト
└── results/
    ├── logs/          # ログファイル
    └── waveforms/     # 波形ファイル (.wlf)
```

---

## トラブルシューティングチェックリスト

### シミュレーションが起動しない

- [ ] ModelSimのパスが正しいか確認
- [ ] `vsim.exe`が存在するか確認
- [ ] PATHに追加されているか確認

### コンパイルエラー

- [ ] Verilogファイルの構文エラーをチェック
- [ ] ファイルパスが正しいか確認（forward slash使用）
- [ ] workライブラリが存在するか確認

### 波形が表示されない

- [ ] `add wave -r /*`が実行されているか確認
- [ ] `wave zoom full`が実行されているか確認
- [ ] `raise .main_pane.wave`が実行されているか確認
- [ ] Wave windowタブを手動でクリック

### ログファイルが見つからない

- [ ] `transcript file`コマンドでパス設定しているか
- [ ] デフォルトの`sim/transcript`を確認
- [ ] パスが正しいか確認（forward slash使用）

---

### 7. TCLソケットサーバーによる双方向通信

**課題:**
毎回ModelSimを再起動するのは時間がかかり、HDL開発のイテレーションが遅い。

**解決方法:**
TCLソケットサーバーをModelSim内で起動し、Pythonクライアントから動的にコマンドを送信できるようにする。

**実装:**

#### TCL側（サーバー）

```tcl
# ソケットサーバーの起動
proc start_socket_server {{port 12345}} {
    global server_socket
    set server_socket [socket -server handle_client $port]
    echo "Socket server started on port $port"
}

# クライアント接続処理
proc handle_client {sock addr port} {
    fconfigure $sock -buffering line -blocking 0 -encoding utf-8
    fileevent $sock readable [list handle_command $sock]
}

# コマンド処理
proc handle_command {sock} {
    if {[eof $sock]} {
        close $sock
        return
    }
    gets $sock line
    # JSON形式のコマンドをパース
    set result [parse_json_command $line]
    set command [dict get $result command]
    set params [dict get $result params]

    # コマンド実行
    set response [execute_command $command $params]

    # JSON形式で返送
    puts $sock [dict_to_json $response]
    flush $sock
}
```

#### Python側（クライアント）

```python
import socket
import json

class ModelSimClient:
    def connect(self, host="localhost", port=12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def send_command(self, command, params=None):
        message = {
            "command": command,
            "params": params or {}
        }
        self.socket.sendall((json.dumps(message) + "\n").encode('utf-8'))
        response = self.socket.recv(4096).decode('utf-8')
        return json.loads(response)

    def recompile(self, design_files, testbench_file):
        return self.send_command("recompile", {
            "design_files": design_files,
            "testbench_file": testbench_file
        })
```

**学習:**
- TCLの`socket -server`でTCPサーバーを作成
- `fconfigure`で非ブロッキング、行バッファリング、UTF-8エンコーディング設定
- `fileevent`でデータ受信時のコールバック設定
- `eof`でクライアント切断を検知
- Pythonの`socket`ライブラリでクライアント実装
- JSON形式でコマンド/レスポンスをやり取り
- `\n`を区切り文字として使用（行バッファリング）

**実装したコマンド:**
- `ping`: 接続確認
- `recompile`: 設計ファイルの再コンパイル
- `restart`: シミュレーション再起動
- `run`: シミュレーション実行
- `wave_refresh`: 波形更新とズーム
- `exec_tcl`: 任意のTCLコマンド実行
- `shutdown`: サーバー停止

**利点:**
- ModelSim再起動不要で超高速イテレーション
- Pythonから柔軟に制御可能
- リアルタイムで波形を確認しながら開発
- Claudeとの協働に最適

**注意点:**
- サーバーはlocalhost（127.0.0.1）のみ許可（セキュリティ）
- クライアント接続前にサーバーが起動している必要がある
- リトライロジックで接続待機（最大10回、1秒間隔）
- タイムアウト設定（デフォルト30秒）

---

### 8. TCL JSON変換のboolean判定エラー

**問題:**
TCLの`dict_to_json`関数で空リスト`{}`をboolean値として誤検出し、エラーが発生。

```tcl
# エラー: expected boolean value but got ""
set response [dict create success true errors {} warnings {}]
set json [dict_to_json $response]
```

**原因:**
- `string is boolean $value`が空リスト`{}`を評価しようとしてエラー
- 空文字列`""`もboolean判定でエラーになる
- 空リストのチェックがboolean判定の後にあった

**解決方法:**
1. **空リストを先にチェック**（boolean判定の前に）
2. **`-strict`フラグを使用**して厳密なboolean判定
3. **空文字列をチェック**してからboolean評価

```tcl
proc dict_to_json {d} {
    set parts {}
    dict for {key value} $d {
        if {[string is list $value] && [llength $value] > 0} {
            # 非空リスト → JSON配列
            set items {}
            foreach item $value {
                lappend items "\"[escape_json_string $item]\""
            }
            lappend parts "\"$key\": \[[join $items ", "]\]"
        } elseif {[llength $value] == 0} {
            # 空リスト → [] (boolean判定の前に！)
            lappend parts "\"$key\": \[\]"
        } elseif {$value != "" && [string is boolean -strict $value]} {
            # boolean値 (-strictで厳密判定)
            lappend parts "\"$key\": [expr {$value ? "true" : "false"}]"
        } else {
            # 文字列
            lappend parts "\"$key\": \"[escape_json_string $value]\""
        }
    }
    return "\{[join $parts ", "]\}"
}
```

**学習:**
- TCLの`string is boolean`は空リストや空文字列でエラーになる
- `-strict`フラグで厳密な型チェックが可能
- 条件判定の順序が重要（空チェック → 型チェック → デフォルト）
- `[llength $value] == 0`で空リスト判定
- 空でないことを確認してから型判定を行う

**検証結果:**
- ✓ Ping成功
- ✓ Recompile成功
- ✓ Restart成功
- ✓ Run成功
- ✓ Wave refresh成功
- ✓ HDLエラー時も通信維持
- ✓ 完全なワークフロー動作確認

---

### 9. Transcript解析による自律的結果確認

**課題:**
Claudeはシミュレーション結果を直接確認できないため、自律的な開発ループが回せない。

**解決方法:**
ModelSimの`sim/transcript`ファイルを読み取り、エラーやテスト結果を解析する機能を`ModelSimController`に実装。

**実装した機能:**

1. **Transcript読み取り**: `read_transcript(lines=None)` - 全体または最後のN行
2. **エラー検出**: `check_for_errors()` - コンパイル・シミュレーションエラー検出
3. **テスト結果検出**: `find_test_results()` - `TEST_RESULT:`マーカー検出
4. **統合解析**: `analyze_simulation()` - 全体の成功/失敗判定

**テストベンチの規約:**
```verilog
$display("TEST_RESULT: PASS - Counter is functioning (final count: %d)", count);
$display("TEST_RESULT: FAIL - Counter did not increment");
```

**学習:**
- ModelSimはすべての出力を`sim/transcript`に記録
- `read_text(encoding='utf-8', errors='ignore')`でバイナリも対処
- 最後の100行だけ解析することで古いエラーを無視（`recent_only=True`）
- `$display()`でTranscriptに出力すれば、専用ファイル不要

**利点:**
- ✅ Claudeが自律的に結果確認
- ✅ エラー検出 → 修正 → 再実行の自動ループ
- ✅ テストPass/Fail自動判定
- ✅ 完全な自律HDL開発サイクル

**検証結果:**
```
✓ No compilation/simulation errors
✓ Test Results: PASS - Counter is functioning (final count: 10)
Overall: SUCCESS
```

**完成した自律ループ:**
```python
# 1. HDL生成 (Claudeが書く)
# 2. シミュレーション実行
controller.quick_recompile_and_run(sim_time='1us')
# 3. 結果確認
analysis = controller.analyze_simulation(verbose=True)
# 4. 判定
if analysis['success']:
    print('✓ Test passed!')
else:
    # エラーを修正して再実行
    errors = analysis['errors']['errors']
    # Claude が errors を解析して修正...
```

---

## 未解決の課題

### 🔴 課題1: 信号の10進数表示

**現象:**
count信号が2進数表示のままで、10進数に変更できない。

**試したこと:**
```tcl
catch {radix signal unsigned /counter_tb/dut/count}
```

**状態:**
コマンドは成功するが、表示は変わらない。

**次のステップ:**
1. `add wave -radix unsigned`で信号追加時に指定
2. 信号パスの確認（階層が正しいか）
3. ModelSimドキュメントで正しい構文を確認
4. GUI操作で手動設定した後、transcriptを確認

---

## 参考リンク

- ModelSim Command Reference: TCLコマンドの完全リファレンス
- ModelSim User Manual: Chapter 6 - Waveform Window
- TCL Tutorial: `catch`コマンドの使い方

---

## 更新履歴

- 2026-01-14: 初版作成
  - TCLエラーハンドリング
  - $finish時の動作制御
  - 波形ウィンドウの前面表示
  - 信号表示形式の課題を記録
- 2026-01-14: ソケット通信機能追加
  - TCLソケットサーバー実装
  - Pythonソケットクライアント実装
  - 高レベルコントローラーAPI実装
  - ModelSim再起動不要の高速イテレーション実現
  - 双方向通信プロトコル（JSON形式）
  - リトライロジックとエラーハンドリング
- 2026-01-14: TCL JSON変換バグ修正
  - `dict_to_json`の空リスト判定エラーを修正
  - boolean型チェックに`-strict`フラグ追加
  - 条件判定の順序を最適化（空チェック → 型チェック）
  - 全コマンドの動作確認完了
  - HDLエラー時の通信耐性を確認
  - システムが本番利用可能な状態に
- 2026-01-14: Transcript解析機能実装（自律開発ループ完成）
  - `read_transcript()`: Transcriptファイル読み取り
  - `check_for_errors()`: エラー・警告検出
  - `find_test_results()`: TEST_RESULTマーカー検出
  - `analyze_simulation()`: 統合解析と成功/失敗判定
  - テストベンチに`TEST_RESULT:`マーカー追加
  - `ModelSimController`のパス変換修正（相対パス + forward slash）
  - 最後の100行のみ解析で古いエラーを無視
  - **完全な自律HDL開発ループが実現**
  - Claudeがコード生成 → シミュレーション → 結果確認 → 修正のサイクルを自律的に実行可能に
  - 実例: Pulse Generator（1MHz, 1msパルス）を完全自律で実装・検証成功
  - 新しいモジュール実行手順をドキュメント化（docs/HOW_TO_RUN_NEW_SIMULATION.md）
