"""
为 PrimeSpiral.mp4 添加 TTS 旁白 + Weyl ASS 字幕 + BGM (v15)
- Weyl 公式用 ASS 字幕（中文不豆腐块）替代 FFmpeg drawtext
- filter_complex 同时烧录旁白 SRT 和 Weyl ASS
- 一步输出最终视频
"""
import asyncio
import subprocess
from pathlib import Path

import edge_tts

VIDEO = Path("D:/code/jianjicode-5/jianjicode/python/manim_templates/videos/PrimeSpiral.mp4")
OUTPUT = VIDEO.parent / "PrimeSpiral_v15_final.mp4"
BGM = Path("D:/code/jianjicode-5/jianjicode/boss.mp3")
FFMPEG = "D:/code/jianjicode-5/jianjicode/node_modules/ffmpeg-static/ffmpeg.exe"
FFPROBE = "D:/softDownload/bin/ffprobe.exe"
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+20%"

LINES = [
    "我第一次看到这个图案，是在一个数学论坛的提问里。",
    "有人把质数画在了极坐标上：半径取p，角度也取p。",
    "乍一看简直是一团乱麻。质数本来最让人捉摸不透。",
    "但是，稍微拉远一点……",
    "两千以内的质数，杂乱的点竟自动编织成了螺旋。",
    "推到八千，螺旋纹理越来越密，像极了遥远的星系。",
    "有些方向形成了空白旋臂——那些角度只对应合数。",
    "现在纳入五万以内的全部质数，继续拉远。",
    "外尔均布定理：质数模2π，最终会均匀分布在圆周上。",
    "再扩大到二十万，螺旋终于解体。",
    "取而代之的是向外辐射的密集射线簇，均匀性愈加确凿。",
    "最混沌的数字，换个维度，竟呈现出宇宙般惊人的秩序。",
]

GAPS = [0.0, 0.0, 0.5, 0.0, 2.0, 2.0, 0.5, 0.8, 0.0, 0.0, 4.5]


def weyl_ass() -> str:
    """生成 Weyl 公式 ASS 字幕 — 顶部三行不重叠，38.5-42s，淡入淡出"""
    start = "0:00:38.50"
    end = "0:00:42.00"
    return f"""[Script Info]
Title: Weyl Formula Overlay
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: WeylTitle,Microsoft YaHei,72,&H00FFFFFF,&H00000000,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,8,10,10,180,1
Style: WeylMath,Microsoft YaHei,63,&H00FFFFFF,&H00000000,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,8,10,10,320,1
Style: WeylSub,Microsoft YaHei,51,&H00BBBBBB,&H00000000,&H00000000,&H80000000,0,1,0,0,100,100,0,0,1,2,0,8,10,10,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{start},{end},WeylTitle,,0,0,0,,{{\\fad(500,500)}}外尔均布定理
Dialogue: 1,{start},{end},WeylMath,,0,0,0,,{{\\fad(500,500)}}p mod 2π → Uniform(0, 2π)
Dialogue: 1,{start},{end},WeylSub,,0,0,0,,{{\\fad(500,500)}}Weyl Equidistribution
"""


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
    if dur <= 0:
        return
    subprocess.run([FFMPEG, "-y", "-f", "lavfi",
                    "-i", f"anullsrc=r=24000:cl=mono",
                    "-t", str(abs(dur)), "-b:a", "48k", path],
                   check=True, capture_output=True)


def _make_srt(segments: list) -> str:
    single = _to_single(segments)
    lines = []
    for i, (text, ts, te) in enumerate(single):
        lines.append(f"{i+1}\n{_ts(ts)} --> {_ts(te)}\n{text}\n")
    return "".join(lines)


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
        if ch in "，。？；！、：" or cur.endswith("——"):
            result.append(cur)
            cur = ""
    if cur:
        result.append(cur)
    merged = []
    for c in result:
        if merged and len(merged[-1]) + len(c) <= 16:
            merged[-1] += c
        else:
            merged.append(c)
    return merged


def _ts(s: float) -> str:
    h, m = int(s // 3600), int((s % 3600) // 60)
    sec, ms = int(s % 60), int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def _ts_ass(s: float) -> str:
    h, m = int(s // 3600), int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


async def main():
    temp_dir = VIDEO.parent / "tts_temp_v15"
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
            t += abs(durations[i])
            continue
        s, e = t, t + durations[i]
        t = e
        timed.append((LINES[line_idx], round(s, 2), round(e, 2)))
        line_idx += 1

    print("\nNarration timeline:")
    for text, ts, te in timed:
        print(f"  {ts:6.1f}s - {te:6.1f}s  {text}")

    concat = str(temp_dir / "files.txt")
    with open(concat, "w") as f:
        for af in audio_files:
            f.write(f"file '{af.replace(chr(92), '/')}'\n")
    merged_audio = str(temp_dir / "full.mp3")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
                    "-i", concat, "-c", "copy", merged_audio], check=True)

    va = str(temp_dir / "va.mp4")
    subprocess.run([FFMPEG, "-y", "-i", str(VIDEO), "-i", merged_audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", va], check=True)

    print("\nStep 2: Generate subtitle files...")
    # 旁白 SRT
    srt_content = _make_srt(timed)
    srt_path = str(temp_dir / "narration.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # Weyl ASS
    ass_path = str(temp_dir / "weyl.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(weyl_ass())

    print(f"  SRT: {srt_path}")
    print(f"  ASS: {ass_path}")

    print("\nStep 3: Burn both subtitles + mix BGM...")
    # 用 filter_complex 同时应用旁白 SRT 和 Weyl ASS
    srt_esc = srt_path.replace("\\", "/").replace(":", "\\:")
    ass_esc = ass_path.replace("\\", "/").replace(":", "\\:")

    srt_style = (
        "FontName=Microsoft YaHei,FontSize=11,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BackColour=&H80000000,BorderStyle=1,Outline=2,"
        "Alignment=2,MarginV=20"
    )

    filter_complex = (
        f"[0:v]subtitles='{srt_esc}':"
        f"force_style='{srt_style}'[v1];"
        f"[v1]subtitles='{ass_esc}'[outv];"
        f"[1:a]volume=0.18[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=shortest[outa]"
    )

    subprocess.run([
        FFMPEG, "-y", "-i", va, "-i", str(BGM),
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(OUTPUT),
    ], check=True)

    print(f"\nDONE -> {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
