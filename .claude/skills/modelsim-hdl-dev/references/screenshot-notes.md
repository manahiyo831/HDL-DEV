# ModelSim波形ウィンドウキャプチャ実装ノート

## 概要

ModelSimの波形ウィンドウをPythonから自動キャプチャする機能の実装記録。
複数のアプローチを試行し、最終的にシンプルで確実な方法に到達した。

---

## 実装の経緯

### 目的

Claudeが自身でシミュレーション結果を視覚的に確認できるように、波形ウィンドウのスクリーンショットを自動取得する機能を追加する。

### 要件

1. 波形ウィンドウのみを正確にキャプチャ
2. デュアルモニター環境でも動作
3. ModelSimの内部状態に依存しない安定した動作

---

## 試行したアプローチ

### アプローチ1: Tcl座標を使った相対キャプチャ（失敗）

**方法:**
1. TclコマンドでWaveウィンドウの座標を取得 (`winfo geometry .main_pane.wave`)
2. 親ウィンドウのクライアント領域オフセットを計算
3. 座標を変換してキャプチャ

**問題点:**
- Tclが返す座標は`.main_pane.wave`ウィンドウ内の相対座標
- 親ウィンドウのクライアント領域を基準にしており、タイトルバー/メニューバー/ツールバーのオフセット計算が複雑
- 座標系の変換が必要で、エラーが発生しやすい

**結果:**
```
Geometry from Tcl: 1191x458+804+0
Client Offset: (8, 51)
Capture Position: (812, 51)
→ 正しくキャプチャできず
```

---

### アプローチ2: MDIClientウィンドウの探索（失敗）

**方法:**
1. MDIアプリケーションの仕組みを利用
2. `MDIClient`クラスのウィンドウを探索
3. MDIClientを基準に座標を計算

**問題点:**
- ModelSimはTcl/Tkベースで、MDIClientクラスが存在しない
- 代わりにTkChildウィンドウが398個存在
- MDIアプローチは適用不可

**調査結果:**
```
Child window classes:
  Button: 133
  ScrollBar: 6
  Static: 49
  TkChild: 398
```

---

### アプローチ3: ウィジェット階層の詳細調査（参考情報）

**方法:**
TclコマンドでWaveウィンドウの内部ウィジェット構造を調査

**調査結果:**
```
.main_pane.wave (1191x458+804+0)          ← Waveウィンドウ全体
  └─ .interior (1191x458+0+0)
      ├─ .header                           ← ツールバー
      └─ .cs (1187x436+2+20)              ← コンテンツ領域（+20pxオフセット）
          └─ .body.pw.wf (1185x434+1+1)   ← 波形表示領域のみ
```

**発見:**
- `.main_pane.wave.interior.cs.body.pw.wf` が実際の波形表示領域
- しかし、この座標もウィンドウ内相対座標であり、変換が必要

---

### アプローチ4: 直接HWND取得（成功✓）

**方法:**
1. `EnumChildWindows`で全子ウィンドウを列挙
2. サイズでフィルタリング（1191x458のTkChildを検索）
3. 見つかったHWNDから直接キャプチャ

**実装:**
```python
def find_wave_window_by_size(target_width=1191, target_height=458):
    """サイズでWaveウィンドウを特定"""
    # ModelSim親ウィンドウを探す
    modelsim_windows = find_modelsim_window()
    parent_hwnd = modelsim_windows[0][0]

    # 子ウィンドウを列挙してサイズでフィルタ
    candidates = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if class_name == "TkChild":
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                if width == target_width and height == target_height:
                    candidates.append({'hwnd': hwnd, 'rect': rect})
        return True

    win32gui.EnumChildWindows(parent_hwnd, callback, None)
    return candidates

def capture_child_window_direct(hwnd: int, output_path: Path):
    """HWNDから直接キャプチャ"""
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)

    # ウィンドウ内容をコピー
    save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

    # PIL Imageに変換
    bmp_info = bitmap.GetInfo()
    bmp_bits = bitmap.GetBitmapBits(True)
    img = Image.frombuffer('RGB',
        (bmp_info['bmWidth'], bmp_info['bmHeight']),
        bmp_bits, 'raw', 'BGRX', 0, 1)

    img.save(output_path)

    # リソース解放
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
```

**結果:**
```
Found 3 candidate(s):
  1. HWND=2038792, Rect=(1248, 224, 2439, 682)
  2. HWND=1642566, Rect=(1248, 224, 2439, 682)
  3. HWND=855704, Rect=(1248, 224, 2439, 682)

✓ Captured successfully
  Size: 1191x458 pixels
  File size: 21.4 KB
```

**成功理由:**
- ✓ 実際のスクリーン座標を使用（座標変換不要）
- ✓ Tcl経由の複雑な計算が不要
- ✓ シンプルで確実

---

## 最終実装の詳細

### ウィンドウ階層の調査結果

ModelSimの子ウィンドウ構造（サイズ順）:

| # | サイズ | 位置 | 用途 |
|---|--------|------|------|
| 1-8 | 1995x1088 | (444, 224) | メインペイン全体 |
| 9-12 | 1995x601 | (444, 711) | 下部パネル |
| **19-21** | **1191x458** | **(1248, 224)** | **Waveウィンドウ全体（目的）** |
| 22-24 | 1187x436 | (1250, 244) | Wave内部コンテナ |
| 25-27 | 1185x434 | (1251, 245) | 波形表示領域のみ |

**選択したターゲット:**
- **#19-21 (1191x458)** - Waveウィンドウ全体
  - タイトルバー「Wave - Default」を含む
  - シグナルリスト（左側）を含む
  - 波形表示領域を含む
  - 時間軸とカーソル情報（下部）を含む

### キャプチャ内容

完璧にキャプチャされる内容:
- ✓ タイトルバー
- ✓ ツールバー
- ✓ シグナルリスト（信号名と値）
- ✓ 波形表示領域
- ✓ 時間軸
- ✓ カーソル情報

---

## 実装のポイント

### 1. サイズベースのウィンドウ特定

**理由:**
- ウィンドウタイトルは変更される可能性がある
- クラス名 "TkChild" だけでは特定できない（398個存在）
- サイズは安定している（1191x458）

**実装:**
```python
if class_name == "TkChild":
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    if width == target_width and height == target_height:
        # 発見！
```

### 2. GetWindowDCの使用

**BitBlt vs PrintWindow:**
- `BitBlt`: ウィンドウの実際の表示内容をコピー（高速・確実）
- `PrintWindow`: ウィンドウの描画内容を再描画（複雑なUIでは失敗することがある）

**選択:** `BitBlt` を使用（確実性優先）

### 3. 複数候補の処理

**発見:**
同じサイズのウィンドウが3個見つかる（HWND異なる）

**対応:**
最初の候補をキャプチャ（全て同じ内容を持つため）

### 4. リソース管理

**重要:**
Win32リソースは必ず解放する
```python
win32gui.DeleteObject(bitmap.GetHandle())
save_dc.DeleteDC()
mfc_dc.DeleteDC()
win32gui.ReleaseDC(hwnd, hwnd_dc)
```

---

## 学んだ教訓

### ✓ シンプルな解決策を優先

複雑な座標変換やMDI構造の理解より、直接的なHWND取得の方が確実で保守しやすい。

### ✓ 実際の動作確認が重要

理論的に正しそうなアプローチ（Tcl座標、MDIClient）も、実際には機能しないことがある。

### ✓ ウィンドウ階層の調査ツール

`EnumChildWindows` で全子ウィンドウをリストアップすることで、構造を理解できる。

### ✓ サイズベースの特定は有効

ウィンドウサイズは比較的安定しており、特定の要素を見つけるのに有効な手段。

---

## 今後の拡張案

### オプション1: 波形表示領域のみキャプチャ

**ターゲット:** #25-27 (1185x434)

**用途:**
- より詳細な波形確認
- シグナルリストを除外してコンパクトに

### オプション2: 動的サイズ対応

**課題:**
ウィンドウをリサイズした場合、サイズ固定検索では見つからない

**解決策:**
1. ウィンドウタイトル「Wave」で検索
2. クラス名 "TkChild" でフィルタ
3. サイズの範囲でフィルタ（例: 1000x400以上）

### オプション3: 複数波形ウィンドウ対応

**用途:**
複数の波形ウィンドウが開いている場合

**実装:**
全候補をキャプチャして返す

---

## 参考情報

### 使用ライブラリ

- `win32gui`: Windows GUI操作
- `win32ui`: デバイスコンテキスト操作
- `win32con`: Windows定数
- `PIL (Pillow)`: 画像処理

### 関連ファイル

- `test_direct_capture.py` - 最終実装のテストスクリプト
- `list_child_windows.py` - ウィンドウ階層調査ツール
- `modelsim_child_windows.json` - ウィンドウ一覧（JSON）
- `modelsim_child_windows.txt` - ウィンドウ一覧（人間が読める形式）

### Tcl/Tkウィンドウ構造

```
.main_pane.wave
  ├─ .interior
  │   ├─ .header                    # ツールバー
  │   └─ .cs                         # コンテンツ領域
  │       └─ .body
  │           └─ .pw
  │               ├─ .wf             # 波形表示領域
  │               ├─ .af             # 追加フレーム
  │               └─ .sf             # スクロールバー
  └─ .wavecursorpopup_popup         # カーソルポップアップ
```

---

## まとめ

**最終解決策:**
サイズ (1191x458) でTkChildウィンドウを検索し、見つかったHWNDから直接キャプチャする。

**利点:**
- シンプルで理解しやすい
- Tcl座標変換が不要
- デュアルモニター環境でも動作
- 高速・確実

**制約:**
- ウィンドウサイズが固定されている前提
- 複数の同サイズウィンドウがある場合、最初のものを取得

**推奨:**
このアプローチを`modelsim_controller.py`に統合し、`capture_waveform_window()`メソッドとして提供する。

---

作成日: 2026-01-15
作成者: Claude Code
バージョン: 1.0
