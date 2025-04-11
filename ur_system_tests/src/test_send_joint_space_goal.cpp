#include <memory>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>

int main(int argc, char* argv[])
{
  rclcpp::init(argc, argv);
  auto const node = std::make_shared<rclcpp::Node>(
      "test_send_joint_space_goal_node", rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));

  auto const logger = rclcpp::get_logger("test_send_joint_space_goal_node");

  using moveit::planning_interface::MoveGroupInterface;
  MoveGroupInterface move_group_interface(node, "arm");  // <-- Make sure "arm" is correct!

  // Provide all 7 joint values for UR3 (you can adjust as needed)
  std::vector<double> joint_group_positions = {
    0.1, 0.3, 0.1, 0.4, 0.0, 0.0, 0.0
  };
  move_group_interface.setJointValueTarget(joint_group_positions);

  auto const [success, plan] = [&move_group_interface] {
    MoveGroupInterface::Plan msg;
    bool ok = static_cast<bool>(move_group_interface.plan(msg));
    return std::make_pair(ok, msg);
  }();

  if (success)
  {
    move_group_interface.execute(plan);
    RCLCPP_INFO(logger, "Motion executed successfully.");
  }
  else
  {
    RCLCPP_ERROR(logger, "Planning failed!");
  }

  rclcpp::shutdown();
  return 0;
}
