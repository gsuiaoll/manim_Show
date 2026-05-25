"""质数球坐标 3D 可视化 — 渐进式构建 200→20w, 每层叠加新颜色

映射: r ∝ p, θ = p mod 2π, φ = p mod π
坐标: x = r·sin(φ)·cos(θ), y = r·sin(φ)·sin(θ), z = r·cos(φ)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from manimlib import *
import numpy as np
import sympy as sp

GLOBAL_SCALE = 40.0 / 50000  # p=50000 → r=40.0


def prime_point(p: int, max_p: float = 200000.0) -> list:
    """球坐标系 → 笛卡尔坐标"""
    r = p * GLOBAL_SCALE
    theta = p % TAU
    phi = p % PI
    sin_phi = np.sin(phi)
    return [
        r * np.cos(theta) * sin_phi,
        r * np.sin(theta) * sin_phi,
        r * np.cos(phi),
    ]


def dot_radius_for(cam_width: float) -> float:
    return cam_width * (56.0 + cam_width * 0.05) / 1920


def glow_for(cam_width: float) -> float:
    return 18.0 + cam_width * 0.10


def spherical_points_array(primes, max_p=200000.0):
    """向量化球坐标转换 — 返回 (n, 3) float32"""
    p = np.array(primes, dtype=np.float64)
    r = p * GLOBAL_SCALE
    theta = p % TAU
    phi = p % PI
    sin_phi = np.sin(phi)
    pts = np.column_stack([
        r * np.cos(theta) * sin_phi,
        r * np.sin(theta) * sin_phi,
        r * np.cos(phi),
    ]).astype(np.float32)
    return pts


def make_glow(primes, cam_w, color="#00D4AA", max_p=200000.0, brightness=1.0, use_shading=True):
    pts = spherical_points_array(primes, max_p)
    g = GlowDots(
        pts,
        color=color,
        radius=dot_radius_for(cam_w) * brightness,
        glow_factor=glow_for(cam_w) * brightness,
    )
    if use_shading:
        g.make_3d()
    return g


class PrimeSphere(ThreeDScene):
    def add(self, *mobjects):
        super(ThreeDScene, self).add(*mobjects)

    def construct(self):
        L1, L2, L3, L4, L5, L6 = 200, 500, 2000, 8000, 50000, 200000

        SUBTLE = GREY
        # 每层增量用不同颜色: 冷→暖, 叠加出层次
        C_TEASER = "#BBBBBB"
        C1 = "#5DADE2"
        C2 = "#00D4AA"
        C3 = "#F4D03F"
        C4 = "#F39C12"
        C5 = "#E74C3C"
        C6 = "#AF4CFF"

        self.camera.background_rgba = (0, 0, 0, 1)

        def vr(limit):
            return limit * GLOBAL_SCALE

        # ================================================================
        # 0. 开场钩子 — 8000 质数预览
        # ================================================================

        r_t = vr(L4)
        cam_t = r_t * 2.5
        self.camera.frame.set_width(cam_t)
        self.camera.frame.reorient(theta_degrees=-20, phi_degrees=65)

        teaser_dots = make_glow(
            list(sp.primerange(2, L4 + 1)), cam_t, color=C_TEASER, use_shading=False,
        )
        teaser_label = Text("质数螺旋 · 球坐标", font_size=64, color=WHITE)
        teaser_label.to_edge(UP, buff=0.6)
        teaser_label.fix_in_frame()

        self.play(FadeIn(teaser_dots), FadeIn(teaser_label), run_time=1.5)
        self.wait(1.5)
        self.play(FadeOut(teaser_dots), FadeOut(teaser_label), run_time=0.8)

        # ================================================================
        # 1. 200 质数 — 随机散点 → 球坐标 (浅蓝)
        # ================================================================

        r1 = vr(L1)
        cam1 = r1 * 3.0
        self.camera.frame.set_width(cam1)
        self.camera.frame.reorient(theta_degrees=-20, phi_degrees=65)

        primes1 = list(sp.primerange(2, L1 + 1))

        np.random.seed(42)
        random_points = []
        for _ in range(len(primes1)):
            u = np.random.uniform(0, 1)
            phi_rand = np.arccos(2 * u - 1)
            theta_rand = np.random.uniform(0, TAU)
            r_rand = np.random.uniform(0, r1)
            sin_p = np.sin(phi_rand)
            random_points.append([
                r_rand * np.cos(theta_rand) * sin_p,
                r_rand * np.sin(theta_rand) * sin_p,
                r_rand * np.cos(phi_rand),
            ])

        random_dots = GlowDots(
            np.array(random_points, dtype=np.float32),
            color=SUBTLE, radius=dot_radius_for(cam1), glow_factor=glow_for(cam1),
        )
        dots_1 = make_glow(primes1, cam1, color=C1, use_shading=False)

        self.play(FadeIn(random_dots), run_time=2.0)
        self.wait(2.0)
        self.play(Transform(random_dots, dots_1), run_time=3.0)
        self.wait(1.5)

        active_dots = [dots_1]
        self.play(FadeOut(random_dots), run_time=1.0)

        # ================================================================
        # 2. 201-500 增量 (青绿) + 公式
        # ================================================================

        r2 = vr(L2)
        cam2 = r2 * 3.0

        formula_label = Tex(
            r"r \propto p \qquad \theta = p \bmod 2\pi \qquad \phi = p \bmod \pi",
            font_size=28, color=WHITE,
        )
        formula_label.anti_alias_width = 2.0
        formula_label.to_edge(UP, buff=1.0)
        formula_label.fix_in_frame()

        dots_2 = make_glow(
            list(sp.primerange(L1 + 1, L2 + 1)), cam2, color=C2, use_shading=False,
        )

        self.play(
            Write(formula_label),
            self.camera.frame.animate.set_width(cam2),
            FadeIn(dots_2),
            run_time=2.5,
        )
        active_dots.append(dots_2)
        self.wait(3.3)

        # ================================================================
        # 3. 501-2000 增量 (金黄)
        # ================================================================

        r3 = vr(L3)
        cam3 = r3 * 2.5
        dots_3 = make_glow(
            list(sp.primerange(L2 + 1, L3 + 1)), cam3, color=C3, use_shading=False,
        )

        self.play(
            FadeIn(dots_3),
            self.camera.frame.animate.set_width(cam3),
            rate_func=smooth,
            run_time=4.5,
        )
        active_dots.append(dots_3)
        self.wait(2.5)

        # ================================================================
        # 4. 2001-8000 增量 (橙色) + 旋转
        # ================================================================

        r4 = vr(L4)
        cam4 = r4 * 2.5
        dots_4 = make_glow(
            list(sp.primerange(L3 + 1, L4 + 1)), cam4, color=C4, use_shading=False,
        )

        self.play(
            FadeIn(dots_4),
            self.camera.frame.animate.set_width(cam4),
            rate_func=smooth,
            run_time=4.5,
        )
        active_dots.append(dots_4)
        self.wait(1.0)

        self.play(
            self.camera.frame.animate.increment_euler_angles(
                dtheta=PI * 0.6, dphi=-10 * DEGREES
            ),
            run_time=3.0,
        )
        self.wait(0.5)

        self.play(FadeOut(formula_label), run_time=0.8)
        self.wait(1.0)

        # ================================================================
        # 5. 8001-50000 增量 (赤红)
        # ================================================================

        r5 = vr(L5)
        cam5 = r5 * 2.25
        dots_5 = make_glow(
            list(sp.primerange(L4 + 1, L5 + 1)), cam5,
            color=C5, brightness=50.0, use_shading=False,
        )

        self.play(
            FadeIn(dots_5),
            self.camera.frame.animate.set_width(cam5),
            rate_func=smooth,
            run_time=5.0,
        )
        active_dots.append(dots_5)

        self.play(
            self.camera.frame.animate.increment_euler_angles(
                dtheta=-PI * 0.8, dphi=-15 * DEGREES
            ),
            run_time=4.0,
        )
        self.wait(2.0)

        # ================================================================
        # 6. 50001-200000 增量 (紫色)
        # ================================================================

        r6 = vr(L6)
        cam6 = r6 * 3.6
        dots_6 = make_glow(
            list(sp.primerange(L5 + 1, L6 + 1)), cam6,
            color=C6, brightness=50.0, use_shading=False,
        )

        self.play(
            FadeIn(dots_6),
            self.camera.frame.animate.set_width(cam6),
            rate_func=smooth,
            run_time=5.0,
        )
        active_dots.append(dots_6)

        self.play(
            self.camera.frame.animate.increment_euler_angles(
                dtheta=TAU * 0.7, dphi=-25 * DEGREES
            ),
            run_time=6.0,
        )
        self.wait(4.0)

        # ================================================================
        # 7. 结尾 — 所有粒子淡出, 展示公式
        # ================================================================

        self.play(
            *[FadeOut(m) for m in self.mobjects],
            run_time=2.0,
        )

        self.camera.frame.set_width(14)
        self.camera.frame.reorient(theta_degrees=0, phi_degrees=75)
        self.camera.frame.move_to(ORIGIN)

        self.wait(1.0)

        math_note = Tex(
            r"r \propto p \qquad "
            r"\theta = p \ (\text{mod } 2\pi) \qquad "
            r"\phi = p \ (\text{mod } \pi)",
            font_size=48, color=WHITE,
        )
        math_note.anti_alias_width = 2.0
        math_note.move_to(ORIGIN + UP * 1.0)
        math_note.fix_in_frame()
        self.play(Write(math_note), run_time=2.0)

        explore = Text("球坐标下的质数粒子", font_size=28, color=GREY)
        explore.next_to(math_note, DOWN, buff=0.8)
        explore.fix_in_frame()
        self.play(FadeIn(explore), run_time=1.5)
        self.wait(3.5)


def build_scene(params: dict = None):
    return PrimeSphere
