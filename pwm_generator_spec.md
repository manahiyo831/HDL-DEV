# HDL設計仕様書 - PWMジェネレーター
# HDL Design Specification - PWM Generator

## ドキュメント情報 / Document Information

| 項目 / Item | 内容 / Content |
|-------------|----------------|
| モジュール名 / Module Name | pwm_generator |
| バージョン / Version | 1.0.0 |
| 作成日 / Date | 2025-01-17 |
| 作成者 / Author | Claude Code |
| レビュアー / Reviewer | - |
| ステータス / Status | Draft |

### 改訂履歴 / Revision History

| バージョン / Version | 日付 / Date | 作成者 / Author | 変更内容 / Changes |
|---------------------|-------------|-----------------|-------------------|
| 1.0.0 | 2025-01-17 | Claude Code | 初版 / Initial version |

---

## 1. 概要 / Overview

### 1.1 目的 / Purpose
16bit分解能のPWM（Pulse Width Modulation）信号を生成するモジュール。
デューティ比を0%～100%の範囲で設定可能。LED調光、モーター制御、D/A変換等に使用可能。

Claude Code SKILLのデモンストレーション用として、HDL自動生成→シミュレーション→波形確認の一連のフローを示す。

### 1.2 スコープ / Scope
- 目標 / Goals:
  - 16bit分解能のPWM信号生成
  - デューティ比の動的変更対応
  - シンプルで理解しやすい実装
- 非目標 / Non-Goals:
  - デッドタイム生成（相補出力なし）
  - 複数チャンネル出力
  - 位相制御

### 1.3 要求仕様概要 / Requirements Summary
- PWM周波数: 約39.06kHz（10MHz / 256）
- 分解能: 8bit（256段階）
- デューティ比: 0～255（0%～100%）
- 即時更新: デューティ値変更は次の周期から反映

---

## 2. システム構成 / System Architecture

### 2.1 ブロック図 / Block Diagram
```
              +-------------------------+
              |     pwm_generator       |
              |                         |
    clk  ---->|  +--------+  +-------+  |
    rst  ---->|  |Counter |->|Compare|--+--> pwm_out
              |  | (8bit) |  | Logic |  |
    duty ---->|  +--------+  +-------+  |
    [7:0]     |                         |
              +-------------------------+
```

### 2.2 階層構造 / Module Hierarchy
```
pwm_generator (単一モジュール、サブモジュールなし)
```

### 2.3 他システムとの関係 / System Integration
対象外 - スタンドアロンデモ用モジュール

---

## 3. インターフェース仕様 / Interface Specification

### 3.1 信号一覧 / Signal List

#### 3.1.1 入力信号 / Input Signals

| 信号名 / Signal Name | ビット幅 / Width | 説明 / Description | プロトコル / Protocol |
|---------------------|-----------------|-------------------|---------------------|
| clk | 1 | システムクロック (10MHz) / System clock | - |
| rst | 1 | 同期リセット（正論理）/ Sync reset (active high) | - |
| duty | 8 | デューティ比設定値 / Duty cycle setting (0-255) | - |

#### 3.1.2 出力信号 / Output Signals

| 信号名 / Signal Name | ビット幅 / Width | 説明 / Description | プロトコル / Protocol |
|---------------------|-----------------|-------------------|---------------------|
| pwm_out | 1 | PWM出力信号 / PWM output signal | - |

#### 3.1.3 双方向信号 / Inout Signals
対象外 - なし

### 3.2 プロトコル仕様 / Protocol Specification
対象外 - 標準プロトコル不使用

---

## 4. クロックとリセット / Clock and Reset

### 4.1 クロックドメイン / Clock Domains

| クロック名 / Clock Name | 公称周波数 / Nominal Frequency | 周波数範囲 / Frequency Range | 説明 / Description |
|------------------------|-------------------------------|----------------------------|-------------------|
| clk | 10 MHz | 10 MHz (固定) | システムクロック / System clock |

### 4.2 クロックドメイン間の信号転送 / Clock Domain Crossing (CDC)
対象外 - 単一クロックドメイン

### 4.3 リセット仕様 / Reset Specification

- リセット方式 / Reset Type: 同期リセット (Synchronous)
- リセット極性 / Reset Polarity: 正論理 (Active High)
- リセット期間 / Reset Duration: 最小1クロックサイクル / Minimum 1 clock cycle
- リセット解除 / Reset Deassertion: 同期（クロック立ち上がりエッジ）

---

## 5. 機能仕様 / Functional Specification

### 5.1 機能概要 / Functional Overview
1. 8bitフリーランニングカウンタでPWM周期を生成
2. カウンタ値とデューティ設定値を比較
3. カウンタ < デューティ のとき pwm_out = 1
4. カウンタ >= デューティ のとき pwm_out = 0

### 5.2 動作説明 / Operation Description

#### 5.2.1 通常動作 / Normal Operation
1. リセット解除後、カウンタは0から開始
2. 毎クロックでカウンタをインクリメント
3. カウンタがオーバーフロー（255→0）でPWM周期が完了
4. duty値との比較結果をpwm_outに出力

#### 5.2.2 状態遷移 / State Machine
対象外 - ステートマシン不使用（単純なカウンタ＋比較器）

#### 5.2.3 エラー処理 / Error Handling
対象外 - エラー状態なし

### 5.3 タイミング仕様 / Timing Specification

#### 5.3.1 タイミングダイアグラム / Timing Diagram
```
        ___     ___     ___     ___     ___     ___
clk    |   |___|   |___|   |___|   |___|   |___|   |___

counter  0       1       2       3       4       5   ...

duty = 3の場合:
        _________________
pwm_out                  |_____________________________...
        (counter < 3)     (counter >= 3)
```

#### 5.3.2 タイミングパラメータ / Timing Parameters

| パラメータ / Parameter | 値 / Value | 単位 / Unit | 説明 / Description |
|----------------------|-----------|------------|-------------------|
| PWM周期 / PWM Period | 25.6 | μs | 256 / 10MHz |
| PWM周波数 / PWM Frequency | 39.06 | kHz | 10MHz / 256 |
| 分解能 / Resolution | 8 | bit | 256段階 |
| duty変更反映 / Duty update latency | 1 | cycle | 即時反映 |

---

## 6. レジスタ仕様 / Register Specification
対象外 - レジスタマップなし（直接信号入力）

---

## 7. パフォーマンス仕様 / Performance Specification

### 7.1 スループット / Throughput
対象外 - 連続動作

### 7.2 リソース使用量 / Resource Utilization
対象デバイス / Target device: 汎用FPGA（Intel/Xilinx）

| リソース / Resource | 予想使用量 / Estimated Usage |
|-------------------|------------------------------|
| LUT | ~10 |
| FF | ~17 (8bit counter + 8bit duty reg + 1bit output) |
| BRAM | 0 |
| DSP | 0 |

### 7.3 電力仕様 / Power Specification
対象外 - デモ用途のため未規定

---

## 8. 検証仕様 / Verification Specification

### 8.1 検証戦略 / Verification Strategy
- ModelSimによるRTLシミュレーション
- TEST_RESULT:マーカーによる自動Pass/Fail判定

### 8.2 テストシナリオ / Test Scenarios

| テストID / Test ID | テスト項目 / Test Item | 目的 / Purpose | 合格基準 / Pass Criteria |
|-------------------|----------------------|---------------|------------------------|
| TC001 | リセット動作 | リセット後の初期化確認 | counter=0, pwm_out=0 |
| TC002 | duty=0 (0%) | 最小デューティ | pwm_out常にLow |
| TC003 | duty=255 (100%) | 最大デューティ | pwm_out常にHigh |
| TC004 | duty=64 (25%) | 25%デューティ | 適切なパルス幅 |
| TC005 | duty=128 (50%) | 50%デューティ | 適切なパルス幅 |
| TC006 | duty=192 (75%) | 75%デューティ | 適切なパルス幅 |
| TC007 | duty動的変更 | 動作中のduty変更 | 次周期から反映 |

### 8.3 カバレッジ目標 / Coverage Goals
対象外 - デモ用途のため未規定

---

## 9. デバッグ機能 / Debug Features
対象外 - デモ用途のため未実装

---

## 10. 信頼性とテスト / Reliability and Testing
対象外 - デモ用途のため未規定

---

## 11. 実装ガイドライン / Implementation Guidelines

### 11.1 コーディングスタイル / Coding Style
- 言語 / Language: Verilog
- コーディング規約 / Coding standard: シンプルで読みやすい記述

### 11.2 合成制約 / Synthesis Constraints
- 最大動作周波数 / Maximum operating frequency: 10 MHz以上
- 特別な制約なし

### 11.3 配置配線制約 / Place and Route Constraints
対象外 - 特別な制約なし

---

## 12. 参考資料 / References
対象外

---

## 13. 用語集 / Glossary

| 用語 / Term | 説明 / Description |
|------------|-------------------|
| PWM | Pulse Width Modulation - パルス幅変調 |
| デューティ比 | Highレベルの時間比率 |

---

## 14. 付録 / Appendix

### 14.1 設計上の考慮事項 / Design Considerations
- 8bitカウンタ採用により、高速なPWM周期（約39kHz）を実現
- 波形観測に適した周期長（25.6μs）
- duty値は即時反映（周期境界での同期なし）により、応答性を優先

### 14.2 既知の問題と制限事項 / Known Issues and Limitations
- duty=0のとき、pwm_outは常にLow（パルスなし）
- duty=255のとき、pwm_outは常にHigh（パルスなし）
- 周期途中でのduty変更はグリッチを発生させる可能性あり

### 14.3 将来の拡張 / Future Extensions
- 周期同期でのduty値更新オプション
- 複数チャンネル対応
- デッドタイム生成機能

---

## 承認 / Approval
対象外 - デモ用途
