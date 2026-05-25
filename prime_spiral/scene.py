"""质数螺旋可视化 — 极坐标下质数的隐藏秩序

核心：每个质数 p 对应唯一坐标 (r = p * SCALE, θ = p)。
相机拉远时，点半径和辉光按比例放大，保证始终可见。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from manimlib import *
import sympy as sp
import numpy as np
GLOBAL_SCALE = 40.0 / 50000  # p=50000 → r=40.0


def prime_point(p: int) -> list:
    r = p * GLOBAL_SCALE
    theta = p % TAU
    return [r * np.cos(theta), r * np.sin(theta), 0]


def dot_radius_for(cam_width: float) -> float:
    return cam_width * (24.0 + cam_width * 0.02) / 1920


def glow_for(cam_width: float) -> float:
    return 8.0 + cam_width * 0.04


class PrimeSpiral(Scene):
    def construct(self):
        limit_stage1 = 200
        limit_stage2 = 500
        limit_stage3 = 2000
        limit_stage4 = 8000
        limit_stage5 = 50000
        limit_stage6 = 200000

        GLOW_COLOR = "#00D4AA"
        SUBTLE = GREY

        self.camera.background_rgba = (0, 0, 0, 1)

        def vr(limit):
            return limit * GLOBAL_SCALE

        def make_glow(primes, cam_w, color=GLOW_COLOR):
            pts = [prime_point(p) for p in primes]
            return GlowDots(
                np.array(pts),
                color=color, radius=dot_radius_for(cam_w),
                glow_factor=glow_for(cam_w),
            )

        # ================================================================
        # 0. 开场钩子 — 先瞥一眼 8000 质数的螺旋全貌
        # ================================================================

        r_teaser = vr(limit_stage4)
        cam_teaser = r_teaser * 2.5
        self.camera.frame.set_width(cam_teaser)

        teaser_primes = list(sp.primerange(2, limit_stage4 + 1))
        teaser_dots = make_glow(teaser_primes, cam_teaser)
        teaser_label = Text("质数螺旋", font_size=72, color=WHITE)
        teaser_label.to_edge(UP, buff=0.6)
        teaser_label.fix_in_frame()

        self.play(FadeIn(teaser_dots), FadeIn(teaser_label), run_time=1.5)
        self.wait(1.5)
        self.play(FadeOut(teaser_dots), FadeOut(teaser_label), run_time=0.8)

        # ================================================================
        # 1. 开场 — 200 质数, 半径 0.16, 相机 0.48
        # ================================================================

        r1 = vr(limit_stage1)
        cam1 = r1 * 3.0
        self.camera.frame.set_width(cam1)

        primes1 = list(sp.primerange(2, limit_stage1 + 1))

        np.random.seed(42)
        random_points = []
        for _ in primes1:
            angle = np.random.uniform(0, TAU)
            dist = np.random.uniform(0, r1)
            random_points.append([dist * np.cos(angle), dist * np.sin(angle), 0])

        random_dots = GlowDots(
            np.array(random_points),
            color=SUBTLE, radius=dot_radius_for(cam1), glow_factor=2.5,
        )
        prime_dots_1 = make_glow(primes1, cam1)

        self.play(FadeIn(random_dots), run_time=2.0)
        self.wait(2.0)
        self.play(Transform(random_dots, prime_dots_1), run_time=3.0)
        self.wait(1.5)

        active_dots = [prime_dots_1]  # 追踪当前活跃的点集
        self.play(FadeOut(random_dots), run_time=1.0)

        # ================================================================
        # 2. 500 质数 + 网格, 半径 0.4, 相机 1.2
        # ================================================================

        r2 = vr(limit_stage2)
        cam2 = r2 * 3.0

        formula_label = Tex(
            r"r = p \qquad \theta = p \bmod 2\pi",
            font_size=30, color=WHITE,
        )
        formula_label.anti_alias_width = 2.0
        formula_label.to_edge(UP, buff=1.0)
        formula_label.fix_in_frame()


        primes2 = list(sp.primerange(2, limit_stage2 + 1))
        bands = [[], [], []]
        for p in primes2:
            r_val = p * GLOBAL_SCALE
            pt = prime_point(p)
            if r_val < r2 * 0.3:
                bands[0].append(pt)
            elif r_val < r2 * 0.6:
                bands[1].append(pt)
            else:
                bands[2].append(pt)

        colors = ["#FF6B6B", "#FFD93D", "#00D4AA"]
        dots_stage2 = Group(*[
            GlowDots(np.array(pts), color=colors[i],
                     radius=dot_radius_for(cam2), glow_factor=glow_for(cam2))
            for i, pts in enumerate(bands) if pts
        ])

        self.play(
            FadeOut(active_dots[0]),
            Write(formula_label),
            self.camera.frame.animate.set_width(cam2),
            FadeIn(dots_stage2),
            run_time=2.5,
        )
        active_dots = [dots_stage2]
        self.wait(1.0)

        self.wait(2.3)

        # ================================================================
        # 3. 第一次加量 — 2000 质数, 半径 1.6, 相机 4.0
        # ================================================================



        r3 = vr(limit_stage3)
        cam3 = r3 * 2.5
        primes3_all = list(sp.primerange(2, limit_stage3 + 1))
        new_dots_3 = make_glow(primes3_all, cam3)

        self.play(
            *[FadeOut(d) for d in active_dots],
            FadeIn(new_dots_3),
            self.camera.frame.animate.set_width(cam3),
            rate_func=rush_into,
            run_time=4.5,
        )
        active_dots = [new_dots_3]
        self.wait(2.5)

        # ================================================================
        # 4. 第二次加量 — 8000 质数, 半径 6.4, 相机 16.0
        # ================================================================

        r4 = vr(limit_stage4)
        cam4 = r4 * 2.5
        primes4_all = list(sp.primerange(2, limit_stage4 + 1))
        new_dots_4 = make_glow(primes4_all, cam4)

        self.play(
            *[FadeOut(d) for d in active_dots],
            FadeIn(new_dots_4),
            self.camera.frame.animate.set_width(cam4),
            rate_func=rush_into,
            run_time=4.5,
        )
        active_dots = [new_dots_4]
        self.wait(1.0)
        # 提前淡出 formula_label，避免 fix_in_frame 在后续相机缩放中产生尖刺
        self.play(FadeOut(formula_label), run_time=0.8)
        self.wait(1.0)

        # ================================================================
        # 5. 第三次加量 — 50000 质数, 半径 40.0, 相机 90.0
        # ================================================================

        r5 = vr(limit_stage5)
        cam5 = r5 * 2.25
        primes5_all = list(sp.primerange(2, limit_stage5 + 1))
        new_dots_5 = make_glow(primes5_all, cam5)

        self.play(
            *[FadeOut(d) for d in active_dots],
            FadeIn(new_dots_5),
            self.camera.frame.animate.set_width(cam5),
            rate_func=rush_into,
            run_time=5.0,
        )
        active_dots = [new_dots_5]

        self.wait(3.8)

        # ================================================================
        # 6. 第四次加量 — 200000 质数, 半径 160.0, 相机 576.0
        # ================================================================

        r6 = vr(limit_stage6)
        cam6 = r6 * 3.6
        primes6_all = list(sp.primerange(2, limit_stage6 + 1))
        new_dots_6 = make_glow(primes6_all, cam6)

        self.play(
            *[FadeOut(d) for d in active_dots],
            FadeIn(new_dots_6),
            self.camera.frame.animate.set_width(cam6),
            rate_func=rush_into,
            run_time=5.0,
        )
        active_dots = [new_dots_6]
        self.wait(2.8)

        # ================================================================
        # 8. 结尾
        # ================================================================

        self.play(
            *[FadeOut(m) for m in self.mobjects],
            run_time=2.0,
        )

        self.play(
            self.camera.frame.animate.set_width(14).move_to(ORIGIN),
            rate_func=overshoot,
            run_time=1.5,
        )

        self.wait(1.0)

        math_note = Tex(
            r"\theta = p \ (\text{mod } 2\pi)",
            font_size=56, color=WHITE,
        )
        math_note.anti_alias_width = 2.0
        math_note.move_to(ORIGIN + UP * 1.0)
        self.play(Write(math_note), run_time=2.0)

        explore = Tex(
            r"\text{Try: } (p^2,\; p),\; (p,\; \log p),\;\ldots",
            font_size=28, color=SUBTLE,
        )
        explore.next_to(math_note, DOWN, buff=0.8)
        self.play(FadeIn(explore), run_time=1.5)
        self.wait(3.5)


def build_scene(params: dict = None):
    return PrimeSpiral
