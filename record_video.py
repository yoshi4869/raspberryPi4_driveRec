import time
from picamera2 import Picamera2
from libcamera import controls # libcamera.controls が存在しない場合はこの行をコメントアウト
from picamera2.encoders import H264Encoder # この行も追加

print("カメラを初期化しています...")
picam2 = Picamera2()

# カメラの設定 (ここでは1080p動画設定の例)
video_config = picam2.create_video_configuration(main={"size": (1920, 1080)}, lores={"size": (640, 480)}, display="lores")
picam2.configure(video_config)

# オートフォーカスを設定 (V3カメラの特性)
# libcamera.controls が存在しない場合はこのifブロック全体をコメントアウトまたは削除
if hasattr(controls, 'AfModeEnum'):
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
else:
    print("警告: libcamera.controls.AfModeEnum が見つかりませんでした。オートフォーカス設定をスキップします。")

encoder = H264Encoder() # エンコーダーオブジェクトを作成

print("録画を開始します (5秒間)...")
picam2.start_recording(
    encoder,
    output="my_first_video.mp4"
)

time.sleep(5)

print("録画を停止します。")
picam2.stop_recording()

# --- この行を追加しましたか？ ---
picam2.close() # カメラリソースを解放する
# --- この行を追加しましたか？ ---

print("動画を 'my_first_video.mp4' として保存しました！")