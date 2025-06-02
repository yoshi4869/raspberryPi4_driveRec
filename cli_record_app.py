import time
import sys
import threading
import subprocess # subprocessモジュールを追加
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from libcamera import controls # libcamera.controls が存在しない場合はコメントアウト

# --- グローバル変数とカメラ・エンコーダーの設定 ---
picam2 = None
encoder = None
is_recording = False
current_h264_filename = "" # H.264の生データファイル名を保持
final_mp4_filename = ""    # 最終的なMP4ファイル名を保持

def initialize_camera():
    """カメラの初期設定と準備を行う関数"""
    global picam2, encoder
    try:
        picam2 = Picamera2()

        video_config = picam2.create_video_configuration(
            main={"size": (1920, 1080)},
            lores={"size": (640, 480)},
            display="lores"
        )
        picam2.configure(video_config)

        if hasattr(controls, 'AfModeEnum'):
            picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        else:
            print("警告: libcamera.controls.AfModeEnum が見つかりませんでした。オートフォーカス設定をスキップします。")
        
        encoder = H264Encoder()
        print("カメラ初期化完了。")
        print("--------------------------------------------------")
        print("コマンド入力待ち: 'start' で録画開始, 'stop' で録画停止, 'exit' で終了")
        print("--------------------------------------------------")

    except Exception as e:
        print(f"エラー: カメラの初期化に失敗しました: {e}")
        sys.exit(1)

def start_recording_func():
    """録画を開始する処理"""
    global is_recording, current_h264_filename, final_mp4_filename
    if is_recording:
        print("すでに録画中です。")
        return

    if picam2 is None:
        print("エラー: カメラが初期化されていません。")
        return

    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        # 直接MP4ではなく、一時的にH.264生データで保存
        current_h264_filename = f"temp_video_{timestamp}.h264"
        final_mp4_filename = f"video_{timestamp}.mp4" # 最終的なMP4ファイル名
        
        print(f"録画を開始します: {current_h264_filename}")
        picam2.start_recording(
            encoder,
            output=current_h264_filename # H.264生データとして保存
        )
        is_recording = True
        print("録画中...")
    except Exception as e:
        print(f"エラー: 録画の開始に失敗しました: {e}")
        is_recording = False

def stop_recording_func():
    """録画を停止し、MP4に変換する処理"""
    global is_recording, current_h264_filename, final_mp4_filename
    if not is_recording:
        print("現在録画していません。")
        return
    
    try:
        print("録画を停止します。")
        picam2.stop_recording()
        is_recording = False
        print(f"一時H.264ファイル '{current_h264_filename}' を保存しました。")
        
        # --- ここからFFmpegでの変換処理を追加 ---
        print(f"'{current_h264_filename}' を '{final_mp4_filename}' に変換中...")
        try:
            # ffmpegコマンドを実行
            subprocess.run(
                ['ffmpeg', '-i', current_h264_filename, '-c:v', 'copy', final_mp4_filename],
                check=True, # エラーが発生したら例外を発生させる
                capture_output=True, # 出力をキャプチャして表示しない
                text=True
            )
            print(f"動画を '{final_mp4_filename}' として保存しました！")
            # 変換が成功したら、一時ファイルを削除 (任意)
            # import os
            # os.remove(current_h264_filename)
            # print(f"一時ファイル '{current_h264_filename}' を削除しました。")

        except subprocess.CalledProcessError as e:
            print(f"エラー: FFmpegでの変換に失敗しました。")
            print(f"FFmpegエラー出力: {e.stderr}")
            print(f"一時ファイル '{current_h264_filename}' は残しています。")
        except FileNotFoundError:
            print("エラー: FFmpegコマンドが見つかりません。Raspberry PiにFFmpegがインストールされているか確認してください。")
            print("sudo apt install -y ffmpeg")
        # --- FFmpegでの変換処理ここまで ---

    except Exception as e:
        print(f"エラー: 録画の停止または変換中に失敗しました: {e}")

def monitor_commands():
    """コマンド入力を監視するスレッド"""
    global is_recording
    while True:
        try:
            command = input(">> ").strip().lower()
            if command == "start":
                start_recording_func()
            elif command == "stop":
                stop_recording_func()
            elif command == "exit":
                print("終了コマンドが入力されました。")
                break
            else:
                print("無効なコマンドです。'start', 'stop', 'exit' のいずれかを入力してください。")
        except EOFError:
            print("\nEOFが検出されました。終了します。")
            break
        except Exception as e:
            print(f"コマンド処理中にエラー: {e}")
            break

# --- メイン処理 ---
if __name__ == "__main__":
    initialize_camera()

    command_thread = threading.Thread(target=monitor_commands)
    command_thread.daemon = True
    command_thread.start()

    command_thread.join()

    # --- 終了処理 ---
    print("アプリケーションを終了します。")
    if is_recording:
        stop_recording_func() # 録画中なら停止する
    if picam2:
        try:
            picam2.close() # カメラリソースを解放
            print("カメラリソースを解放しました。")
        except Exception as e:
            print(f"カメラリソースの解放中にエラー: {e}")
    sys.exit(0)