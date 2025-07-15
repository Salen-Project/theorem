
import sys
import os
# Adjust sys.path so that the "src" directory (which contains our utils) can be found.
# Updated the relative path to correctly reference the directory containing the "utils" folder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from manim import *
from manim import config as global_config
from manim_voiceover import VoiceoverScene
from utils.kokoro_voiceover import KokoroService  # Updated import to reflect new sys.path

# Plugin imports (if any additional plugin is used, they are imported here)
from manim_circuit import *
from manim_physics import *
from manim_chemistry import *
from manim_dsa import *
from manim_ml import *
import numpy as np

# Helper Functions/Classes (Implement and use helper classes and functions for improved code reusability and organization)
class Scene3_Helper:
    # Helper class containing utility functions for Scene 3 (Angle Variations).
    def __init__(self, scene):
        self.scene = scene

    def create_triangle_group(self, vertices, label_text, marker_type, marker_vertex_index):
        """
        Create a VGroup containing a triangle, an angle marker (arc or square),
        and a Tex label. The triangle is defined by its vertices.
        
        marker_type: "arc" for acute/obtuse, or "square" for right-angle marker.
        marker_vertex_index: index of the vertex (in vertices list) where the marker attaches.
        
        All internal object positions enforce a minimum spacing (buff=0.3) and objects are expected
        to be small enough to remain within the safe area (0.5 units from each edge).
        """
        # Create the triangle using Polygon with the given vertices
        triangle = Polygon(*vertices, color=WHITE, stroke_width=2)
        
        # Error check: Validate triangle bounding box is within safe area margins
        if triangle.get_left()[0] < -6.5 or triangle.get_right()[0] > 6.5 or triangle.get_bottom()[1] < -3.5 or triangle.get_top()[1] > 3.5:
            triangle.add(Text("Safe area violation", font_size=16, color=RED).scale(0.5))
            # NOTE: Manual review required for safe area constraints.

        # Determine the marker based on marker_type
        marker = None
        vertex_point = triangle.get_vertices()[marker_vertex_index]
        if marker_type == "arc":
            # For an arc marker, choose a small arc.
            # For acute triangle, use a small sweep. For obtuse, use a larger sweep angle.
            # Set parameters: radius=0.2, arc_angle based on label.
            if "Obtuse" in label_text:
                arc_angle = 2 * DEGREES * 80  # ~160° sweep for visual effect (obtuse marker)
                marker = Arc(radius=0.3, start_angle=0, angle=arc_angle, color=TEAL_D, stroke_width=2)
            else:
                arc_angle = PI/4  # 45° arc for acute triangle
                marker = Arc(radius=0.2, start_angle=0, angle=arc_angle, color=TEAL_D, stroke_width=2)
            # Position the arc marker next to the vertex, with a buff of 0.3 units
            marker.next_to(vertex_point, RIGHT, buff=0.3)
        elif marker_type == "square":
            # Create a small square marker for right angle.
            marker = Square(side_length=0.2, color=TEAL_D, stroke_width=2)
            # Position it adjacent to the vertex. For the right angle vertex, we choose DOWN+RIGHT.
            marker.next_to(vertex_point, DOWN + RIGHT, buff=0.3)
        else:
            # Default to no marker if invalid type is passed.
            marker = VGroup()

        # Create the label Tex, font size 24 if short.
        label = Tex(label_text, font_size=24, color=BLUE_C)
        # Position label below the triangle with a minimum buff of 0.3 units.
        label.next_to(triangle, DOWN, buff=0.3)
        # Validate label does not cross safe area margin: check its bottom
        if label.get_bottom()[1] < -3.5:
            label.shift(UP * 0.3)
            # COMMENT: Adjusted label upward to avoid safe area margin violation.

        # Group triangle, marker, and label into one VGroup for reusability.
        group = VGroup(triangle, marker, label)
        return group

    def position_vgroup(self, vgroup, target_edge, buff=0.3):
        """
        Position a VGroup so that its specified edge aligns with the scene's safe area.
        target_edge: "left", "center", or "right"
        """
        # Get the group's current bounding box
        if target_edge == "left":
            # Shift so that the left edge is at x = -6.5 (safe left margin)
            current_left = vgroup.get_left()[0]
            vgroup.shift(LEFT * (current_left - (-6.5)))
        elif target_edge == "right":
            # Shift so that the right edge is at x = 6.5 (safe right margin)
            current_right = vgroup.get_right()[0]
            vgroup.shift(RIGHT * (6.5 - current_right))
        elif target_edge == "center":
            vgroup.move_to(ORIGIN)
        # Using next_to for inter-group spacing will be handled outside this function.
        return vgroup

class Scene3(VoiceoverScene, MovingCameraScene):
    # Scene3: Angle Variations.
    def construct(self):
        # Initialize speech service
        self.set_speech_service(KokoroService())

        # Instantiate helper class
        helper = Scene3_Helper(self)

        # --- Stage 1: Title and Layout Setup ---
        with self.voiceover(text="Now, in Scene 3, we explore Angle Variations by examining how triangles are classified by the measures of their interior angles. Notice the title at the top as it sets the stage."):
            # Create the title text and position it at the top-center with a safe margin of 0.5 units.
            title = Tex("Angle Variations", font_size=28, color=GOLD_D)
            title.to_edge(UP, buff=0.5)
            self.play(Write(title), run_time=1)
            self.wait(1)

        # --- Stage 2: Create and Position Triangle Groups ---
        with self.voiceover(text="In the left section, we have an Acute Triangle with all angles less than 90 degrees. A small arc marker highlights one of its acute angles."):
            # Create Acute Triangle VGroup (LeftGroup)
            # Define vertices that yield an acute triangle.
            acute_vertices = [np.array([-0.5, -0.5, 0]),
                              np.array([0.5, -0.5, 0]),
                              np.array([0, 0.5, 0])]
            acute_group = helper.create_triangle_group(acute_vertices, "Acute Triangle", marker_type="arc", marker_vertex_index=2)
            # Position the acute group; first center it, then adjust relative to left safe area.
            acute_group.move_to(ORIGIN)
            acute_group = helper.position_vgroup(acute_group, target_edge="left")
            self.play(Create(acute_group[0]), run_time=1)  # Create triangle
            self.play(FadeIn(acute_group[1]), Write(acute_group[2]), run_time=1)
            self.wait(0.5)

        with self.voiceover(text="Moving to the center, here is a Right Triangle. Notice the small square marker indicating its perfect 90-degree angle at one corner."):
            # Create Right Triangle VGroup (CenterGroup)
            # Define vertices with a clear right angle at the first vertex.
            right_vertices = [np.array([-0.5, -0.5, 0]),  # Right angle at this vertex
                              np.array([0.5, -0.5, 0]),
                              np.array([-0.5, 0.5, 0])]
            right_group = helper.create_triangle_group(right_vertices, "Right Triangle", marker_type="square", marker_vertex_index=0)
            # Center the right triangle group
            right_group.move_to(ORIGIN)
            right_group = helper.position_vgroup(right_group, target_edge="center")
            self.play(Create(right_group[0]), run_time=1)
            self.play(FadeIn(right_group[1]), Write(right_group[2]), run_time=1)
            self.wait(0.5)

        with self.voiceover(text="Finally, in the right section, we see an Obtuse Triangle with one angle larger than 90 degrees. An extended arc around that vertex visually demonstrates its obtuse nature."):
            # Create Obtuse Triangle VGroup (RightGroup)
            # Define vertices that yield an obtuse angle; choose vertex 0 as the obtuse angle.
            obtuse_vertices = [np.array([-0.4, -0.5, 0]),  # Intended obtuse angle here
                               np.array([0.4, -0.5, 0]),
                               np.array([-0.7, 0.7, 0])]
            obtuse_group = helper.create_triangle_group(obtuse_vertices, "Obtuse Triangle", marker_type="arc", marker_vertex_index=0)
            # For the obtuse marker, we want an extended arc, so adjust its parameters if needed.
            # (Already handled in create_triangle_group by checking "Obtuse" in label_text.)
            obtuse_group.move_to(ORIGIN)
            obtuse_group = helper.position_vgroup(obtuse_group, target_edge="right")
            self.play(Create(obtuse_group[0]), run_time=1)
            self.play(FadeIn(obtuse_group[1]), Write(obtuse_group[2]), run_time=1)
            self.wait(0.5)

        # --- Stage 3: Arrange Groups Horizontally with Minimum Spacing ---
        with self.voiceover(text="The three panels are arranged side-by-side with a minimum spacing of 0.3 units between them, all well within the safe area margins."):
            # Group all three VGroups
            all_groups = VGroup(acute_group, right_group, obtuse_group)
            # Arrange them horizontally using next_to with a buff of 0.3 units.
            # First, align the right_group (center) with the other two.
            right_group.move_to(ORIGIN)  # already centered
            acute_group.next_to(right_group, LEFT, buff=0.3)
            obtuse_group.next_to(right_group, RIGHT, buff=0.3)
            # After positioning, ensure that none of the groups exceed safe margins.
            # Manual check comment: Verify that the acute group's left edge is >= -6.5 and obtuse's right edge <= 6.5.
            self.play(
                AnimationGroup(
                    FadeIn(acute_group, run_time=0.5),
                    FadeIn(right_group, run_time=0.5),
                    FadeIn(obtuse_group, run_time=0.5),
                    lag_ratio=0.2
                )
            )
            self.wait(1)

        # --- Stage 4: Summary Overlay ---
        with self.voiceover(text="To summarize, triangle classifications depend on the nature of their interior angles: acute triangles have all angles below 90 degrees, right triangles contain one 90-degree angle, and obtuse triangles feature an angle greater than 90 degrees."):
            summary = Tex("Triangles classified by angle measures: Acute, Right, Obtuse", font_size=24, color=PURPLE_C)
            summary.to_edge(DOWN, buff=0.5)
            # Safety check: ensure summary text is within vertical safe area.
            if summary.get_bottom()[1] < -3.5:
                summary.shift(UP * 0.3)
            self.play(Write(summary), run_time=1)
            self.wait(1)
