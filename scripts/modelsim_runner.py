"""
ModelSim Automation Runner
Claudeが生成したHDLコードを自動的にシミュレーションするためのスクリプト
"""

import os
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ModelSimRunner:
    """ModelSimを制御してシミュレーションを実行するクラス"""

    def __init__(self, modelsim_path: str = "C:/intelFPGA/20.1/modelsim_ase/win32aloem"):
        """
        Args:
            modelsim_path: ModelSimのインストールディレクトリ
        """
        self.modelsim_path = Path(modelsim_path)
        self.vsim_exe = self.modelsim_path / "vsim.exe"
        self.vlog_exe = self.modelsim_path / "vlog.exe"
        self.vlib_exe = self.modelsim_path / "vlib.exe"

        # プロジェクトのルートディレクトリ
        self.project_root = Path(__file__).parent.parent
        self.hdl_dir = self.project_root / "hdl"
        self.sim_dir = self.project_root / "sim"
        self.scripts_dir = self.project_root / "scripts"
        self.results_dir = self.project_root / "results"

        # ModelSimの実行可能ファイルが存在するか確認
        if not self.vsim_exe.exists():
            raise FileNotFoundError(f"ModelSim not found at {self.vsim_exe}")

    def create_tcl_script(self,
                         design_files: List[str],
                         testbench_file: str,
                         top_module: str,
                         sim_time: str = "1us") -> str:
        """
        シミュレーション用のTCLスクリプトを生成

        Args:
            design_files: 設計ファイルのリスト
            testbench_file: テストベンチファイル
            top_module: トップモジュール名
            sim_time: シミュレーション時間（例: "1us", "10ns"）

        Returns:
            生成されたTCLスクリプトのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tcl_file = self.scripts_dir / f"sim_{timestamp}.tcl"
        log_file = self.results_dir / "logs" / f"sim_{timestamp}.log"
        waveform_file = self.results_dir / "waveforms" / f"sim_{timestamp}.wlf"

        # パスをModelSim用に変換（forward slash）
        design_files_str = " ".join([str(f).replace("\\", "/") for f in design_files])
        testbench_str = str(testbench_file).replace("\\", "/")
        log_file_str = str(log_file).replace("\\", "/")
        waveform_file_str = str(waveform_file).replace("\\", "/")
        sim_dir_str = str(self.sim_dir).replace("\\", "/")

        tcl_content = f"""# Auto-generated TCL script for ModelSim
# Generated at {timestamp}

# ワークライブラリの作成
if {{[file exists {sim_dir_str}/work]}} {{
    catch {{vdel -all}}
}}
if {{[catch {{vlib {sim_dir_str}/work}}]}} {{
    puts "ERROR: Failed to create work library"
    quit -f
}}
if {{[catch {{vmap work {sim_dir_str}/work}}]}} {{
    puts "ERROR: Failed to map work library"
    quit -f
}}

# 設計ファイルのコンパイル
puts "Compiling design files..."
if {{[catch {{vlog -work work {design_files_str}}}]}} {{
    puts "ERROR: Design compilation failed"
    quit -f
}}

# テストベンチのコンパイル
puts "Compiling testbench..."
if {{[catch {{vlog -work work {testbench_str}}}]}} {{
    puts "ERROR: Testbench compilation failed"
    quit -f
}}

# シミュレーションの開始
puts "Starting simulation..."
if {{[catch {{vsim -c -wlf {waveform_file_str} work.{top_module}}}]}} {{
    puts "ERROR: Failed to start simulation"
    quit -f
}}

# ログファイルを設定
transcript file {log_file_str}

# すべての信号をログに記録
log -r /*

# シミュレーション実行
puts "Running simulation for {sim_time}..."
run {sim_time}

# 終了
puts "Simulation completed successfully"
quit -f
"""

        with open(tcl_file, 'w', encoding='utf-8') as f:
            f.write(tcl_content)

        return str(tcl_file)

    def run_simulation(self, tcl_script: str) -> Tuple[bool, str, str]:
        """
        ModelSimでシミュレーションを実行

        Args:
            tcl_script: 実行するTCLスクリプトのパス

        Returns:
            (成功/失敗, 標準出力, 標準エラー出力)
        """
        # ModelSimのbinディレクトリをPATHに追加
        env = os.environ.copy()
        env['PATH'] = str(self.modelsim_path) + os.pathsep + env.get('PATH', '')

        # vsimをコマンドラインモードで実行
        cmd = [
            str(self.vsim_exe),
            '-c',  # コマンドラインモード
            '-do', tcl_script
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=str(self.sim_dir)
            )

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except Exception as e:
            return False, "", str(e)

    def parse_log(self, log_file: str) -> Dict:
        """
        シミュレーションログを解析

        Args:
            log_file: ログファイルのパス

        Returns:
            解析結果の辞書
        """
        # ログファイルが存在しない場合、transcriptファイルを試す
        if not os.path.exists(log_file):
            transcript_file = self.sim_dir / "transcript"
            if transcript_file.exists():
                log_file = str(transcript_file)
            else:
                return {
                    "success": False,
                    "errors": ["Log file and transcript not found"],
                    "warnings": [],
                    "display_outputs": []
                }

        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()

        # エラー、警告、情報メッセージを抽出
        errors = re.findall(r'\*\* Error:.*|ERROR:.*', log_content)
        warnings = re.findall(r'\*\* Warning:.*', log_content)

        # $displayや$write出力を抽出（# で始まる行）
        display_outputs = re.findall(r'^# (.+)$', log_content, re.MULTILINE)

        # シミュレーション成功の判定
        # 1. エラーがない
        # 2. $finishが正常に実行された、またはPASSメッセージがある
        has_finish = "$finish" in log_content or "End time:" in log_content
        has_pass = "PASS" in log_content
        success = (len(errors) == 0 and (has_finish or has_pass))

        return {
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "display_outputs": display_outputs,
            "raw_log": log_content
        }

    def simulate(self,
                design_files: List[str],
                testbench_file: str,
                top_module: str,
                sim_time: str = "1us") -> Dict:
        """
        完全な自動シミュレーションフローを実行

        Args:
            design_files: 設計ファイルのリスト
            testbench_file: テストベンチファイル
            top_module: トップモジュール名
            sim_time: シミュレーション時間

        Returns:
            シミュレーション結果の辞書
        """
        print(f"Starting simulation for {top_module}...")

        # TCLスクリプトを生成
        tcl_script = self.create_tcl_script(
            design_files, testbench_file, top_module, sim_time
        )
        print(f"TCL script generated: {tcl_script}")

        # シミュレーション実行
        success, stdout, stderr = self.run_simulation(tcl_script)
        print(f"Simulation {'succeeded' if success else 'failed'}")

        # ログファイルを見つける
        timestamp = Path(tcl_script).stem.replace("sim_", "")
        log_file = self.results_dir / "logs" / f"sim_{timestamp}.log"

        # ログ解析
        log_analysis = self.parse_log(str(log_file))

        result = {
            "overall_success": success and log_analysis["success"],
            "tcl_script": tcl_script,
            "log_file": str(log_file),
            "stdout": stdout,
            "stderr": stderr,
            "log_analysis": log_analysis
        }

        return result

    def print_result(self, result: Dict):
        """シミュレーション結果を見やすく表示"""
        print("\n" + "="*60)
        print("SIMULATION RESULT")
        print("="*60)

        if result["overall_success"]:
            print("✓ SUCCESS")
        else:
            print("✗ FAILED")

        print(f"\nLog file: {result['log_file']}")

        analysis = result["log_analysis"]

        if analysis["errors"]:
            print(f"\n{len(analysis['errors'])} Error(s):")
            for err in analysis["errors"]:
                print(f"  - {err}")

        if analysis["warnings"]:
            print(f"\n{len(analysis['warnings'])} Warning(s):")
            for warn in analysis["warnings"][:5]:  # 最初の5件のみ表示
                print(f"  - {warn}")
            if len(analysis["warnings"]) > 5:
                print(f"  ... and {len(analysis['warnings']) - 5} more warnings")

        if analysis.get("display_outputs"):
            print("\nSimulation Output:")
            for output in analysis["display_outputs"][:20]:  # 最初の20行のみ
                print(f"  {output}")
            if len(analysis["display_outputs"]) > 20:
                print(f"  ... and {len(analysis['display_outputs']) - 20} more lines")

        print("="*60 + "\n")


def main():
    """使用例"""
    # ModelSimランナーを初期化
    runner = ModelSimRunner()

    # 例：カウンタのシミュレーション
    design_files = [
        runner.hdl_dir / "design" / "counter.v"
    ]
    testbench_file = runner.hdl_dir / "testbench" / "counter_tb.v"

    # シミュレーション実行
    result = runner.simulate(
        design_files=design_files,
        testbench_file=testbench_file,
        top_module="counter_tb",
        sim_time="1us"
    )

    # 結果表示
    runner.print_result(result)

    # JSON形式で保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_json = runner.results_dir / "logs" / f"result_{timestamp}.json"
    with open(result_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Result saved to: {result_json}")


if __name__ == "__main__":
    main()
