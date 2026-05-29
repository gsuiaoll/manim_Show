# ManimGL 视频制作流水线指南

基于 prime_spiral / prime_sphere / sphere_tetrahedron 三个项目的实战经验。

---

## 一、项目结构

每个项目目录的标准结构：

```
project_name/
├── scene.py              # ManimGL 场景代码
└── add_narration.py       # TTS + BGM + ASS字幕合成脚本
```

场景文件包含一个或多个类，约定 `if __name__ == "__main__"` 块调用 `build_scene()` 函数以支持参数化。

---

## 二、ManimGL 渲染

### 基本命令

```bash
# 横屏 16:9 (1920x1080)
manimgl scenes/xxx.py ClassName -w --hd

# 竖屏 9:16 (1080x1920)
manimgl scenes/xxx.py ClassName -w -r 1080x1920
```

### 摄像机控制

| 用法 | 代码 |
|------|------|
| 画面宽度 | `self.camera.frame.set_width(9)` 横屏 / `set_width(7)` 竖屏 |
| 视角 | `self.camera.frame.reorient(theta_degrees=-15, phi_degrees=65)` |
| 缓动冲入 | `self.play(self.camera.frame.animate.rush_into(...))` |
| 缓动退出 | `self.play(self.camera.frame.animate.rush_from(...))` |

缓动类型: `rush_into`, `rush_from`, `running_start`, `overshoot` — 比默认 smooth 更有镜头感。

### fix_in_frame 注意事项

```python
text.fix_in_frame()  # 固定在屏幕空间，不随相机移动/缩放
```

**关键限制**: 当相机缩放 >5x 时，`fix_in_frame` 纹理严重退化（锯齿/模糊）。大缩放前用 `FadeOut` 移除，或改用 FFmpeg ASS 在后期叠加。

### 拖尾效果

```python
from manimlib.utils.rate_functions import there_and_back

# TracedPath — 跟踪单点轨迹
trail = TracedPath(dot.get_center, stroke_width=2, stroke_opacity=0.6)

# TracingTail — 渐变描边尾部渐隐
TracingTail(mobject, time_traced=0.8, stroke_width=4, stroke_opacity=0.7)
```

### 色彩工具

```python
from manimlib.utils.color import get_colormap_list

colors = get_colormap_list(n, "viridis")  # 科学配色表
mob.set_color_by_gradient(color1, color2)  # 渐变着色
```

### 其他隐藏功能

| 效果 | 类/函数 |
|------|---------|
| 冲击波扩散 | `Broadcast(mob)` |
| 放大高亮淡入 | `FlashyFadeIn(mob)` |
| 波浪变形 | `ApplyWave(mob)` |
| 辉光点 | `GlowDot(point, radius=0.05, glow_factor=4.0, color=WHITE)` |

完整隐藏 API 文档: jianjicode 项目中 `python/manim_templates/HIDDEN_FEATURES.md`

---

## 三、ASS 字幕（关键！）

### 为什么必须用 ASS，不用 SRT

1. **FFmpeg drawtext 不支持 CJK** — Windows 上 libfreetype 对中文渲染不完整，显示为豆腐块。ASS 通过 libass + DirectWrite 正确渲染。
2. **SRT 没有 PlayRes 头** — libass 默认坐标系 384×288，MarginV=280 会让字幕飞出屏幕。ASS 强制声明分辨率。

### ASS 文件结构

```ini
[Script Info]
ScriptType: v4.00+
PlayResX: 1920     # 横屏
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, ...
Style: Default,Noto Sans SC,64,&H00FFFFFF,&H000000FF,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.50,0:00:04.00,Default,,0,0,0,,字幕文本
```

### Alignment 和 MarginV

| Alignment | 位置 | MarginV 含义 |
|-----------|------|-------------|
| 2 | 底部居中 | 距底部距离 |
| 8 | 顶部居中 | 距顶部距离 |

### 字体

- 用字体名称，不写路径 — libass 自动查找系统字体
- 中文推荐: `Noto Sans SC` 或 `Microsoft YaHei`
- 验证: FFmpeg 日志中出现 `Using font provider directwrite (with GDI)` + `fontselect: (Noto Sans SC, ...) -> NotoSansSC-Regular`

### FFmpeg 烧录字幕

```bash
ffmpeg -i video.mp4 -vf "ass='path/to/subs.ass'" -c:a copy output.mp4
```

### 多字幕流

用 `-filter_complex` 链式调用:

```bash
ffmpeg -i video.mp4 \
  -filter_complex "[0:v]ass='sub1.ass'[v1];[v1]ass='sub2.ass'[outv]" \
  -map "[outv]" -map 0:a output.mp4
```

---

## 四、TTS + BGM 合成流水线

### 工具链

- **edge-tts**: 微软 Edge TTS，免费，中文推荐 `zh-CN-XiaoxiaoNeural`
- **FFmpeg**: 音频混合、字幕烧录

### 标准步骤

```
1. edge_tts 逐句合成旁白音频
2. 生成静音间隙文件，插入句子之间
3. concat 所有音频片段
4. 截取 BGM 到视频时长，添加淡入淡出
5. BGM 降音量 (-20dB) + 旁白混音
6. 视频 + 混音合并
7. ASS 字幕烧录
```

### GAPS 数组

`GAPS[i]` = 第 i 句**之后**的静音时长（秒）。用于调整旁白节奏与动画同步。

### 时间同步策略

1. 先渲染纯动画（无文字叠加）
2. 独立运行 TTS + 字幕脚本
3. 用 GAPS 调整句子间停顿来对齐视觉事件
4. 时机敏感的数学公式叠加用 ASS，不用 ManimGL 渲染
5. 音视频 filter 合并到一个 `-filter_complex` 中（两个会互相覆盖）

---

## 五、横屏 → 竖屏适配

### 必须创建独立场景文件

直接复用横屏场景会导致:
- `fix_in_frame` 文字按 1920px 设计，在 1080px 宽竖屏上溢出
- `dot_radius_for` 等像素密度计算分母错误

### 竖屏调整清单

| 项目 | 横屏值 | 竖屏值 |
|------|--------|--------|
| camera width | 9 | 7 |
| font_size | 横屏基准 | ≈ 横屏 × 0.56 |
| PlayResX | 1920 | 1080 |
| PlayResY | 1080 | 1920 |
| MarginV (字幕位置) | 80 | 280~760 (需目视微调) |

### 字幕位置（竖屏关键）

竖屏字幕放画面下 1/3 处，不要太靠底部 — 抖音/TikTok 底部有信息栏（约 0-200px）会遮挡。

- Alignment=2, MarginV 起点约 280
- 用画面高度的 1/10 (≈192px) 作为调整步进
- **每版必须用户目视确认后微调**，没有万能值

### prime_sphere 竖屏实测案例

| 元素 | 横屏 | 竖屏 |
|------|------|------|
| teaser_label | 64 | 32 |
| formula_label | 28 | 18 |
| math_note | 48 | 28（拆 3 行竖排） |
| explore | 28 | 18 |
| 字幕 MarginV | 80 | 568（经 3 轮: 280→760→568） |

---

## 六、常见踩坑速查

| 问题 | 原因 | 解决 |
|------|------|------|
| 中文字幕豆腐块 | drawtext 不支持 CJK | 用 ASS + libass DirectWrite |
| 字幕飞出屏幕 | SRT 无 PlayRes 头 | 用 ASS，显式声明分辨率 |
| fix_in_frame 模糊 | 相机缩放 >5x | 大缩放前 FadeOut |
| 两个 -filter_complex 后一个失效 | FFmpeg 只认最后一个 | 合并到一个 filter_complex |
| 竖屏文字溢出 | 横屏 font_size 直接复用 | 创建独立竖屏场景，×0.56 |
| 旁白和画面对不上 | GAPS 位置理解反了 | GAPS[i] 是第 i 句**之后**的静音 |

---

## 七、环境依赖

| 工具 | 用途 | 版本/位置 |
|------|------|-----------|
| ManimGL | 数学动画渲染 | v1.7.2, pip install manimgl |
| FFmpeg | 视频编码/字幕烧录 | 8.1 essentials, 需包含 libass |
| edge-tts | TTS 语音合成 | pip install edge-tts |
| Noto Sans SC | 字幕字体 | 系统字体目录 |

ManimGL 最低渲染命令会自动打开预览窗口，加 `-w` 直接写入文件。
