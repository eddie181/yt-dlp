#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import shutil

def check_ytdlp():
    """檢查 yt-dlp 是否在系統 PATH 中"""
    if shutil.which("yt-dlp") is None:
        print("錯誤：找不到 'yt-dlp'。")
        print("請確定您已經安裝了 yt-dlp 並且它的路徑在系統的 PATH 環境變數中。")
        print("安裝指南：https://github.com/yt-dlp/yt-dlp#installation")
        sys.exit(1)
    print("✓ yt-dlp 檢查通過。")

def check_ffmpeg():
    """檢查 ffmpeg 是否在系統 PATH 中"""
    if shutil.which("ffmpeg") is None:
        print("\n警告：找不到 'ffmpeg'。")
        print("MP3 轉換和 MP4 合併/格式處理強烈依賴 FFmpeg。")
        print("若下載失敗或格式錯誤，請務必安裝 FFmpeg 並將其加入 PATH。")
        print("FFmpeg 下載：https://ffmpeg.org/download.html")
        # 不退出，讓 yt-dlp 處理，但給予強烈警告
    else:
        print("✓ ffmpeg 檢查通過。")


def main():
    """主執行函數"""
    check_ytdlp()
    check_ffmpeg()

    # 1. 獲取網址
    video_url = input("\n請輸入要下載的影片網址：").strip()
    if not video_url:
        print("錯誤：未輸入網址。程式結束。")
        sys.exit(1)

    # 2. 選擇格式 (MP3 或 MP4)
    while True:
        format_choice = input("請選擇儲存格式 (輸入 mp3 或 mp4)：").lower().strip()
        if format_choice in ['mp3', 'mp4']:
            break
        else:
            print("無效的輸入，請輸入 'mp3' 或 'mp4'。")

    # --- 構建命令的共同部分 ---
    command = ["yt-dlp"]
    # 預設檔名格式 (無 Video ID)
    output_template = "%(title)s.%(ext)s" # 只保留標題和副檔名，如要影片ID，加上 %(id)s
    command.extend(["-o", output_template])

    # --- 處理 MP3 ---
    if format_choice == 'mp3':
        print("\n選擇儲存為 MP3。")
        command.extend([
            "-x",                     # 提取音訊
            "--audio-format", "mp3",  # 指定格式為 mp3
            "--audio-quality", "0",   # 最高音質 (VBR)
            # "--remux-video", "aac>mp3", # 嘗試確保來源是 aac 再轉 mp3 (通常不需要)
            "--embed-thumbnail",      # 嵌入封面圖
            video_url                 # 網址
        ])
        print("準備下載最佳音訊並轉換為 MP3...")

    # --- 處理 MP4 ---
    elif format_choice == 'mp4':
        print("\n選擇儲存為 MP4。")

        # 3. 詢問偏好的視訊編碼
        codec_options = {
            "1": ("H.264 (AVC) - 相容性最佳（最高畫質通常只有 1080p）", "avc"),
            "2": ("H.265 (HEVC)", "hevc"),
            "3": ("VP9", "vp9"),
            "4": ("AV1 - 最新最高效", "av1"),
            "5": ("讓 yt-dlp 自動選擇最佳", "best")
        }
        print("請選擇偏好的 MP4 視訊編碼（若該影片不提供所選編碼，則改其他編碼）：")
        for key, (name, _) in codec_options.items():
            print(f"  {key}: {name}")

        while True:
            codec_choice_key = input("請輸入選項編號 (1-5)：").strip()
            if codec_choice_key in codec_options:
                chosen_codec_name, yt_codec_id = codec_options[codec_choice_key]
                print(f"已選擇：{chosen_codec_name}")
                break
            else:
                print("無效的選項編號，請重新輸入。")

        # 根據選擇的編碼構建格式字串，優先 AAC 音訊
        if yt_codec_id == "best":
             # 用戶選擇自動，使用 yt-dlp 預設，不特別處理音訊
            format_string = "bestvideo+bestaudio/best"
            print("\n準備下載 yt-dlp 判定的最高畫質視訊與最高音質音訊...")
            print("警告：此選項不保證音訊為 AAC，可能無法用 QuickTime 開啟。")
        else:
            # 用戶選擇了特定視訊編碼，優先搭配 AAC (m4a) 音訊
            # 格式說明：
            # 1. bestvideo[vcodec^=CODEC]+bestaudio[acodec=m4a]  -> 最佳選定視訊 + 最佳AAC音訊
            # 2. /bestvideo[vcodec^=CODEC]+bestaudio             -> 若無AAC，最佳選定視訊 + 任何最佳音訊
            # 3. /best[vcodec^=CODEC][acodec=m4a]                -> 若無分離流，嘗試預合併的 選定視訊+AAC音訊 檔案
            # 4. /best[vcodec^=CODEC]                           -> 若無預合併AAC，嘗試預合併的 選定視訊 檔案
            # 5. /bestvideo+bestaudio/best                     -> 若連選定視訊都找不到，回退到完全預設的最佳選擇
            format_string = (
                f"bestvideo[vcodec^={yt_codec_id}]+bestaudio[acodec=m4a]/"
                f"bestvideo[vcodec^={yt_codec_id}]+bestaudio/"
                f"best[vcodec^={yt_codec_id}][acodec=m4a]/"
                f"best[vcodec^={yt_codec_id}]/"
                f"bestvideo+bestaudio/best"
            )
            print(f"\n準備下載 {chosen_codec_name} 編碼的最佳視訊...")
            print("並優先嘗試搭配 AAC 音訊以獲得最佳 QuickTime 相容性。")
            if yt_codec_id != 'avc': # H.264 通常搭配 AAC，其他格式更可能遇到 Opus
                 print("如果找不到 AAC 音訊，會嘗試其他音訊格式 (可能影響 QuickTime 播放)。")
            print(f"如果找不到 {chosen_codec_name} 視訊，將嘗試下載其他可用最佳格式。")


        command.extend([
            "-f", format_string,            # 使用精心構造的格式選擇字串
            "--merge-output-format", "mp4", # 確保合併後的容器是 mp4
            video_url                       # 網址
        ])

    # --- 執行命令 ---
    print(f"\n將執行的命令：\n{' '.join(command)}") # 顯示完整命令方便除錯
    print("\n------ 開始執行 yt-dlp ------")
    try:
        # 使用 Popen 可以逐行讀取輸出，但這裡為了簡單，直接用 run
        process = subprocess.run(command, check=False, encoding='utf-8', errors='ignore') # 指定編碼避免解碼錯誤

        print("\n------ yt-dlp 執行完畢 ------")

        if process.returncode == 0:
            print("✅ 下載成功完成！")
        else:
            print(f"❌ 下載過程中發生錯誤。yt-dlp 返回代碼：{process.returncode}")
            print("請仔細檢查上面的 yt-dlp 輸出訊息以找出問題原因。")
            # 可以添加更具體的錯誤檢查，例如檢查 stderr 中是否有 "Requested format is not available"
            # if process.stderr and "requested format not available" in process.stderr.lower():
            #    print("錯誤提示：可能是您選擇的視訊編碼或與 AAC 音訊的組合在此影片中不可用。")

    except FileNotFoundError:
        print(f"❌ 致命錯誤：無法執行命令 'yt-dlp'。請確保已正確安裝並將其路徑加入系統 PATH。")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作被用戶中斷。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行過程中發生未預期的 Python 錯誤：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()