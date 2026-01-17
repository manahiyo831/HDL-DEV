# 新しいシミュレーションを実行する手順

このドキュメントでは、ModelSim GUIが起動中に、新しいHDLモジュールをコンパイルしてシミュレーションする手順を説明します。

## 前提条件

- ModelSim GUIが起動済み
- ソケットサーバーが動作中（ポート12345）
- Pythonクライアントから接続可能

## 方法1: Pythonから自動実行（推奨）

### ステップバイステップで実行

```python
from scripts.modelsim_client import ModelSimClient
import time

client = ModelSimClient(port=12345)
client.connect(max_retries=3, retry_delay=1.0)

# Step 1: 既存のシミュレーションを終了
client.execute_tcl('quit -sim')
time.sleep(0.5)

# Step 2: 新しい設計ファイルをコンパイル
client.execute_tcl('vlog -work work ../hdl/design/your_module.v')
time.sleep(0.5)

# Step 3: テストベンチをコンパイル
client.execute_tcl('vlog -work work ../hdl/testbench/your_module_tb.v')
time.sleep(0.5)

# Step 4: 新しいシミュレーションを開始
client.execute_tcl('vsim work.your_module_tb')
time.sleep(0.5)

# Step 5: $finish時の動作を設定
client.execute_tcl('onfinish stop')

# Step 6: 波形設定
client.execute_tcl('view wave')
client.execute_tcl('add wave -r /*')

# Step 7: シミュレーション実行
client.execute_tcl('run 10ms')  # 時間は適宜調整

# Step 8: 波形を表示
client.refresh_waveform()

client.disconnect()
```

### 一括実行（簡単版）

```python
from scripts.modelsim_client import ModelSimClient

client = ModelSimClient(port=12345)
client.connect()

# すべてのコマンドを一度に実行
commands = '''
quit -sim
vlog -work work ../hdl/design/your_module.v
vlog -work work ../hdl/testbench/your_module_tb.v
vsim work.your_module_tb
onfinish stop
view wave
add wave -r /*
run 10ms
wave zoom full
view wave
raise .main_pane.wave
'''

result = client.execute_tcl(commands)
client.disconnect()
```

## 方法2: ModelSim Transcriptで手動実行

ModelSimのTranscriptウィンドウ（下部のコマンド入力エリア）で、以下を1行ずつ実行：

```tcl
# 1. 既存のシミュレーションを終了
quit -sim

# 2. 新しいファイルをコンパイル
vlog -work work ../hdl/design/your_module.v
vlog -work work ../hdl/testbench/your_module_tb.v

# 3. 新しいシミュレーションを開始
vsim work.your_module_tb

# 4. $finish時の動作設定
onfinish stop

# 5. 波形設定
view wave
add wave -r /*
configure wave -namecolwidth 250
configure wave -valuecolwidth 100
configure wave -timelineunits ns

# 6. シミュレーション実行
run 10ms

# 7. 波形を全体表示
wave zoom full
view wave
raise .main_pane.wave
```

## 方法3: ModelSimControllerの高レベルAPI

```python
from scripts.modelsim_controller import ModelSimController
from scripts.modelsim_client import ModelSimClient
from pathlib import Path

# 既存のModelSimに接続
controller = ModelSimController(Path('.'))
controller.client = ModelSimClient(port=12345)
controller.client.connect()

# 新しいファイルを設定
controller.design_files = [Path('hdl/design/your_module.v')]
controller.testbench_file = Path('hdl/testbench/your_module_tb.v')

# コンパイル・実行・解析
result = controller.quick_recompile_and_run(sim_time='10ms')

# 結果解析
analysis = controller.analyze_simulation(verbose=True)

if analysis['success']:
    print('✓ Simulation successful!')
else:
    print('✗ Errors detected')

controller.disconnect()
```

## 結果の確認方法

### 1. Transcriptファイルから直接確認

```python
from pathlib import Path

transcript = Path('sim/transcript').read_text(encoding='utf-8', errors='ignore')
lines = transcript.splitlines()

# 最後の50行を表示
for line in lines[-50:]:
    print(line)
```

### 2. 自動解析

```python
from scripts.modelsim_controller import ModelSimController
from pathlib import Path

controller = ModelSimController(Path('.'))

# 最新のシミュレーション結果を解析
analysis = controller.analyze_simulation(verbose=True, recent_only=True)

if analysis['success']:
    print('✓ Test PASSED')
    if analysis['test_results']['found']:
        print(f'  {analysis["test_results"]["message"]}')
else:
    print('✗ Test FAILED or Errors')
    for error in analysis['errors']['errors'][:5]:
        print(f'  - {error}')
```

## トラブルシューティング

### エラー: "can not find channel"

既存のシミュレーションが異常終了した場合、ソケット接続がクリーンアップされていない可能性があります。

**解決方法:**
1. ModelSimを完全に閉じる
2. 再度起動して、ソケットサーバーを開始

### 古いモジュールが実行される

`quit -sim` を実行して、既存のシミュレーションを確実に終了してください。

### コンパイルエラー

パスが正しいか確認：
- ModelSimは `sim/` ディレクトリから実行される
- 設計ファイルは `../hdl/design/` からの相対パス
- テストベンチは `../hdl/testbench/` からの相対パス

## 注意事項

- `quit -sim` を実行しないと、新しいモジュールがロードされません
- パスは必ず forward slash (`/`) を使用
- `onfinish stop` を設定しないと、`$finish` 時にダイアログが表示されます
- シミュレーション時間は、テストベンチの内容に応じて調整してください

## 例: Pulse Generator

```python
# Pulse Generatorの例（実際に成功した手順）
from scripts.modelsim_client import ModelSimClient
import time

client = ModelSimClient(port=12345)
client.connect()

# Step by step
client.execute_tcl('quit -sim')
time.sleep(0.5)

client.execute_tcl('vlog -work work ../hdl/design/pulse_generator.v')
time.sleep(0.5)

client.execute_tcl('vlog -work work ../hdl/testbench/pulse_generator_tb.v')
time.sleep(0.5)

client.execute_tcl('vsim work.pulse_generator_tb')
time.sleep(0.5)

client.execute_tcl('onfinish stop')
client.execute_tcl('view wave')
client.execute_tcl('add wave -r /*')

# 3.5ms実行（3つのパルスを検出するため）
client.execute_tcl('run 3.5ms')

# 波形を表示
client.refresh_waveform()

client.disconnect()

# 結果確認
from scripts.modelsim_controller import ModelSimController
from pathlib import Path

controller = ModelSimController(Path('.'))
analysis = controller.analyze_simulation(verbose=True)

# 結果: TEST_RESULT: PASS - Pulse generator is functioning correctly
```

---

最終更新: 2026-01-14
