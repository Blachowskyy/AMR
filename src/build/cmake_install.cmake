# Install script for directory: /home/ros/catkin_ws/src

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Debug")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  
      if (NOT EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}")
        file(MAKE_DIRECTORY "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}")
      endif()
      if (NOT EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/.catkin")
        file(WRITE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/.catkin" "")
      endif()
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/_setup_util.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local" TYPE PROGRAM FILES "/home/ros/catkin_ws/src/build/catkin_generated/installspace/_setup_util.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/env.sh")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local" TYPE PROGRAM FILES "/home/ros/catkin_ws/src/build/catkin_generated/installspace/env.sh")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/setup.bash;/usr/local/local_setup.bash")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local" TYPE FILE FILES
    "/home/ros/catkin_ws/src/build/catkin_generated/installspace/setup.bash"
    "/home/ros/catkin_ws/src/build/catkin_generated/installspace/local_setup.bash"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/setup.sh;/usr/local/local_setup.sh")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local" TYPE FILE FILES
    "/home/ros/catkin_ws/src/build/catkin_generated/installspace/setup.sh"
    "/home/ros/catkin_ws/src/build/catkin_generated/installspace/local_setup.sh"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/setup.zsh;/usr/local/local_setup.zsh")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local" TYPE FILE FILES
    "/home/ros/catkin_ws/src/build/catkin_generated/installspace/setup.zsh"
    "/home/ros/catkin_ws/src/build/catkin_generated/installspace/local_setup.zsh"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/.rosinstall")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local" TYPE FILE FILES "/home/ros/catkin_ws/src/build/catkin_generated/installspace/.rosinstall")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/ros/catkin_ws/src/build/gtest/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geographic_info/geographic_info/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/geometry2/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_geotiff_launch/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_slam/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_slam_launch/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/my_mapping_launcher/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/navigation/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation_msgs/move_base_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_map_tools/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_nav_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_bullet/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_eigen/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/unique_identifier/unique_identifier/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/unique_identifier/uuid_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geographic_info/geographic_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/beginner_tutorials/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_geotiff/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_geotiff_plugins/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_marker_drawing/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/mobile_manipulator_body/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/map_server/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/server_for_wms/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_py/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_compressed_map_transport/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation_msgs/map_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/rplidar_ros/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/sick_safetyscanners/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_ros/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_imu_attitude_to_tf/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_imu_tools/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_map_server/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_trajectory_server/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/sick_lidar_localization/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_geometry_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/amcl/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/fake_localization/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/hector_slam/hector_mapping/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/ira_laser_tools/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/robot_localization/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_kdl/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/test_tf2/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_sensor_msgs/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geometry2/tf2_tools/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/tf_remapper_cpp/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/unique_identifier/unique_id/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/geographic_info/geodesy/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/rviz/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/model_wozek/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/urdf_tutorial/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/voxel_grid/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/costmap_2d/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/nav_core/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/base_local_planner/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/carrot_planner/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/clear_costmap_recovery/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/dwa_local_planner/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/move_slow_and_clear/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/navfn/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/global_planner/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/relaxed_astar/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/rotate_recovery/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/navigation/move_base/cmake_install.cmake")
  include("/home/ros/catkin_ws/src/build/robot_dhi_1/cmake_install.cmake")

endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/ros/catkin_ws/src/build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
