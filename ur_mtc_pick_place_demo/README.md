
# MoveIt Task Constructor (MTC) Installation Guide – ROS 2 Jazzy

This guide walks you through installing the MoveIt Task Constructor (MTC) package and applying necessary fixes for a successful setup on ROS 2 Jazzy.

---

## 🔧 Prerequisites

Ensure you have:
- ROS 2 Jazzy installed and sourced
- A working colcon workspace (e.g. `~/ros2_ws`)

---

## 🚀 Installation Steps

### 1. Clone the MTC repository

```bash
cd ~/ros2_ws/src
git clone https://github.com/moveit/moveit_task_constructor.git -b jazzy
cd moveit_task_constructor
```

### 2. Checkout a stable commit

This ensures reproducibility and avoids potential issues from newer changes.

```bash
git reset --hard 9ced9fc10a15388224f0741e5a930a33f4ed6255
```

---

### 3. Install dependencies

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

---

### 4. Build the workspace

```bash
cd ~/ros2_ws
colcon build
source ~/.bashrc
```

> ⚠️ **Note:** You can ignore build warnings like this:
>
> ```
> --- stderr: rviz_marker_tools
> rviz_marker_tools: You did not request a specific build type: Choosing 'Release' for maximum performance
> ```

---

### 5. Rebuild (if errors show up)

If you see build errors, rebuild the workspace again:

```bash
cd ~/ros2_ws
colcon build
source ~/.bashrc
```

> ✅ Safe to ignore errors like:
>
> ```
> --- stderr: moveit_task_constructor_core
> lto-wrapper: warning: using serial compilation of 12 LTRANS jobs
> ```

---

## 🛠️ Fix Known Issues

Some runtime issues have been reported when executing plans from code. Follow these fixes to avoid path execution errors.

---

### 🔁 Fix 1: Planning Scene Diff

**File:**

```bash
cd ~/ros2_ws/src/moveit_task_constructor/core/src/
gedit storage.cpp
```

**Replace:**
```cpp
if (this->end()->scene()->getParent() == this->start()->scene())
    this->end()->scene()->getPlanningSceneDiffMsg(t.scene_diff);
else
    this->end()->scene()->getPlanningSceneMsg(t.scene_diff);
```

**With:**
```cpp
this->end()->scene()->getPlanningSceneDiffMsg(t.scene_diff);
```

---

### 📏 Fix 2: Cartesian Path Jump Threshold

**File:**

```bash
cd ~/ros2_ws/src/moveit_task_constructor/core/src/solvers/
gedit cartesian_path.cpp
```

**Replace:**
```cpp
moveit::core::JumpThreshold(props.get<double>("jump_threshold")), is_valid,
```

**With:**
```cpp
moveit::core::JumpThreshold::relative(props.get<double>("jump_threshold")), is_valid,
```

---

### 🔄 Rebuild

After applying fixes, rebuild the workspace:

```bash
cd ~/ros2_ws
colcon build
source ~/.bashrc
# OR
source ~/ros2_ws/install/setup.bash
```

---

## 🎉 Success!

You have now successfully installed and patched the **MoveIt Task Constructor** on ROS 2 Jazzy!  
You're ready to use MTC for pick-and-place and complex motion planning tasks.

---
  