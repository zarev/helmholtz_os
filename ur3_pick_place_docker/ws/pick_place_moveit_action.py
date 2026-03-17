#!/usr/bin/env python3
"""
UR3 Pick-and-Place controller with fake AI agent popups.

Flow:
  open gripper → approach standoff → approach pre-grasp
    → [AGENT POPUP 1: battery detected? grasp or abort?]
  → descend → close gripper → lift → move to place standoff
    → [AGENT POPUP 2: scan analysis → choose next action]
  → return to init
"""
import os
from pathlib import Path
import time
import math
import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseStamped
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import RobotState
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration

try:
    import tkinter as tk
    from tkinter import ttk
    from PIL import Image, ImageTk          # optional — degrades gracefully
    _PIL_AVAILABLE = True
except ImportError:
    try:
        import tkinter as tk
        from tkinter import ttk
        _PIL_AVAILABLE = False
    except Exception:
        tk = None
        ttk = None
        _PIL_AVAILABLE = False


UR_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

EE_LINK = "tool0"

# ---------------------------------------------------------------------------
# Fake scan descriptions (used in Popup 2)
# ---------------------------------------------------------------------------
SCAN_DESCRIPTION = (
    "Real-time CT scan analysis complete.\n\n"
    "• Cell chemistry   : Li-NMC 622\n"
    "• Apparent capacity: 2 850 mAh  (nominal 3 000 mAh)\n"
    "• Anode expansion  : +4.1 %  (within limit)\n"
    "• Separator status : Intact — no deformation detected\n"
    "• Internal shorts  : None detected\n"
    "• Dendrite risk    : LOW\n"
    "• Gas void volume  : 0.12 cm³  (below threshold)\n"
    "• Recommendation   : Cell is safe to process.\n\n"
    "Please select the next action for this sample:"
)

SCAN_OPTIONS = [
    "✅  Archive & release sample",
    "🔬  Send to secondary analysis",
    "⚠️  Flag for manual inspection",
    "🗑️  Mark as defective & discard",
]

# ---------------------------------------------------------------------------
# Task options (used in Popup 2)
# ---------------------------------------------------------------------------
TASK_DESCRIPTION = (
    "Battery sample has been successfully grasped.\n\n"
    "Please select the next task for this sample:"
)

TASK_OPTIONS = [
    "🔬  Scan the sample",
    "📦  Put it away (storage)",
    "🚚  Remove from system"
]

# ---------------------------------------------------------------------------
# Helper: blocking Tk dialog running in its own thread
# ---------------------------------------------------------------------------

def _run_dialog_thread(target, *args, **kwargs):
    """Launch *target* in a daemon thread and wait until it finishes."""
    result_box = [None]
    exc_box = [None]

    def _wrapper():
        try:
            result_box[0] = target(*args, **kwargs)
        except Exception as exc:
            exc_box[0] = exc

    t = threading.Thread(target=_wrapper, daemon=True)
    t.start()
    t.join()          # block the calling (robot) thread until the user responds
    if exc_box[0]:
        raise exc_box[0]
    return result_box[0]


def _agent_popup_1_grasp():
    """
    Popup 1 – Battery sample detected.
    Returns True  → user confirmed grasp
            False → user chose to abort
    """
    if tk is None:
        print("[AGENT] tkinter unavailable – defaulting to GRASP")
        return True

    root = tk.Tk()
    root.title("🤖 AI Agent – Sample Detection")
    root.resizable(False, False)
    root.lift()
    root.attributes("-topmost", True)

    choice = [None]          # mutable container so inner functions can write

    # ── Styling ──────────────────────────────────────────────────────────────
    BG      = "#0f172a"
    PANEL   = "#1e293b"
    ACCENT  = "#38bdf8"
    GREEN   = "#4ade80"
    RED     = "#f87171"
    FG      = "#e2e8f0"
    FG_DIM  = "#94a3b8"
    FONT    = ("Segoe UI", 11)
    FONT_B  = ("Segoe UI", 11, "bold")
    FONT_H  = ("Segoe UI", 16, "bold")

    root.configure(bg=BG)

    def _close_with(value):
        choice[0] = value
        root.destroy()

    # ── Header ───────────────────────────────────────────────────────────────
    header = tk.Frame(root, bg=ACCENT, height=6)
    header.pack(fill="x")

    body = tk.Frame(root, bg=BG, padx=32, pady=24)
    body.pack(fill="both")

    # Agent badge
    badge_frame = tk.Frame(body, bg=PANEL, bd=0, padx=12, pady=8)
    badge_frame.pack(fill="x", pady=(0, 16))
    tk.Label(badge_frame, text="🤖  AI INSPECTION AGENT",
             fg=ACCENT, bg=PANEL, font=("Segoe UI", 10, "bold")).pack(anchor="w")
    tk.Label(badge_frame, text="HZB Battery Lab  —  Automated Sample Handler",
             fg=FG_DIM, bg=PANEL, font=("Segoe UI", 9)).pack(anchor="w")

    # Main message
    tk.Label(body, text="Battery Sample Detected", fg=FG, bg=BG,
             font=FONT_H).pack(anchor="w")
    tk.Label(body,
             text=(
                 "The scanning head has identified a battery cell at the pick\n"
                 "position. Visual confidence: 97.3 %\n\n"
                 "Should the robot arm grasp this sample?"
             ),
             fg=FG_DIM, bg=BG, font=FONT, justify="left").pack(anchor="w", pady=8)

    # Divider
    tk.Frame(body, bg="#334155", height=1).pack(fill="x", pady=8)

    # Buttons
    btn_frame = tk.Frame(body, bg=BG)
    btn_frame.pack(fill="x", pady=(4, 0))

    tk.Button(btn_frame, text="✅  Yes — Grasp Sample",
              font=FONT_B, bg=GREEN, fg="#0f172a", activebackground="#86efac",
              relief="flat", padx=20, pady=10, cursor="hand2",
              command=lambda: _close_with(True)
              ).pack(side="left", padx=(0, 8))

    tk.Button(btn_frame, text="❌  No — Abort & Return Home",
              font=FONT_B, bg=RED, fg="#0f172a", activebackground="#fca5a5",
              relief="flat", padx=20, pady=10, cursor="hand2",
              command=lambda: _close_with(False)
              ).pack(side="left")

    root.mainloop()
    return bool(choice[0])  # default False if window was closed via X


def _agent_popup_3_scan(image_path=None):
    """
    Popup 3 – Post-place scan analysis.
    Shows a fake scan image + CT description and lets the operator
    choose one of four next-step options.

    Returns the chosen option string (or None if closed without choice).
    """
    if tk is None:
        print("[AGENT] tkinter unavailable – defaulting to 'Archive & release'")
        return SCAN_OPTIONS[0]

    root = tk.Tk()
    root.title("🤖 AI Agent – Scan Analysis Report")
    root.resizable(True, True)
    root.lift()
    root.attributes("-topmost", True)

    choice = [None]

    BG      = "#0f172a"
    PANEL   = "#1e293b"
    ACCENT  = "#a78bfa"
    FG      = "#e2e8f0"
    FG_DIM  = "#94a3b8"
    FONT    = ("Segoe UI", 11)
    FONT_B  = ("Segoe UI", 11, "bold")
    FONT_H  = ("Segoe UI", 15, "bold")
    FONT_M  = ("Segoe UI", 10)

    OPTION_COLORS = ["#4ade80", "#60a5fa", "#fbbf24", "#f87171"]

    root.configure(bg=BG)

    def _close_with(value):
        choice[0] = value
        root.destroy()

    # ── Header bar ───────────────────────────────────────────────────────────
    tk.Frame(root, bg=ACCENT, height=6).pack(fill="x")

    outer = tk.Frame(root, bg=BG, padx=28, pady=20)
    outer.pack(fill="both", expand=True)

    # Agent badge
    badge = tk.Frame(outer, bg=PANEL, padx=12, pady=8)
    badge.pack(fill="x", pady=(0, 14))
    tk.Label(badge, text="🤖  AI INSPECTION AGENT  —  SCAN REPORT",
             fg=ACCENT, bg=PANEL, font=("Segoe UI", 10, "bold")).pack(anchor="w")
    tk.Label(badge, text="Tomographic scan completed. Awaiting operator decision.",
             fg=FG_DIM, bg=PANEL, font=("Segoe UI", 9)).pack(anchor="w")

    # ── Two-column layout: image left, text right ─────────────────────────
    cols = tk.Frame(outer, bg=BG)
    cols.pack(fill="both", expand=True, pady=(0, 14))

    # Image panel
    img_frame = tk.Frame(cols, bg=PANEL, bd=0)
    img_frame.pack(side="left", padx=(0, 16), fill="y")

    CANVAS_W, CANVAS_H = 320, 260
    canvas = tk.Canvas(img_frame, width=CANVAS_W, height=CANVAS_H,
                       bg="#111827", highlightthickness=0)
    canvas.pack(padx=8, pady=8)

    _photo_ref = [None]          # keep reference alive

    def _load_image():
        """Try to render the scan image (PNG/GIF) on the canvas."""
        path = image_path or _resolve_image()
        if not path:
            _draw_placeholder()
            return
        # PIL path
        if _PIL_AVAILABLE:
            try:
                img = Image.open(path).convert("RGB")
                img = img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                canvas.create_image(CANVAS_W // 2, CANVAS_H // 2, image=photo)
                _photo_ref[0] = photo
                return
            except Exception:
                pass
        # Tk native path (only GIF / PPM without PIL)
        try:
            photo = tk.PhotoImage(file=path)
            # Scale to fit
            pw, ph = photo.width(), photo.height()
            sx = max(1, pw // CANVAS_W)
            sy = max(1, ph // CANVAS_H)
            if sx > 1 or sy > 1:
                photo = photo.subsample(max(sx, sy))
            canvas.create_image(CANVAS_W // 2, CANVAS_H // 2, image=photo)
            _photo_ref[0] = photo
            return
        except Exception:
            pass
        _draw_placeholder()

    def _draw_placeholder():
        canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill="#1c2a3a")
        canvas.create_text(CANVAS_W // 2, CANVAS_H // 2 - 20,
                           text="🔬", font=("Segoe UI", 48), fill="#60a5fa")
        canvas.create_text(CANVAS_W // 2, CANVAS_H // 2 + 26,
                           text="CT Scan Image", font=("Segoe UI", 12),
                           fill="#94a3b8")

    def _resolve_image():
        candidates = [
            "ws/1-s2.0-S037877532201480X-gr1.jpg"
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    _load_image()

    tk.Label(img_frame, text="Tomographic slice — lateral view",
             fg=FG_DIM, bg=PANEL, font=("Segoe UI", 8)).pack(pady=(0, 6))

    # Text panel
    text_frame = tk.Frame(cols, bg=BG)
    text_frame.pack(side="left", fill="both", expand=True)

    tk.Label(text_frame, text="Scan Analysis Results",
             fg=FG, bg=BG, font=FONT_H, anchor="w").pack(fill="x")
    tk.Frame(text_frame, bg=ACCENT, height=2).pack(fill="x", pady=4)

    desc_box = tk.Text(text_frame, wrap="word", height=14,
                       bg=PANEL, fg=FG_DIM, font=FONT_M,
                       relief="flat", padx=10, pady=8,
                       state="normal", cursor="arrow")
    desc_box.pack(fill="both", expand=True)
    desc_box.insert("1.0", SCAN_DESCRIPTION)
    desc_box.configure(state="disabled")

    # ── Option buttons ────────────────────────────────────────────────────
    tk.Frame(outer, bg="#334155", height=1).pack(fill="x", pady=(0, 10))

    btn_frame = tk.Frame(outer, bg=BG)
    btn_frame.pack(fill="x")

    for i, opt in enumerate(SCAN_OPTIONS):
        color = OPTION_COLORS[i % len(OPTION_COLORS)]
        tk.Button(btn_frame, text=opt,
                  font=FONT_B, bg=color, fg="#0f172a",
                  activebackground=color,
                  relief="flat", padx=14, pady=9,
                  cursor="hand2",
                  command=lambda o=opt: _close_with(o)
                  ).pack(side="left", padx=(0, 6))

    root.mainloop()
    return choice[0]


def _agent_popup_2_task():
    """
    Popup 2 – Task selection after successful grasp.
    Lets the operator choose what to do with the grasped sample.

    Returns the chosen option string (or None if closed without choice).
    """
    if tk is None:
        print("[AGENT] tkinter unavailable – defaulting to 'Scan'")
        return TASK_OPTIONS[0]

    root = tk.Tk()
    root.title("🤖 AI Agent – Task Selection")
    root.resizable(False, False)
    root.lift()
    root.attributes("-topmost", True)

    choice = [None]

    BG      = "#0f172a"
    PANEL   = "#1e293b"
    ACCENT  = "#fbbf24"
    FG      = "#e2e8f0"
    FG_DIM  = "#94a3b8"
    FONT    = ("Segoe UI", 11)
    FONT_B  = ("Segoe UI", 11, "bold")
    FONT_H  = ("Segoe UI", 15, "bold")

    OPTION_COLORS = ["#60a5fa", "#4ade80", "#f87171", "#a78bfa"]

    root.configure(bg=BG)

    def _close_with(value):
        choice[0] = value
        root.destroy()

    # ── Header bar ───────────────────────────────────────────────────────────
    tk.Frame(root, bg=ACCENT, height=6).pack(fill="x")

    body = tk.Frame(root, bg=BG, padx=28, pady=24)
    body.pack(fill="both", expand=True)

    # Agent badge
    badge = tk.Frame(body, bg=PANEL, padx=12, pady=8)
    badge.pack(fill="x", pady=(0, 14))
    tk.Label(badge, text="🤖  AI INSPECTION AGENT  —  TASK SELECTION",
             fg=ACCENT, bg=PANEL, font=("Segoe UI", 10, "bold")).pack(anchor="w")
    tk.Label(badge, text="Sample successfully grasped. Awaiting operator decision.",
             fg=FG_DIM, bg=PANEL, font=("Segoe UI", 9)).pack(anchor="w")

    # Main message
    tk.Label(body, text="What is the task needed for this sample?",
             fg=FG, bg=BG, font=FONT_H).pack(anchor="w", pady=(0, 14))

    tk.Label(body,
             text=TASK_DESCRIPTION,
             fg=FG_DIM, bg=BG, font=("Segoe UI", 10), justify="left").pack(anchor="w", pady=8)

    # Divider
    tk.Frame(body, bg="#334155", height=1).pack(fill="x", pady=12)

    # Task option buttons
    btn_frame = tk.Frame(body, bg=BG)
    btn_frame.pack(fill="x", pady=(4, 0))

    for i, opt in enumerate(TASK_OPTIONS):
        color = OPTION_COLORS[i % len(OPTION_COLORS)]
        tk.Button(btn_frame, text=opt,
                  font=FONT_B, bg=color, fg="#0f172a",
                  activebackground=color,
                  relief="flat", padx=16, pady=11,
                  cursor="hand2",
                  command=lambda o=opt: _close_with(o)
                  ).pack(side="left", padx=(0, 6), fill="x", expand=True)

    root.mainloop()
    return choice[0]

class UR3_IK_PickPlace(Node):
    def __init__(self):
        super().__init__("ur3_ik_pick_place")

        self.arm_action_name = os.getenv(
            "ARM_ACTION_NAME",
            "/scaled_joint_trajectory_controller/follow_joint_trajectory",
        )
        self.ik_group_name = os.getenv("IK_GROUP_NAME", "ur_manipulator")
        self.require_gripper = os.getenv("REQUIRE_GRIPPER", "0") == "1"
        self.arm = ActionClient(self, FollowJointTrajectory, self.arm_action_name)

        self.gripper = ActionClient(self, GripperCommand,
                                    "/gripper_controller/gripper_cmd")
        self.gripper_available = False

        self.ik = self.create_client(GetPositionIK, "/compute_ik")
        self.last_joint_state = None
        self.last_orientation = None
        self.orientation_rpy_candidates = [
            (math.pi, 0.0, 0.0),
            (math.pi, 0.0, math.pi / 2.0),
            (math.pi, 0.0, -math.pi / 2.0),
            (0.0, 0.0, 0.0),
            (0.0, math.pi / 2.0, 0.0),
            (0.0, -math.pi / 2.0, 0.0),
        ]

        self.create_subscription(JointState, "/joint_states",
                                 self._joint_state_cb, 10)

        self.get_logger().info("Waiting for services...")
        if not self.arm.wait_for_server(timeout_sec=20.0):
            raise RuntimeError("No arm FollowJointTrajectory action server is available")

        self.gripper_available = self.gripper.wait_for_server(timeout_sec=20.0)
        if not self.gripper_available:
            if self.require_gripper:
                raise RuntimeError("Gripper action server /gripper_controller/gripper_cmd is unavailable")
            self.get_logger().warn("Gripper server unavailable; continuing in arm-only mode")

        if not self.ik.wait_for_service(timeout_sec=20.0):
            raise RuntimeError("IK service /compute_ik did not become available in time")

        # Ensure we have at least one joint-state sample before commanding motion.
        wait_deadline = time.time() + 45.0
        while self.last_joint_state is None and time.time() < wait_deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.last_joint_state is None:
            raise RuntimeError("No /joint_states data received")

        self.get_logger().info(f"All services ready (arm action: {self.arm_action_name})")

        self.pick_loop()

    # ── callbacks ────────────────────────────────────────────────────────────

    def _joint_state_cb(self, msg: JointState):
        self.last_joint_state = msg

    # ── IK ───────────────────────────────────────────────────────────────────

    def _rpy_to_quat_tuple(self, roll, pitch, yaw):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        return (
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy,
        )

    def _apply_quat(self, pose: PoseStamped, quat):
        pose.pose.orientation.x = quat[0]
        pose.pose.orientation.y = quat[1]
        pose.pose.orientation.z = quat[2]
        pose.pose.orientation.w = quat[3]

    def compute_ik(self, pose: PoseStamped):
        req = GetPositionIK.Request()
        req.ik_request.group_name = self.ik_group_name
        req.ik_request.ik_link_name = EE_LINK
        req.ik_request.pose_stamped = pose
        req.ik_request.timeout.sec = 4

        if self.last_joint_state:
            state = RobotState()
            state.joint_state = self.last_joint_state
            req.ik_request.robot_state = state

        orientation_candidates = []
        if self.last_orientation:
            orientation_candidates.append(self.last_orientation)
        for rpy in self.orientation_rpy_candidates:
            orientation_candidates.append(self._rpy_to_quat_tuple(*rpy))

        res = None
        for avoid_collisions in (True, False):
            req.ik_request.avoid_collisions = avoid_collisions
            for quat in orientation_candidates:
                self._apply_quat(pose, quat)
                req.ik_request.pose_stamped = pose

                future = self.ik.call_async(req)
                rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
                if not future.done():
                    self.get_logger().warn("IK request timed out; trying next orientation")
                    continue

                res = future.result()
                if res and res.error_code.val == res.error_code.SUCCESS:
                    self.last_orientation = quat
                    return [
                        res.solution.joint_state.position[
                            res.solution.joint_state.name.index(j)
                        ]
                        for j in UR_JOINTS
                    ]

        if res:
            self.get_logger().error(f"IK failed, error_code={res.error_code.val}")
        else:
            self.get_logger().error("IK failed, no response")
        return None

    # ── Motion helpers ───────────────────────────────────────────────────────

    def _arm_reached(self, target_positions, tolerance=0.08):
        if self.last_joint_state is None:
            return False
        js = self.last_joint_state
        try:
            current = [js.position[js.name.index(j)] for j in UR_JOINTS]
        except ValueError:
            return False
        return all(abs(c - t) <= tolerance for c, t in zip(current, target_positions))

    def _send_action_goal(self, client, goal, label, expected_positions=None):
        goal_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future, timeout_sec=12.0)
        goal_handle = goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f"{label} goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=20.0)
        if result_future.result() is None:
            if expected_positions is not None:
                deadline = time.time() + 25.0
                while time.time() < deadline:
                    rclpy.spin_once(self, timeout_sec=0.1)
                    if self._arm_reached(expected_positions):
                        self.get_logger().info(f"{label} reached target via joint-state check")
                        return True
            self.get_logger().error(f"{label} result not received")
            return False
        return True

    def move_joints(self, joints, t=4.0):
        goal = FollowJointTrajectory.Goal()
        p = JointTrajectoryPoint()
        p.positions = joints
        sec = int(t)
        nanosec = int((t - sec) * 1e9)
        p.time_from_start = Duration(sec=sec, nanosec=nanosec)
        goal.trajectory.joint_names = UR_JOINTS
        goal.trajectory.points = [p]
        return self._send_action_goal(self.arm, goal, "Arm", expected_positions=joints)

    def move_pose(self, pose: PoseStamped, t=4.0):
        joints = self.compute_ik(pose)
        if not joints:
            return False
        return self.move_joints(joints, t)

    def move_step(self, label, joints, t):
        self.get_logger().info(label)
        return self.move_joints(joints, t)

    def gripper_cmd(self, pos):
        if not self.gripper_available:
            if self.require_gripper:
                self.get_logger().error("Gripper command requested but gripper server is unavailable")
                return False
            return True
        g = GripperCommand.Goal()
        g.command.position = pos
        g.command.max_effort = 20.0
        return self._send_action_goal(self.gripper, g, "Gripper")

    @staticmethod
    def _pose_at(x, y, z):
        p = PoseStamped()
        p.header.frame_id = os.getenv("POSE_FRAME", "base_link")
        p.pose.position.x = x
        p.pose.position.y = y
        p.pose.position.z = z
        p.pose.orientation.w = 1.0
        return p

    # ── AGENT POPUP 1 ────────────────────────────────────────────────────────

    def _ask_agent_grasp(self):
        """
        Block the robot thread and show Popup 1 (battery detection).
        Returns True → grasp, False → abort.
        """
        self.get_logger().info("[AGENT] Showing battery-detection popup …")
        try:
            result = _run_dialog_thread(_agent_popup_1_grasp)
        except Exception as exc:
            self.get_logger().error(f"[AGENT] Popup error: {exc} — defaulting to GRASP")
            result = True
        action = "GRASP" if result else "ABORT"
        self.get_logger().info(f"[AGENT] Operator chose: {action}")
        return result

    # ── AGENT POPUP 2 ────────────────────────────────────────────────────────

    def _ask_agent_task(self):
        """
        Block the robot thread and show Popup 3 (task selection).
        Returns the chosen task option string.
        """
        self.get_logger().info("[AGENT] Showing task-selection popup …")
        try:
            result = _run_dialog_thread(_agent_popup_2_task)
        except Exception as exc:
            self.get_logger().error(f"[AGENT] Popup error: {exc} — defaulting to SCAN")
            result = TASK_OPTIONS[0]
        self.get_logger().info(f"[AGENT] Operator selected task: {result}")
        return result

    # ── AGENT POPUP 3 ────────────────────────────────────────────────────────

    def _ask_agent_scan(self):
        """
        Block the robot thread and show Popup 2 (scan analysis).
        Returns the chosen option string.
        """
        self.get_logger().info("[AGENT] Showing scan-analysis popup …")
        image_path = self._resolve_scan_image()
        try:
            result = _run_dialog_thread(_agent_popup_3_scan, image_path)
        except Exception as exc:
            self.get_logger().error(f"[AGENT] Popup error: {exc}")
            result = None
        self.get_logger().info(f"[AGENT] Operator selected: {result}")
        return result

    @staticmethod
    def _resolve_scan_image():
        for candidate in ["/ws/1-s2.0-S037877532201480X-gr1.jpg"]:
            if os.path.isfile(candidate):
                return candidate
        return None

    # ── Main pick-and-place loop ─────────────────────────────────────────────

    def pick_loop(self):
        # Scene geometry (metres)
        pick_x = float(os.getenv("PICK_X", "0.35"))
        pick_y = float(os.getenv("PICK_Y", "0.15"))
        pick_z = float(os.getenv("PICK_Z", "0.12"))
        place_x = float(os.getenv("PLACE_X", "0.35"))
        place_y = float(os.getenv("PLACE_Y", "-0.20"))
        place_z = float(os.getenv("PLACE_Z", "0.12"))

        pre_z      = 0.20
        grasp_z    = 0.02
        lift_z     = 0.18
        standoff_y = 0.12

        while rclpy.ok():
            # ── 1. Open gripper ──────────────────────────────────────────
            self.get_logger().info("Opening gripper")
            if not self.gripper_cmd(0.0):
                continue

            # ── 2. Approach standoff ─────────────────────────────────────
            self.get_logger().info("Approach standoff (near pick)")
            if not self.move_pose(
                self._pose_at(pick_x + 0.1, pick_y, pick_z + pre_z), 3.5
            ):
                continue

            # ── 3. Approach pre-grasp ────────────────────────────────────
            self.get_logger().info("Approach pre-grasp (closer)")
            if not self.move_pose(
                self._pose_at(pick_x, pick_y, pick_z + pre_z), 2.5
            ):
                continue

            # ═══════════════════════════════════════════════════════════════
            # AGENT POPUP 1 — Battery detected: grasp or abort?
            # Robot is stationary here while the popup blocks.
            # ═══════════════════════════════════════════════════════════════
            should_grasp = self._ask_agent_grasp()

            if not should_grasp:
                # Operator said NO → return home and end loop
                self.get_logger().info("[AGENT] Abort selected — returning to init")
                # Ensure gripper is closed, then move to the initial (safe) pose
                try:
                    self.gripper_cmd(0.0)
                except Exception:
                    pass
                self.get_logger().info("Moving to initial pose")
                self.move_pose(
                    self._pose_at(pick_x + 0.1, pick_y, pick_z + pre_z), 3.0
                )
                break   # ← exits the while loop entirely

            # ── 4. Descend and grasp ─────────────────────────────────────
            self.get_logger().info("Descend to grasp")
            if not self.move_pose(
                self._pose_at(pick_x, pick_y, pick_z + pre_z + grasp_z), 2.0
            ):
                continue

            self.get_logger().info("Close gripper")
            if not self.gripper_cmd(0.7):
                continue

            # ── 5. Lift ──────────────────────────────────────────────────
            self.get_logger().info("Lift object")
            if not self.move_pose(
                self._pose_at(pick_x, pick_y, pick_z + lift_z + 0.05), 2.5
            ):
                continue

            # ── 6. Move to place standoff ────────────────────────────────
            self.get_logger().info("Move to place standoff")
            if not self.move_pose(
                self._pose_at(place_x, place_y + standoff_y, place_z + pre_z), 3.0
            ):
                continue

            # ═══════════════════════════════════════════════════════════════
            # AGENT POPUP 2 — Task selection: operator picks next action.
            # Robot is stationary here while the popup blocks.
            # ═══════════════════════════════════════════════════════════════
            task_choice = self._ask_agent_task()
            self.get_logger().info(f"[AGENT] Task recorded: {task_choice or '(no choice)'}")

            # ═══════════════════════════════════════════════════════════════
            # AGENT POPUP 3 — Scan analysis: operator picks next action.
            # Show scan while the robot still holds the sample (before release).
            # Robot is stationary here while the popup blocks.
            # ═══════════════════════════════════════════════════════════════
            scan_choice = self._ask_agent_scan()
            self.get_logger().info(f"[AGENT] Action recorded: {scan_choice or '(no choice)'}")

            # In all cases: open gripper and return to a safe home pose.
            self.get_logger().info("Open gripper (release sample)")
            self.gripper_cmd(0.0)

            self.get_logger().info("Retreating to init pose")
            self.move_pose(
                self._pose_at(pick_x + 0.1, pick_y, pick_z + pre_z), 3.0
            )

            time.sleep(1.0)
            # Loop ends naturally after one full cycle —
            # remove the 'break' below if you want continuous cycling.
            break


def main():
    rclpy.init()
    node = UR3_IK_PickPlace()
    try:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
