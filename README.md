# Manim Show

质数可视化项目集合 — 用 ManimGL 将数学之美转化为可观看的视频。

## 项目列表

### prime_spiral — 质数螺旋（2D 极坐标）

```
每个质数 p → 极坐标 (r=p, θ=p mod 2π)
```

质数在极坐标下并非随机分布——它们编织出螺旋纹理和射线状的纹路。外尔均布定理预言：质数模 2π 最终均匀铺满圆周。

| 参数 | 值 |
|------|-----|
| 质数范围 | 2 ~ 20 万 |
| 阶段 | teaser → 200 → 500 → 2000 → 8000 → 5w → 20w |
| 输出 | 1920×1080 横屏 |
| 旁白 | 中文 TTS + ASS 字幕 + BGM |

**文件**: `prime_spiral/scene.py` + `prime_spiral/add_narration.py`

### prime_sphere — 质数球坐标（3D 球坐标）

```
每个质数 p → 球坐标 (r∝p, θ=p mod 2π, φ=p mod π)
```

将质数从极坐标扩展到三维球坐标系。同样的映射逻辑下，3D 粒子云从随机散点渐变为带螺旋结构的立体漩涡，最后在外尔均布的作用下解体为均匀辐射的射线簇。

| 参数 | 值 |
|------|-----|
| 质数范围 | 2 ~ 20 万 |
| 阶段 | teaser(8000) → 200 → 500 → 2000 → 8000 → 5w → 20w |
| 颜色策略 | 每阶段叠加新颜色，旧层保留（6 种颜色） |
| 深度测试 | 全局关闭（粒子全部可见） |
| 输出 | 1920×1080 横屏 |
| 旁白 | 中文 TTS + ASS 字幕 + 星际穿越 BGM |

**文件**: `prime_sphere/scene.py` + `prime_sphere/add_narration.py`

## 环境依赖

```bash
pip install manimgl edge-tts sympy numpy
```

- **ManimGL** ≥ 1.7 — 3D 渲染引擎
- **edge-tts** — 微软 TTS 合成中文旁白
- **FFmpeg** (系统安装) — 音视频后期合成、字幕烧录

## 使用方式

```bash
# 1. 渲染动画（以 prime_sphere 为例）
cd prime_sphere
manimgl scene.py PrimeSphere -w --hd

# 2. 生成旁白 + 字幕 + BGM
python add_narration.py
```

竖屏 9:16 版本用 `-r 1080x1920` 替代 `--hd`。

## 旁白流水线

1. **edge-tts** 逐句合成 TTS 音频（zh-CN-XiaoxiaoNeural）
2. 在句子间插入静音间隙以对齐视觉节奏
3. 截取 BGM 匹配视频时长，混音（BGM -18dB + 旁白）
4. 生成 ASS 字幕（带 PlayRes 头），用 libass 烧录到视频

## 视频编辑踩坑

- **字幕必须用 ASS 格式**：SRT 没有 PlayRes 头，libass 默认 384×288 坐标系，MarginV 定位完全错乱
- **竖屏字幕位置**：需在底部平台 UI 栏以上（MarginV≥280），字体和位置需要多轮目视调整
- **`fix_in_frame()` 在大缩放下退化**：纹理质量急剧下降，大缩放前用 FadeOut 移除
- **深度测试关闭**：3D 场景中 `ThreeDScene.add()` 默认开启深度遮挡，需要重写 `add()` 方法绕过

## License

MIT
