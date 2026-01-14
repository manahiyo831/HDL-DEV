"""
ModelSim GUIでインタラクティブにシミュレーションを実行するスクリプト
波形をリアルタイムで確認しながらシミュレーションできます
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List


class ModelSimGUIRunner:
    """ModelSim GUIでシミュレーションを実行するクラス"""

    def __init__(self, modelsim_path: str = "C:/intelFPGA/20.1/modelsim_ase/win32aloem"):
        """
        Args:
            modelsim_path: ModelSimのインストールディレクトリ
        """
        self.modelsim_path = Path(modelsim_path)
        self.vsim_exe = self.modelsim_path / "vsim.exe"

        # プロジェクトのルートディレクトリ
        self.project_root = Path(__file__).parent.parent
        self.hdl_dir = self.project_root / "hdl"
        self.sim_dir = self.project_root / "sim"
        self.scripts_dir = self.project_root / "scripts"
        self.results_dir = self.project_root / "results"

        # ModelSimの実行可能ファイルが存在するか確認
        if not self.vsim_exe.exists():
            raise FileNotFoundError(f"ModelSim not found at {self.vsim_exe}")

    def create_gui_tcl_script(self,
                              design_files: List[str],
                              testbench_file: str,
                              top_module: str,
                              sim_time: str = "1us") -> str:
        """
        GUI用のTCLスクリプトを生成

        Args:
            design_files: 設計ファイルのリスト
            testbench_file: テストベンチファイル
            top_module: トップモジュール名
            sim_time: シミュレーション時間（例: "1us", "10ns"）

        Returns:
            生成されたTCLスクリプトのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tcl_file = self.scripts_dir / f"sim_gui_{timestamp}.tcl"
        waveform_file = self.results_dir / "waveforms" / f"sim_{timestamp}.wlf"

        # パスをModelSim用に変換（forward slash + sim/からの相対パス）
        # ModelSimはsim/ディレクトリで実行されるため、プロジェクトルートへは ../
        design_files_rel = []
        for f in design_files:
            p = Path(f)
            # 絶対パスの場合は相対パスに変換
            if p.is_absolute():
                try:
                    rel = p.relative_to(self.project_root)
                    design_files_rel.append(f"../{str(rel).replace(chr(92), '/')}")
                except ValueError:
                    # プロジェクトルート外のファイルの場合は絶対パス
                    design_files_rel.append(str(p).replace("\\", "/"))
            else:
                # 既に相対パスの場合
                design_files_rel.append(f"../{str(p).replace(chr(92), '/')}")
        design_files_str = " ".join(design_files_rel)

        # テストベンチも同様
        tb_path = Path(testbench_file)
        if tb_path.is_absolute():
            try:
                tb_rel = tb_path.relative_to(self.project_root)
                testbench_str = f"../{str(tb_rel).replace(chr(92), '/')}"
            except ValueError:
                testbench_str = str(tb_path).replace("\\", "/")
        else:
            testbench_str = f"../{str(tb_path).replace(chr(92), '/')}"

        waveform_file_str = str(waveform_file).replace("\\", "/")
        sim_dir_str = str(self.sim_dir).replace("\\", "/")

        tcl_content = f"""# Auto-generated TCL script for ModelSim GUI
# Generated at {timestamp}

# コンソールメッセージ
echo "========================================"
echo "ModelSim GUI Simulation"
echo "========================================"

# ワークライブラリの作成
if {{[file exists {sim_dir_str}/work]}} {{
    catch {{vdel -all}}
}}
if {{[catch {{vlib {sim_dir_str}/work}}]}} {{
    echo "ERROR: Failed to create work library"
    return
}}
if {{[catch {{vmap work {sim_dir_str}/work}}]}} {{
    echo "ERROR: Failed to map work library"
    return
}}

# 設計ファイルのコンパイル
echo "Compiling design files..."
if {{[catch {{vlog -work work {design_files_str}}}]}} {{
    echo "ERROR: Design compilation failed"
    return
}}
echo "Design compilation: OK"

# テストベンチのコンパイル
echo "Compiling testbench..."
if {{[catch {{vlog -work work {testbench_str}}}]}} {{
    echo "ERROR: Testbench compilation failed"
    return
}}
echo "Testbench compilation: OK"

# シミュレーションの開始（GUIモード）
echo "Starting simulation..."
if {{[catch {{vsim -wlf {waveform_file_str} work.{top_module}}}]}} {{
    echo "ERROR: Failed to start simulation"
    return
}}

# $finish時に停止する（終了しない）
onfinish stop

# 波形ウィンドウを開く
view wave

# すべての信号を波形に追加
echo "Adding signals to wave window..."
add wave -r /*

# 数値信号を10進数表示に設定
# radixコマンドを使用（エラー回避のためcatchで囲む）
catch {{radix signal unsigned /counter_tb/dut/count}}

# 波形表示の設定
configure wave -namecolwidth 200
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 1
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -timelineunits ns

# Objectsウィンドウ、Waveウィンドウを整理
view structure
view signals

# シミュレーション実行
echo "Running simulation for {sim_time}..."
run {sim_time}

# 波形を全体表示
wave zoom full

# 波形ウィンドウを前面に表示
view wave
raise .main_pane.wave

echo "========================================"
echo "Simulation completed"
echo "========================================"
echo ""
echo "Available commands:"
echo "  run <time>      - Continue simulation (e.g., run 1us)"
echo "  restart -f      - Restart simulation"
echo "  wave zoom full  - Zoom to full range"
echo "  wave zoom in    - Zoom in"
echo "  wave zoom out   - Zoom out"
echo "========================================"
"""

        with open(tcl_file, 'w', encoding='utf-8') as f:
            f.write(tcl_content)

        return str(tcl_file)

    def create_gui_tcl_script_with_server(self,
                                           design_files: List[str],
                                           testbench_file: str,
                                           top_module: str,
                                           sim_time: str = "1us",
                                           server_port: int = 12345) -> str:
        """
        GUI用のTCLスクリプトを生成（ソケットサーバー付き）

        Args:
            design_files: 設計ファイルのリスト
            testbench_file: テストベンチファイル
            top_module: トップモジュール名
            sim_time: シミュレーション時間（例: "1us", "10ns"）
            server_port: ソケットサーバーのポート番号（デフォルト: 12345）

        Returns:
            生成されたTCLスクリプトのパス
        """
        # Generate basic TCL script first
        tcl_file_path = self.create_gui_tcl_script(
            design_files, testbench_file, top_module, sim_time
        )

        # Read the generated script
        with open(tcl_file_path, 'r', encoding='utf-8') as f:
            tcl_content = f.read()

        # Get the socket server script path
        socket_server_script = self.scripts_dir / "modelsim_socket_server.tcl"
        socket_server_str = str(socket_server_script).replace("\\", "/")

        # Add socket server startup at the end
        server_startup_code = f"""

# ========================================
# Socket Server Startup
# ========================================
echo ""
echo "Starting socket server..."

# Source the socket server script
if {{[catch {{source {socket_server_str}}} err]}} {{
    echo "ERROR: Failed to source socket server script: $err"
    echo "Socket server will not be available"
}} else {{
    # Start the socket server
    set server_result [start_socket_server {server_port}]
    if {{$server_result == 1}} {{
        echo ""
        echo "=========================================="
        echo "✓ Socket server is running on port {server_port}"
        echo "=========================================="
        echo ""
        echo "You can now control ModelSim from Python:"
        echo "  from scripts.modelsim_client import ModelSimClient"
        echo "  client = ModelSimClient(port={server_port})"
        echo "  client.connect()"
        echo "  client.ping()"
        echo ""
    }} else {{
        echo "ERROR: Failed to start socket server"
    }}
}}
"""

        # Append server startup code
        tcl_content += server_startup_code

        # Write back to file
        with open(tcl_file_path, 'w', encoding='utf-8') as f:
            f.write(tcl_content)

        return str(tcl_file_path)

    def run_simulation_gui(self,
                          design_files: List[str],
                          testbench_file: str,
                          top_module: str,
                          sim_time: str = "1us"):
        """
        ModelSim GUIでシミュレーションを実行

        Args:
            design_files: 設計ファイルのリスト
            testbench_file: テストベンチファイル
            top_module: トップモジュール名
            sim_time: シミュレーション時間
        """
        print(f"Starting ModelSim GUI for {top_module}...")

        # TCLスクリプトを生成
        tcl_script = self.create_gui_tcl_script(
            design_files, testbench_file, top_module, sim_time
        )
        print(f"TCL script generated: {tcl_script}")

        # ModelSim GUIを起動
        cmd = [
            str(self.vsim_exe),
            "-do", tcl_script
        ]

        try:
            # 環境変数にModelSimのパスを追加
            env = os.environ.copy()
            env['PATH'] = str(self.modelsim_path) + os.pathsep + env.get('PATH', '')

            # GUIをバックグラウンドで起動
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(self.sim_dir)
            )

            print(f"ModelSim GUI launched (PID: {process.pid})")
            print("\nGUI Window:")
            print("  - Wave window: 波形がリアルタイムで表示されます")
            print("  - Transcript: コマンド入力とメッセージ")
            print("  - Objects: 信号の一覧")
            print("\nTips:")
            print("  - 追加でシミュレーション実行: Transcriptで 'run 1us' と入力")
            print("  - 再スタート: 'restart -f' と入力してから 'run <time>'")
            print("  - ズーム: Ctrl+0 でズームフル")
            print("  - 信号の追加: Objectsから波形にドラッグ")

        except Exception as e:
            print(f"ERROR: Failed to launch ModelSim: {e}")

    def run_simulation_gui_with_server(self,
                                       design_files: List[str],
                                       testbench_file: str,
                                       top_module: str,
                                       sim_time: str = "1us",
                                       server_port: int = 12345):
        """
        ModelSim GUIでシミュレーションを実行（ソケットサーバー付き）

        Args:
            design_files: 設計ファイルのリスト
            testbench_file: テストベンチファイル
            top_module: トップモジュール名
            sim_time: シミュレーション時間
            server_port: ソケットサーバーのポート番号（デフォルト: 12345）
        """
        print(f"Starting ModelSim GUI with socket server for {top_module}...")

        # TCLスクリプトを生成（サーバー付き）
        tcl_script = self.create_gui_tcl_script_with_server(
            design_files, testbench_file, top_module, sim_time, server_port
        )
        print(f"TCL script generated: {tcl_script}")

        # ModelSim GUIを起動
        cmd = [
            str(self.vsim_exe),
            "-do", tcl_script
        ]

        try:
            # 環境変数にModelSimのパスを追加
            env = os.environ.copy()
            env['PATH'] = str(self.modelsim_path) + os.pathsep + env.get('PATH', '')

            # GUIをバックグラウンドで起動
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=str(self.sim_dir)
            )

            print(f"ModelSim GUI launched (PID: {process.pid})")
            print(f"Socket server will start on port {server_port}")
            print("\nGUI Window:")
            print("  - Wave window: 波形がリアルタイムで表示されます")
            print("  - Transcript: コマンド入力とメッセージ")
            print("  - Objects: 信号の一覧")
            print("\nSocket Control:")
            print("  - Python から ModelSim を制御できます")
            print("  - サーバーが起動するまで数秒お待ちください")
            print("\nPython Example:")
            print("  from scripts.modelsim_client import ModelSimClient")
            print("  client = ModelSimClient()")
            print("  client.connect()")
            print("  client.recompile([...], ...)")
            print("  client.restart_simulation()")
            print("  client.run_simulation('1us')")
            print("\nTips:")
            print("  - 追加でシミュレーション実行: Transcriptで 'run 1us' と入力")
            print("  - 再スタート: 'restart -f' と入力してから 'run <time>'")
            print("  - ズーム: Ctrl+0 でズームフル")
            print("  - 信号の追加: Objectsから波形にドラッグ")

            return process

        except Exception as e:
            print(f"ERROR: Failed to launch ModelSim: {e}")
            return None


def main():
    """使用例"""
    # ModelSim GUIランナーを初期化
    runner = ModelSimGUIRunner()

    # 例：カウンタのシミュレーション
    design_files = [
        runner.hdl_dir / "design" / "counter.v"
    ]
    testbench_file = runner.hdl_dir / "testbench" / "counter_tb.v"

    # GUI上でシミュレーション実行
    runner.run_simulation_gui(
        design_files=design_files,
        testbench_file=testbench_file,
        top_module="counter_tb",
        sim_time="1us"
    )


if __name__ == "__main__":
    main()
