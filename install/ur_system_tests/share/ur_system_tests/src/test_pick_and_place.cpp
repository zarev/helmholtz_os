#include <chrono>
#include <memory>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "control_msgs/action/follow_joint_trajectory.hpp"
#include "control_msgs/action/gripper_command.hpp"
#include "trajectory_msgs/msg/joint_trajectory_point.hpp"
#include "geometry_msgs/msg/pose.hpp"

#include "moveit/move_group_interface/move_group_interface.h"
#include "moveit/planning_scene_interface/planning_scene_interface.h"

using namespace std::chrono_literals;
using FollowJointTrajectory = control_msgs::action::FollowJointTrajectory;
using GripperCommand = control_msgs::action::GripperCommand;

class IKPickPlaceNode : public rclcpp::Node
{
public:
  IKPickPlaceNode() : Node("ik_pick_place_node")
  {
    arm_client_ = rclcpp_action::create_client<FollowJointTrajectory>(
      this, "/arm_controller/follow_joint_trajectory");
    gripper_client_ = rclcpp_action::create_client<GripperCommand>(
      this, "/gripper_controller/gripper_cmd");

    RCLCPP_INFO(this->get_logger(), "Waiting for action servers...");
    arm_client_->wait_for_action_server(10s);
    gripper_client_->wait_for_action_server(10s);
    RCLCPP_INFO(this->get_logger(), "Connected to action servers.");

    // ✨ Replace "ur3_arm" with your actual planning group name
    move_group_ = std::make_shared<moveit::planning_interface::MoveGroupInterface>(
      shared_from_this(), "arm");

    joint_names_ = move_group_->getJointNames();

    timer_ = this->create_wall_timer(500ms, std::bind(&IKPickPlaceNode::controlLoopCallback, this));
  }

private:
  geometry_msgs::msg::Pose createPose(double x, double y, double z)
  {
    geometry_msgs::msg::Pose pose;
    pose.position.x = x;
    pose.position.y = y;
    pose.position.z = z;
    pose.orientation.x = 0.0;
    pose.orientation.y = 0.0;
    pose.orientation.z = 0.0;
    pose.orientation.w = 1.0;
    return pose;
  }

  bool computeIK(const geometry_msgs::msg::Pose& target_pose, std::vector<double>& joint_positions)
  {
    move_group_->setPoseTarget(target_pose);
    moveit::planning_interface::MoveGroupInterface::Plan plan;

    bool success = (move_group_->plan(plan) == moveit::core::MoveItErrorCode::SUCCESS);
    if (success)
    {
      joint_positions = plan.trajectory.joint_trajectory.points.back().positions;
    }

    return success;
  }

  void sendArmCommand(const std::vector<double>& positions)
  {
    auto goal_msg = FollowJointTrajectory::Goal();
    goal_msg.trajectory.joint_names = joint_names_;

    trajectory_msgs::msg::JointTrajectoryPoint point;
    point.positions = positions;
    point.time_from_start = rclcpp::Duration::from_seconds(2.0);

    goal_msg.trajectory.points.push_back(point);

    auto options = rclcpp_action::Client<FollowJointTrajectory>::SendGoalOptions();
    arm_client_->async_send_goal(goal_msg, options);
  }

  void sendGripperCommand(double position)
  {
    auto goal_msg = GripperCommand::Goal();
    goal_msg.command.position = position;
    goal_msg.command.max_effort = 5.0;

    auto options = rclcpp_action::Client<GripperCommand>::SendGoalOptions();
    gripper_client_->async_send_goal(goal_msg, options);
  }

  void controlLoopCallback()
  {
    static int step = 0;
    std::vector<double> joints;

    switch (step)
    {
      case 0:
      {
        geometry_msgs::msg::Pose approach_pose = createPose(0.22, 0.12, 0.375);
        if (computeIK(approach_pose, joints))
        {
          RCLCPP_INFO(this->get_logger(), "Moving to approach pose...");
          sendArmCommand(joints);
          step++;
        }
        break;
      }

      case 1:
      {
        geometry_msgs::msg::Pose grasp_pose = createPose(0.22, 0.12, 0.175);
        if (computeIK(grasp_pose, joints))
        {
          RCLCPP_INFO(this->get_logger(), "Moving to grasp pose...");
          sendArmCommand(joints);
          step++;
        }
        break;
      }

      case 2:
        RCLCPP_INFO(this->get_logger(), "Closing gripper...");
        sendGripperCommand(-0.7);
        step++;
        break;

      case 3:
      {
        geometry_msgs::msg::Pose retreat_pose = createPose(0.22, 0.12, 0.375);
        if (computeIK(retreat_pose, joints))
        {
          RCLCPP_INFO(this->get_logger(), "Retreating...");
          sendArmCommand(joints);
          step++;
        }
        break;
      }

      case 4:
      {
        std::vector<double> home = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
        RCLCPP_INFO(this->get_logger(), "Returning to home...");
        sendArmCommand(home);
        step++;
        break;
      }

      case 5:
        RCLCPP_INFO(this->get_logger(), "Opening gripper...");
        sendGripperCommand(0.0);
        step++;
        break;

      case 6:
        RCLCPP_INFO(this->get_logger(), "Pick-and-place complete.");
        timer_->cancel();
        break;
    }
  }

  rclcpp_action::Client<FollowJointTrajectory>::SharedPtr arm_client_;
  rclcpp_action::Client<GripperCommand>::SharedPtr gripper_client_;
  std::shared_ptr<moveit::planning_interface::MoveGroupInterface> move_group_;
  std::vector<std::string> joint_names_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::executors::MultiThreadedExecutor executor;
  auto node = std::make_shared<IKPickPlaceNode>();
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
  return 0;
}
