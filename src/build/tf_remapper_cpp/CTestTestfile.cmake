# CMake generated Testfile for 
# Source directory: /home/ros/catkin_ws/src/tf_remapper_cpp
# Build directory: /home/ros/catkin_ws/src/build/tf_remapper_cpp
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(_ctest_tf_remapper_cpp_gtest_test_tf_remapper "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/gtest-test_tf_remapper.xml" "--return-code" "/home/ros/catkin_ws/src/build/devel/lib/tf_remapper_cpp/test_tf_remapper --gtest_output=xml:/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/gtest-test_tf_remapper.xml")
set_tests_properties(_ctest_tf_remapper_cpp_gtest_test_tf_remapper PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/catkin/cmake/test/gtest.cmake;98;catkin_run_tests_target;/opt/ros/noetic/share/catkin/cmake/test/gtest.cmake;37;_catkin_add_google_test;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;30;catkin_add_gtest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;41;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_empty_mappings.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_empty_mappings.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_empty_mappings.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_empty_mappings.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_empty_mappings.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;42;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_works_if_no_mappings.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_works_if_no_mappings.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_works_if_no_mappings.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_works_if_no_mappings.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_works_if_no_mappings.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;43;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_static.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_static.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_static.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_static.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_static.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;44;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_static_with_param.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_static_with_param.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_static_with_param.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_static_with_param.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_static_with_param.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;45;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_forward.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_bidi_forward.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_bidi_forward.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_bidi_forward.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_forward.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;46;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_back.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_bidi_back.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_bidi_back.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_bidi_back.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_back.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;47;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_both.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_bidi_both.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_bidi_both.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_bidi_both.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_both.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;48;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")
add_test(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_both_static.launch "/home/ros/catkin_ws/src/build/catkin_generated/env_cached.sh" "/usr/bin/python3" "/opt/ros/noetic/share/catkin/cmake/test/run_tests.py" "/home/ros/catkin_ws/src/build/test_results/tf_remapper_cpp/rostest-test_test_tf_remapper_node_bidi_both_static.xml" "--return-code" "/usr/bin/python3 /opt/ros/noetic/share/rostest/cmake/../../../bin/rostest --pkgdir=/home/ros/catkin_ws/src/tf_remapper_cpp --package=tf_remapper_cpp --results-filename test_test_tf_remapper_node_bidi_both_static.xml --results-base-dir \"/home/ros/catkin_ws/src/build/test_results\" /home/ros/catkin_ws/src/tf_remapper_cpp/test/test_tf_remapper_node_bidi_both_static.launch ")
set_tests_properties(_ctest_tf_remapper_cpp_rostest_test_test_tf_remapper_node_bidi_both_static.launch PROPERTIES  _BACKTRACE_TRIPLES "/opt/ros/noetic/share/catkin/cmake/test/tests.cmake;160;add_test;/opt/ros/noetic/share/rostest/cmake/rostest-extras.cmake;52;catkin_run_tests_target;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;49;add_rostest;/home/ros/catkin_ws/src/tf_remapper_cpp/CMakeLists.txt;0;")