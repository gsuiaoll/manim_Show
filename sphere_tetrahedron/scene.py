"""球面随机四点四面体包含球心概率 — 3B1B 风格钩子短片 (v2)

改进:
1. 玻璃球体 (多层透明 + 线框 + 发光球心)
2. 半透明四面体面 (Polygon低透明度)
3. 蒙特卡洛采样 (4次快速重采样,绿/红反馈)
4. 连续 3D→2D 压扁 (apply_function Z轴塌缩)
5. 动态 P3 扫描 (实时包含判定 + TracedPath留痕)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from manimlib import *
import numpy as np

SPHERE_R = 2.0

# ── helpers ──────────────────────────────────────────────────

def _rand_sphere(n=1, r=SPHERE_R):
    pts = np.random.randn(n, 3)
    pts = pts / np.linalg.norm(pts, axis=1, keepdims=True) * r
    return pts if n > 1 else pts[0]


def _tet_contains_origin(a, b, c, d):
    M = np.column_stack([a, b, c, d])
    try:
        A = np.vstack([M, np.ones(4)])
        rhs = np.array([0.0, 0, 0, 1])
        w = np.linalg.solve(A, rhs)
        return bool(np.all(w > 1e-8))
    except np.linalg.LinAlgError:
        return False


def _tri_contains_origin(a, b, c):
    M = np.column_stack([a[:2], b[:2], c[:2]])
    try:
        A = np.vstack([M, np.ones(3)])
        rhs = np.array([0.0, 0, 1])
        w = np.linalg.solve(A, rhs)
        return bool(np.all(w > 1e-8))
    except np.linalg.LinAlgError:
        return False


def _build_tet_edges(verts, color=WHITE, width=0.04):
    edges = []
    for i, j in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]:
        edges.append(Line3D(verts[i], verts[j], width=width, color=color))
    return edges


def _build_tet_faces(verts, color="#00D4AA", opacity=0.12):
    """Create semi-transparent triangular faces for tetrahedron."""
    face_indices = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    faces = VGroup()
    for i, j, k in face_indices:
        faces.add(Polygon(
            verts[i], verts[j], verts[k],
            color=color, fill_opacity=opacity, stroke_width=0,
        ))
    return faces


def _circle_pt(angle, r=2.0):
    return np.array([r * np.cos(angle), r * np.sin(angle), 0.0])


def _flatten_z(p):
    return np.array([p[0], p[1], 0.0])


def _build_meridians(radius=SPHERE_R, n=18, color=WHITE, opacity=0.22, width=0.8):
    """Smooth great-circle arcs from north pole to south pole."""
    meridians = VGroup()
    for i in range(n):
        theta = i * TAU / n
        pts = []
        for phi in np.linspace(0, PI, 80):
            pts.append([
                radius * np.sin(phi) * np.cos(theta),
                radius * np.sin(phi) * np.sin(theta),
                radius * np.cos(phi),
            ])
        curve = VMobject()
        curve.set_style(
            stroke_color="#FFFFFF",
            stroke_width=width,
            stroke_opacity=opacity,
            fill_opacity=0,
        )
        curve.set_points_as_corners(pts)
        meridians.add(curve)
    return meridians


def _build_parallels(radius=SPHERE_R, n=10, color=WHITE, opacity=0.22, width=0.8):
    """Smooth latitude circles (skip poles for cleanliness)."""
    parallels = VGroup()
    for i in range(1, n):
        lat = -PI / 2 + i * PI / n
        r = radius * np.cos(lat)
        z = radius * np.sin(lat)
        circle = Circle(
            radius=r,
            stroke_color="#FFFFFF",
            stroke_width=width,
            stroke_opacity=opacity,
            fill_opacity=0,
        )
        circle.shift(z * OUT)
        parallels.add(circle)
    return parallels


class SphereTetrahedron(ThreeDScene):
    def __init__(self, portrait: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._portrait = portrait

    def add(self, *mobjects):
        # Bypass depth test
        super(ThreeDScene, self).add(*mobjects)

    def construct(self):
        self.camera.background_rgba = (0, 0, 0, 1)
        self.camera.frame.set_width(7 if self._portrait else 9)
        self.camera.frame.reorient(theta_degrees=-15, phi_degrees=65)

        # ═══════════════════════════════════════════════════════════
        # Stage 0: 球体立即出现 + 开场标题叠在上面
        # ═══════════════════════════════════════════════════════════
        sphere_inner = Sphere(radius=SPHERE_R, resolution=(40, 20),
                              color="#4488AA", depth_test=False)
        sphere_inner.set_opacity(0.12)
        meridians = _build_meridians()
        parallels = _build_parallels()
        core = GlowDot(ORIGIN, color=WHITE, radius=0.05, glow_factor=4.0)

        self.add(sphere_inner, meridians, parallels, core)

        title = Text("球面上的四面体", font_size=44, color=WHITE)
        title.to_edge(UP, buff=0.6)
        title.fix_in_frame()
        sub = Text("4 random points on a sphere → tetrahedron", font_size=20, color=GREY)
        sub.next_to(title, DOWN, buff=0.25)
        sub.fix_in_frame()

        self.play(Write(title), FadeIn(sub), run_time=1.5)
        self.wait(0.3)

        # ═══════════════════════════════════════════════════════════
        # Stage 1: 四面体
        # ═══════════════════════════════════════════════════════════
        np.random.seed(42)
        while True:
            v = _rand_sphere(4)
            vol = abs(np.dot(v[1] - v[0], np.cross(v[2] - v[0], v[3] - v[0]))) / 6
            if vol > 0.5:
                break

        dots = [GlowDot(pt, color="#00D4AA", radius=0.06, glow_factor=2.5) for pt in v]
        edges = _build_tet_edges(v)
        faces = _build_tet_faces(v)

        self.play(FadeOut(title), FadeOut(sub), run_time=0.5)
        for i, dot in enumerate(dots):
            self.play(FadeIn(dot), run_time=0.35)
        self.play(FadeIn(faces), run_time=0.6)
        self.play(*[ShowCreation(e) for e in edges], run_time=1.0)

        # ═══════════════════════════════════════════════════════════
        # Stage 2: 提问 + 旋转展示
        # ═══════════════════════════════════════════════════════════
        question = Text("包含球心的概率是多少？", font_size=32, color=WHITE)
        question.to_edge(UP, buff=0.5)
        question.fix_in_frame()
        self.play(Write(question), run_time=1.0)

        self.play(
            self.camera.frame.animate.increment_euler_angles(
                dtheta=PI * 0.35, dphi=-5 * DEGREES),
            run_time=3.0,
        )
        self.wait(0.3)

        # ═══════════════════════════════════════════════════════════
        # Stage 3: 蒙特卡洛采样 — 快速重采样建立直觉
        # ═══════════════════════════════════════════════════════════
        self.play(FadeOut(question), run_time=0.4)
        self.play(FadeOut(faces), *[FadeOut(e) for e in edges],
                  *[FadeOut(d) for d in dots], run_time=0.5)

        mc_title = Text("直觉上，你觉得概率有多大？", font_size=28, color=WHITE)
        mc_title.to_edge(UP, buff=0.5)
        mc_title.fix_in_frame()
        self.play(Write(mc_title), run_time=0.8)

        mc_seeds = [7, 13, 42, 77]
        mc_last = None  # track last batch for cleanup
        for idx, seed in enumerate(mc_seeds):
            np.random.seed(seed)
            mv = _rand_sphere(4)
            contains = _tet_contains_origin(*mv)
            mc_color = "#00FF88" if contains else "#FF4466"
            mc_dots = [GlowDot(pt, color=mc_color, radius=0.06, glow_factor=2.5) for pt in mv]
            mc_edges = _build_tet_edges(mv, color=mc_color)
            mc_faces = _build_tet_faces(mv, color=mc_color, opacity=0.18)

            # 快速出现
            self.play(
                *[FadeIn(d) for d in mc_dots],
                FadeIn(mc_faces),
                *[ShowCreation(e) for e in mc_edges],
                run_time=0.6,
            )
            self.wait(0.3)
            # 快速消失 (保留最后一个)
            if idx < len(mc_seeds) - 1:
                self.play(
                    *[FadeOut(d) for d in mc_dots],
                    FadeOut(mc_faces),
                    *[FadeOut(e) for e in mc_edges],
                    run_time=0.35,
                )
            else:
                mc_last = (mc_dots, mc_faces, mc_edges)

        self.wait(0.6)
        self.play(FadeOut(mc_title), run_time=0.4)

        # 清除最后一个蒙特卡洛样本
        if mc_last:
            ld, lf, le = mc_last
            self.play(
                *[FadeOut(d) for d in ld], FadeOut(lf),
                *[FadeOut(e) for e in le],
                run_time=0.5,
            )

        # ═══════════════════════════════════════════════════════════
        # Stage 4: 认知冲突 → 3D → 2D 连续压扁
        # ═══════════════════════════════════════════════════════════
        how = Text("该从哪里入手？", font_size=34, color="#F4D03F")
        how.to_edge(UP, buff=0.5)
        how.fix_in_frame()
        hint = Text("试试更简单的情况", font_size=26, color=GREY)
        hint.next_to(how, DOWN, buff=0.35)
        hint.fix_in_frame()

        self.play(Write(how), run_time=0.7)
        self.wait(0.3)
        self.play(FadeIn(hint), run_time=0.6)
        self.wait(1.2)
        self.play(FadeOut(how), FadeOut(hint), run_time=0.5)

        # ── 连续 3D → 2D 过渡 (不硬切!) ──
        # 第一步: 相机转到俯视
        dim_label = Text("把 3D 球面压扁成 2D 圆", font_size=26, color=WHITE)
        dim_label.to_edge(UP, buff=0.45)
        dim_label.fix_in_frame()

        self.play(
            self.camera.frame.animate.reorient(theta_degrees=0, phi_degrees=6),
            run_time=2.0,
        )
        self.play(Write(dim_label), run_time=0.8)

        # 第二步: 将球体沿 Z 轴压扁 (核心! 连续形变)
        self.play(
            sphere_inner.animate.apply_function(_flatten_z),
            meridians.animate.apply_function(_flatten_z),
            parallels.animate.apply_function(_flatten_z),
            run_time=2.5,
        )
        self.wait(0.5)

        # ═══════════════════════════════════════════════════════════
        # Stage 5: 2D 圆 + 三角形 + 动态 P₃ 扫描
        # ═══════════════════════════════════════════════════════════
        self.play(FadeOut(dim_label), run_time=0.4)

        # 选 3 个圆上点
        c_pts = np.array([
            _circle_pt(0.28 * TAU),
            _circle_pt(0.62 * TAU),
            _circle_pt(0.85 * TAU),
        ])
        c_dots = [
            GlowDot(pt, color="#00D4AA", radius=0.08, glow_factor=3.5)
            for pt in c_pts
        ]
        c_labels = VGroup(*[
            Tex(f"P_{{{i+1}}}", font_size=26, color=WHITE)
            for i in range(3)
        ])
        for i, lb in enumerate(c_labels):
            lb.next_to(c_dots[i], c_pts[i] * 0.35, buff=0.10)
            lb.fix_in_frame()

        # 三角形 (初始)
        tri_fill = Polygon(
            c_pts[0], c_pts[1], c_pts[2],
            color="#00D4AA", fill_opacity=0.12, stroke_width=0,
        )
        tri_edges = VGroup(*[
            Line(c_pts[i][:2], c_pts[j][:2], color=WHITE, stroke_width=2.0)
            for i, j in [(0, 1), (1, 2), (2, 0)]
        ])

        self.play(
            *[FadeIn(d) for d in c_dots], FadeIn(c_labels),
            FadeIn(tri_fill), ShowCreation(tri_edges), run_time=1.5,
        )

        dim_sub = Text("三角形包含圆心的概率是多少？", font_size=20, color=GREY)
        dim_sub.to_edge(UP, buff=0.45)
        dim_sub.fix_in_frame()
        self.play(FadeIn(dim_sub), run_time=1.0)
        self.wait(1.5)

        # ── 固定 P₁ P₂，动态 P₃ ──
        self.play(FadeOut(dim_sub), run_time=0.4)

        fix_text = Text("固定 P₁ 和 P₂，只让 P₃ 变化", font_size=26, color=WHITE)
        fix_text.to_edge(UP, buff=0.45)
        fix_text.fix_in_frame()
        self.play(Write(fix_text), run_time=0.8)

        # 高亮 P₁, P₂
        self.play(
            c_dots[0].animate.set_color("#F4D03F"),
            c_dots[1].animate.set_color("#F4D03F"),
            c_labels[0].animate.set_color("#F4D03F"),
            c_labels[1].animate.set_color("#F4D03F"),
            run_time=0.5,
        )

        # 有效弧
        t1, t2 = 0.28 * TAU, 0.62 * TAU
        mid = (t1 + t2) / 2
        valid_start = mid + PI
        valid_len = t2 - t1
        valid_end = valid_start + valid_len

        # 预制有效弧 (P₃ 移动后再高亮)
        arc = Arc(radius=SPHERE_R, start_angle=valid_start, angle=valid_len,
                  color="#00D4AA", stroke_width=5)

        # P₃ 沿圆移动 + 实时判定
        p3_tracker = ValueTracker(t1 + 0.15)

        def _get_p3():
            return _circle_pt(p3_tracker.get_value())

        # 动态三角形面 (颜色随包含判定变化)
        dyn_fill = always_redraw(lambda: Polygon(
            c_pts[0], c_pts[1], _get_p3(),
            color="#00D4AA" if _tri_contains_origin(c_pts[0], c_pts[1], _get_p3())
            else "#E74C3C",
            fill_opacity=0.18, stroke_width=0,
        ))
        # 动态连线 P₁-P₃ 和 P₂-P₃
        dyn_edge_13 = always_redraw(
            lambda: Line(c_pts[0][:2], _get_p3()[:2], color=WHITE, stroke_width=2.0)
        )
        dyn_edge_23 = always_redraw(
            lambda: Line(c_pts[1][:2], _get_p3()[:2], color=WHITE, stroke_width=2.0)
        )

        # TracedPath 留痕 (有效区域)
        trace = TracedPath(
            lambda: _get_p3(),
            stroke_color="#00D4AA",
            stroke_width=6,
        )

        moving_dot = always_redraw(
            lambda: GlowDot(_get_p3(), color="#E74C3C", radius=0.10, glow_factor=4.0)
        )
        moving_label = always_redraw(
            lambda: Tex("P_3", font_size=26, color="#E74C3C")
            .next_to(_get_p3(), _get_p3() * 0.35, buff=0.10)
            .fix_in_frame()
        )

        self.add(trace, dyn_fill, dyn_edge_13, dyn_edge_23, moving_dot, moving_label)
        self.play(
            FadeOut(c_dots[2]), FadeOut(c_labels[2]),
            FadeOut(tri_fill),
            FadeOut(tri_edges[1]), FadeOut(tri_edges[2]),
            run_time=0.3,
        )

        # P₃ 沿圆移动 — 第一段: 进入有效区域
        self.play(p3_tracker.animate.set_value(valid_start + 0.4), run_time=2.5,
                  rate_func=smooth)
        self.wait(0.3)
        # P₃ 继续 — 穿越有效区域
        self.play(p3_tracker.animate.set_value(valid_end - 0.4), run_time=2.0,
                  rate_func=smooth)
        self.wait(0.5)

        # 高亮有效弧
        self.play(ShowCreation(arc), run_time=0.8)
        arc_label = Text("有效区域 = 1/4 圆弧", font_size=18, color="#00D4AA")
        arc_center_angle = valid_start + valid_len / 2
        arc_label.next_to(
            _circle_pt(arc_center_angle) * 1.38, ORIGIN, buff=0.1,
        )
        arc_label.fix_in_frame()
        self.play(FadeIn(arc_label), run_time=0.5)
        self.wait(1.2)

        # ═══════════════════════════════════════════════════════════
        # Stage 6: 揭示 2D 答案
        # ═══════════════════════════════════════════════════════════
        self.play(FadeOut(fix_text), run_time=0.4)

        ans2d = Text("2D 答案是 1/4", font_size=40, color="#00D4AA")
        ans2d.to_edge(UP, buff=0.45)
        ans2d.fix_in_frame()
        self.play(Write(ans2d), run_time=0.9)
        self.wait(1.5)

        # ═══════════════════════════════════════════════════════════
        # Stage 7: 升回 3D + 悬念结尾
        # ═══════════════════════════════════════════════════════════
        # always_redraw objects can't be FadeOut'd — remove them directly
        self.remove(dyn_fill, dyn_edge_13, dyn_edge_23, moving_dot, moving_label)
        self.remove(trace)
        self.play(
            FadeOut(ans2d), FadeOut(arc), FadeOut(arc_label),
            FadeOut(c_dots[0]), FadeOut(c_dots[1]),
            FadeOut(c_labels[0]), FadeOut(c_labels[1]),
            FadeOut(tri_edges[0]),
            run_time=0.6,
        )

        # 重置 3D 球体 + 四面体
        self.play(
            sphere_inner.animate.apply_function(lambda p: np.array([p[0], p[1], 0.0])),
            meridians.animate.apply_function(lambda p: np.array([p[0], p[1], 0.0])),
            parallels.animate.apply_function(lambda p: np.array([p[0], p[1], 0.0])),
            run_time=0.01,  # instant reset (they're already flat)
        )
        # Fade out flattened disc
        self.play(FadeOut(sphere_inner), FadeOut(meridians), FadeOut(parallels), FadeOut(core),
                  run_time=0.5)

        # 恢复 3D 视角
        self.camera.frame.set_width(9)
        self.camera.frame.reorient(theta_degrees=-10, phi_degrees=65)

        # 新玻璃球体
        sphere2 = Sphere(radius=SPHERE_R, resolution=(40, 20),
                         color="#4488AA", depth_test=False)
        sphere2.set_opacity(0.15)
        meridians2 = _build_meridians()
        parallels2 = _build_parallels()
        core2 = GlowDot(ORIGIN, color=WHITE, radius=0.05, glow_factor=4.0)

        np.random.seed(99)
        v2 = _rand_sphere(4)
        dots2 = [GlowDot(pt, color="#00D4AA", radius=0.06, glow_factor=2.5) for pt in v2]
        edges2 = _build_tet_edges(v2)
        faces2 = _build_tet_faces(v2)

        self.play(
            FadeIn(sphere2), FadeIn(meridians2), FadeIn(parallels2), FadeIn(core2),
            *[FadeIn(d) for d in dots2],
            FadeIn(faces2),
            *[ShowCreation(e) for e in edges2],
            run_time=1.5,
        )

        cliff = Text("那么 3D 呢？答案是 1/8", font_size=36, color=WHITE)
        cliff.to_edge(UP, buff=0.45)
        cliff.fix_in_frame()
        self.play(Write(cliff), run_time=1.2)
        self.wait(0.5)

        self.play(
            self.camera.frame.animate.increment_euler_angles(
                dtheta=PI * 0.5, dphi=-8 * DEGREES),
            run_time=4.0,
        )
        self.wait(2.0)


class SphereTetrahedronPortrait(SphereTetrahedron):
    def __init__(self, **kwargs):
        super().__init__(portrait=True, **kwargs)


def build_scene(params: dict = None):
    portrait = params.get("portrait", False) if params else False
    return SphereTetrahedron(portrait=portrait)
