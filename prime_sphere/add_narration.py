"""
为 prime_sphere_v13.mp4 添加 TTS 旁白 + 字幕 + 星际穿越 BGM
"""
import asyncio
import subprocess
from pathlib import Path

import edge_tts

VIDEO = Path("D:/code/jianjicode-5/jianjicode/python/manim_templates/output/prime_sphere_v14.mp4")
OUTPUT = VIDEO.parent / "prime_sphere_v14_narrated.mp4"
FFMPEG = "d:/code/jianjicode-5/jianjicode/resources/ffmpeg/win32/ffmpeg.exe"
FFPROBE = "d:/softDownload/bin/ffprobe.exe"
BGM = "D:/code/jianjicode-5/music/1200可商用纯音乐/安静-舒缓/Interstellar Space.mp3"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+20%"

LINES = [
    "如果换个维度看质数，比如放进三维球坐标系——",
    "随机散落的点，毫无章法。",
    "给每个质数 p 赋予一个球坐标：半径正比于 p，角度也等于 p。",
    "同样的数字，只是换了排列规则，结构开始浮现。",
    "但凑近了看，好像也没什么特别的。",
    "把数量加上去：两千，八千。螺旋的旋臂结构开始成形。",
    "注意那些空白的缺口——它们像星系的旋臂一样，把质数编织成了立体的漩涡。",
    "现在纳入五万以内的全部质数。",
    "拉远之后，旋臂渐渐解体，取而代之的是向外辐射的密集射线簇。",
    "再扩大到二十万，射线愈加分明。",
    "外尔均布定理指出：质数模 2π，最终均匀分布在球面上。",
    "均匀性，愈加确凿。",
    "最混沌的数字，换个维度，竟呈现出宇宙般惊人的秩序。",
]

# 停顿对齐视觉节奏: teaser(0-4) → 随机(4-7) → 坐标(7-13) → 结构(13-18)→ 凑近(18-22)
# → 旋臂成形(22-28) → 旋臂缺口(28-36) → 五万(36-42) → 旋臂解体射线(42-49) → 二十万射线(49-55)
# → 外尔定理(55-62) → 均匀性(62-65) → 结尾秩序(65-72)
GAPS = [0.0, 0.5, 1.0, 0.0, 1.5, 1.5, 3.0, 0.0, 3.0, 4.0, 2.0, 2.5, 2.0]


async def synthesize(text: str, output_path: str) -> float:
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(output_path)
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", output_path],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip()) if result.returncode == 0 else 0.0


def _make_silence(dur: float, path: str):
    subprocess.run([FFMPEG, "-y", "-f", "lavfi",
                    "-i", f"anullsrc=r=24000:cl=mono",
                    "-t", str(dur), "-b:a", "48k", path],
                   check=True, capture_output=True)


async def main():
    temp_dir = VIDEO.parent / "tts_temp_sphere"
    temp_dir.mkdir(exist_ok=True)

    print("Step 1: TTS + silence gaps...")
    audio_files, durations = [], []
    for i, text in enumerate(LINES):
        path = str(temp_dir / f"n_{i:02d}.mp3")
        dur = await synthesize(text, path)
        durations.append(dur)
        audio_files.append(path)
        if i < len(GAPS) and GAPS[i] > 0:
            gap_path = str(temp_dir / f"gap_{i:02d}.mp3")
            _make_silence(GAPS[i], gap_path)
            audio_files.append(gap_path)
            durations.append(GAPS[i])

    timed = []
    t = 0.0
    line_idx = 0
    for i, af in enumerate(audio_files):
        if "gap_" in af:
            t += durations[i]
            continue
        s, e = t, t + durations[i]
        t = e
        timed.append((LINES[line_idx], round(s, 2), round(e, 2)))
        line_idx += 1

    concat = str(temp_dir / "files.txt")
    with open(concat, "w") as f:
        for af in audio_files:
            f.write(f"file '{af.replace(chr(92), '/')}'\n")
    merged = str(temp_dir / "narration.mp3")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
                    "-i", concat, "-c", "copy", merged], check=True)

    # Step 2: 获取视频时长, 截取 BGM
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(VIDEO)],
        capture_output=True, text=True, timeout=10,
    )
    video_dur = float(result.stdout.strip())

    bgm_trimmed = str(temp_dir / "bgm_trimmed.mp3")
    subprocess.run([
        FFMPEG, "-y", "-vn", "-i", BGM,
        "-t", str(video_dur),
        "-af", "afade=t=in:d=3,afade=t=out:st=" + str(video_dur - 4) + ":d=3",
        "-b:a", "192k", bgm_trimmed,
    ], check=True)

    # Step 3: 混合 BGM (降低音量作为背景) + 旁白
    mixed_audio = str(temp_dir / "mixed_audio.mp3")
    subprocess.run([
        FFMPEG, "-y", "-vn",
        "-i", bgm_trimmed,
        "-i", merged,
        "-filter_complex",
        "[0:a]volume=-18dB[bgm];[bgm][1:a]amix=inputs=2:duration=first:dropout_transition=3",
        "-b:a", "192k", mixed_audio,
    ], check=True)

    # Step 4: 合成视频 + 音频
    va = str(temp_dir / "va.mp4")
    subprocess.run([FFMPEG, "-y", "-i", str(VIDEO), "-i", mixed_audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", va], check=True)

    # Step 5: 生成 SRT 字幕
    single = _to_single(timed)
    srt = str(temp_dir / "subs.srt")
    with open(srt, "w", encoding="utf-8") as f:
        for i, (text, ts, te) in enumerate(single):
            f.write(f"{i+1}\n{_ts(ts)} --> {_ts(te)}\n{text}\n\n")

    # Step 6: 烧录字幕
    se = srt.replace("\\", "/").replace(":", "\\:")
    subprocess.run([
        FFMPEG, "-y", "-i", va, "-vf",
        f"subtitles='{se}':"
        f"force_style='FontName=Microsoft YaHei,FontSize=13,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"BackColour=&H80000000,BorderStyle=1,Outline=2,"
        f"Alignment=2,MarginV=40'",
        "-c:a", "copy", str(OUTPUT),
    ], check=True)

    print(f"SRT: {srt}")
    print(f"DONE -> {OUTPUT}")


def _to_single(segments):
    result = []
    for text, ts, te in segments:
        chunks = _chunk(text)
        if len(chunks) == 1:
            result.append((chunks[0], ts, te))
        else:
            total = sum(len(c) for c in chunks)
            dur = te - ts
            pos = ts
            for c in chunks:
                cd = dur * len(c) / total if total > 0 else dur / len(chunks)
                result.append((c, round(pos, 2), round(pos + cd, 2)))
                pos += cd
    return result


def _chunk(text: str) -> list:
    result = []
    cur = ""
    for ch in text:
        cur += ch
        if ch in "，。？；！、":
            result.append(cur)
            cur = ""
    if cur:
        result.append(cur)
    merged = []
    for c in result:
        if merged and len(merged[-1]) + len(c) <= 20:
            merged[-1] += c
        else:
            merged.append(c)
    return merged


def _ts(s: float) -> str:
    h, m = int(s // 3600), int((s % 3600) // 60)
    sec, ms = int(s % 60), int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


if __name__ == "__main__":
    asyncio.run(main())
