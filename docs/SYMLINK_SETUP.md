# シンボリックリンク設定ガイド / Symlink Setup Guide

## GitHub上での表示について

GitHub Webインターフェースでは、`.claude/skills/modelsim-hdl-dev` をクリックすると、リンク先パス（例: `D:\Claude\SKILLS\modelsim-hdl-dev`）がテキストとして表示されます。

**これは正常な動作です。** GitHubはシンボリックリンクの「内容」（リンク先パス文字列）を表示するためです。

## クローン時にシンボリックリンクとして復元する方法

### Windows環境

#### 必須条件（いずれか）

1. **開発者モードを有効化**（推奨）
   - 設定 → システム → 開発者向け → 「開発者モード」をON
   - これにより、管理者権限なしでシンボリックリンクを作成可能

2. **管理者権限でGit操作を実行**
   - コマンドプロンプト/PowerShellを「管理者として実行」

#### Git設定

```bash
git config --global core.symlinks true
```

#### クローン方法

```bash
git clone https://github.com/manahiyo831/HDL-DEV.git
cd HDL-DEV
```

#### 検証方法

```powershell
Get-Item .claude/skills/modelsim-hdl-dev | Select-Object LinkType,Target
```

**期待される出力:**
```
LinkType     Target
--------     ------
SymbolicLink {D:\Claude\SKILLS\modelsim-hdl-dev}
```

**テキストファイルになっている場合:**
- 開発者モードが無効で、管理者権限なしでクローンした
- `core.symlinks = false` のままクローンした

### Linux/Mac環境

特別な設定は不要です。自動的にシンボリックリンクとして復元されます。

```bash
git clone https://github.com/manahiyo831/HDL-DEV.git
cd HDL-DEV
ls -la .claude/skills/modelsim-hdl-dev  # -> で表示されればOK
```

## 既存クローンの修正

すでにテキストファイルとしてクローンしてしまった場合：

```bash
cd HDL-DEV
git config core.symlinks true
rm .claude/skills/modelsim-hdl-dev  # テキストファイルを削除
git checkout HEAD -- .claude/skills/modelsim-hdl-dev  # シンボリックリンクとして復元
```

**注意:** Windows開発者モードまたは管理者権限が必要です。

## トラブルシューティング

### 1. "Operation not permitted" エラー

**原因:** Windows開発者モードが無効で、管理者権限もない

**解決策:**
- 開発者モードを有効化
- または、管理者権限でコマンドプロンプトを起動

### 2. シンボリックリンク先が存在しない

この環境では、`.claude/skills/modelsim-hdl-dev` は `D:\Claude\SKILLS\modelsim-hdl-dev` を指しています。

クローン先の環境にSKILLSディレクトリが存在しない場合、リンクは「壊れたリンク」になります。

**解決策A:** SKILLSディレクトリを別途配置
**解決策B:** 相対パスシンボリックリンクに変更（次回更新時に検討）

### 3. シンボリックリンクを使いたくない

`skill-creator`のように、実ディレクトリとしてコピーすることも可能です。ただし、SKILLS本体との同期が手動になります。

## 参考情報

- [Git - gitattributes Documentation (symlinks)](https://git-scm.com/docs/gitattributes#_symlinks)
- [GitHub Docs - Working with symbolic links](https://docs.github.com/en/get-started/getting-started-with-git/working-with-symbolic-links)
- Windows開発者モード: Windows 10 バージョン1703以降で使用可能
