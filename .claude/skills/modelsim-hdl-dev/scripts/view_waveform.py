"""
ModelSim波形ビューアを起動するスクリプト
"""

import os
import subprocess
from pathlib import Path
import glob


def view_waveform(waveform_file: str = None, modelsim_path: str = "C:/intelFPGA/20.1/modelsim_ase/win32aloem", auto_add_signals: bool = True):
    """
    ModelSim GUIで波形ファイルを開く

    Args:
        waveform_file: 波形ファイルのパス。Noneの場合は最新のファイルを開く
        modelsim_path: ModelSimのインストールディレクトリ
        auto_add_signals: すべての信号を自動的に追加するかどうか
    """
    project_root = Path.cwd()
    waveforms_dir = project_root / "results" / "waveforms"
    scripts_dir = project_root / "scripts"
    modelsim_exe = Path(modelsim_path) / "modelsim.exe"

    # ModelSimが存在するか確認
    if not modelsim_exe.exists():
        print(f"ERROR: ModelSim not found at {modelsim_exe}")
        return False

    # 波形ファイルを決定
    if waveform_file is None:
        # 最新の波形ファイルを探す
        wlf_files = sorted(waveforms_dir.glob("sim_*.wlf"), reverse=True)
        if not wlf_files:
            print("ERROR: No waveform files found")
            return False
        waveform_file = wlf_files[0]
    else:
        waveform_file = Path(waveform_file)

    if not waveform_file.exists():
        print(f"ERROR: Waveform file not found: {waveform_file}")
        return False

    print(f"Opening waveform: {waveform_file}")

    # ModelSim GUIを起動
    # -viewオプションで波形ファイルを開く
    cmd = [
        str(modelsim_exe),
        "-view",
        str(waveform_file).replace("\\", "/")
    ]

    # 自動的に信号を追加する場合、TCLスクリプトを指定
    if auto_add_signals:
        view_wave_tcl = scripts_dir / "view_wave.tcl"
        if view_wave_tcl.exists():
            cmd.extend(["-do", str(view_wave_tcl).replace("\\", "/")])
            print("Auto-adding all signals to wave window...")

    try:
        # 環境変数にModelSimのパスを追加
        env = os.environ.copy()
        env['PATH'] = str(Path(modelsim_path)) + os.pathsep + env.get('PATH', '')

        # バックグラウンドでGUIを起動
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(project_root / "sim")
        )

        print(f"ModelSim GUI launched (PID: {process.pid})")
        print("Wave window with all signals should open automatically.")
        print("\nTips:")
        print("  - ズーム: Ctrl+0 でズームフル")
        print("  - カーソル移動: 波形をクリック")
        print("  - 信号の追加: Objects windowから波形にドラッグ")
        print("  - 信号の削除: 波形で右クリック -> Delete")
        return True

    except Exception as e:
        print(f"ERROR: Failed to launch ModelSim: {e}")
        return False


def list_waveforms():
    """利用可能な波形ファイルを一覧表示"""
    project_root = Path.cwd()
    waveforms_dir = project_root / "results" / "waveforms"

    wlf_files = sorted(waveforms_dir.glob("sim_*.wlf"), reverse=True)

    if not wlf_files:
        print("No waveform files found")
        return

    print(f"Found {len(wlf_files)} waveform file(s):\n")
    for i, wlf in enumerate(wlf_files, 1):
        size_kb = wlf.stat().st_size / 1024
        print(f"{i}. {wlf.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_waveforms()
        else:
            # 指定された波形ファイルを開く
            view_waveform(sys.argv[1])
    else:
        # 最新の波形ファイルを開く
        view_waveform()
