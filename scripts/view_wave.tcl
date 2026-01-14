# ModelSim波形自動表示スクリプト
# すべての信号を波形ウィンドウに追加してズーム

# 波形ウィンドウを表示
view wave

# すべての信号を追加
add wave -r /*

# カラーとフォーマットの設定
configure wave -namecolwidth 200
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 1
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2

# 時間軸の設定
configure wave -timelineunits ns

# ズームフル
wave zoom full

# メッセージ表示
echo "================================================"
echo "Wave window configured successfully"
echo "------------------------------------------------"
echo "Available commands:"
echo "  wave zoom full  - Zoom to full range"
echo "  wave zoom in    - Zoom in"
echo "  wave zoom out   - Zoom out"
echo "  run 1us         - Run additional simulation time"
echo "================================================"
