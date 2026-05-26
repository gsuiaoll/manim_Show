"""
为 sphere_tetrahedron_raw_portrait.mp4 添加 TTS 旁白 + 字幕 + BGM (9:16 竖屏)
"""
import asyncio
import subprocess
from pathlib import Path

import edge_tts

VIDEO = Path("D:/code/jianjicode-5/jianjicode/python/manim_templates/output/sphere_tetrahedron_raw_portrait.mp4")
OUTPUT = VIDEO.parent / "sphere_tetrahedron_final_portrait.mp4"
FFMPEG = "d:/code/jianjicode-5/jianjicode/resources/ffmpeg/win32/ffmpeg.exe"
FFPROBE = "d:/softDownload/bin/ffprobe.exe"
BGM = "D:/code/jianjicode-5/music/1200可商用纯音乐/安静-舒缓/Melancholy Tune.mp3"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+15%"

LINES = [
    "在球面上随机取四个点，连成一个四面体。",
    "这个四面体包含球心的概率，你觉得有多大？",
    "试几次看看：包含。这次不包含。包含。又不包含。",
    "完全随机，毫无规律——该从哪里入手？",
    "数学家会先降维：把三维球面，压扁成二维的圆。",
    "问题变成：圆周上三点构成的三角形，包含圆心的概率。",
    "固定两个点，只让第三个点沿圆周移动。",
    "只有当第三点落在对面这段弧上，三角形才会包含圆心。",
    "两点夹角越大，有效弧就越长——恰好占四分之一圆周。",
    "回到三维，同样的逻辑，多一个维度——答案是八分之一。",
]

GAPS = [0.0, 2.5, 2.0, 0.5, 2.0, 0.0, 0.0, 0.0, 3.0, 2.5]


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
    temp_dir = VIDEO.parent / "tts_temp_tetrahedron_portrait"
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
        "[0:a]volume=-20dB[bgm];[bgm][1:a]amix=inputs=2:duration=first:dropout_transition=3",
        "-b:a", "192k", mixed_audio,
    ], check=True)

    # Step 4: 合成视频 + 音频
    va = str(temp_dir / "va.mp4")
    subprocess.run([FFMPEG, "-y", "-i", str(VIDEO), "-i", mixed_audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", va], check=True)

    # Step 5: 生成 ASS 字幕 (竖屏 1080x1920)
    single = _to_single(timed)
    ass = str(temp_dir / "subs.ass")
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n")
        f.write("WrapStyle: 2\n")
        f.write("\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,Noto Sans SC,52,&H00FFFFFF,&H000000FF,"
                "&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,"
                "2,10,10,420,1\n")
        f.write("\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for i, (text, ts, te) in enumerate(single):
            start = _ts_ass(ts)
            end = _ts_ass(te)
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    # Step 6: 烧录字幕
    se = ass.replace("\\", "/").replace(":", "\\:")
    subprocess.run([
        FFMPEG, "-y", "-i", va, "-vf",
        f"ass='{se}'",
        "-c:a", "copy", str(OUTPUT),
    ], check=True)

    print(f"ASS: {ass}")
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


def _ts_ass(s: float) -> str:
    h, m = int(s // 3600), int((s % 3600) // 60)
    sec = s % 60
    return f"{h:01d}:{m:02d}:{sec:05.2f}"


if __name__ == "__main__":
    asyncio.run(main())
