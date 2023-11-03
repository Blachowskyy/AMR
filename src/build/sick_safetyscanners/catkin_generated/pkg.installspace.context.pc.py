# generated from catkin/cmake/template/pkg.context.pc.in
CATKIN_PACKAGE_PREFIX = ""
PROJECT_PKG_CONFIG_INCLUDE_DIRS = "${prefix}/include;/usr/include".split(';') if "${prefix}/include;/usr/include" != "" else []
PROJECT_CATKIN_DEPENDS = "dynamic_reconfigure;message_runtime;roscpp;sensor_msgs;std_msgs".replace(';', ' ')
PKG_CONFIG_LIBRARIES_WITH_PREFIX = "-lsick_safetyscanners_core;/usr/lib/x86_64-linux-gnu/libboost_system.so.1.71.0;/usr/lib/x86_64-linux-gnu/libboost_thread.so.1.71.0".split(';') if "-lsick_safetyscanners_core;/usr/lib/x86_64-linux-gnu/libboost_system.so.1.71.0;/usr/lib/x86_64-linux-gnu/libboost_thread.so.1.71.0" != "" else []
PROJECT_NAME = "sick_safetyscanners"
PROJECT_SPACE_DIR = "/usr/local"
PROJECT_VERSION = "1.0.8"
