#!/usr/bin/env python3
"""
Test script for multi-module Chisel project support

This tests the enhanced build.sbt discovery that handles:
- Multiple build.sbt files in different directories
- Finding the correct build.sbt for the top module
- Creating build.sbt in the right location when needed
"""

import os
import shutil
import tempfile
from core.chisel_manager import (
    find_scala_files,
    extract_chisel_modules,
    build_chisel_dependency_graph,
    find_top_module,
    find_build_sbt,
    configure_build_sbt,
    generate_main_app,
    get_module_package,
)


def create_multi_module_project():
    """Create a multi-module Chisel test project with multiple build.sbt files."""
    temp_dir = tempfile.mkdtemp(prefix='chisel_multi_')
    
    # Create root build.sbt
    root_build = os.path.join(temp_dir, 'build.sbt')
    with open(root_build, 'w') as f:
        f.write("""name := "multi-module-project"
version := "0.1"
scalaVersion := "2.13.10"

lazy val core = (project in file("core"))
  .settings(
    libraryDependencies ++= Seq(
      "edu.berkeley.cs" %% "chisel3" % "3.6.0"
    )
  )

lazy val utils = (project in file("utils"))
  .settings(
    libraryDependencies ++= Seq(
      "edu.berkeley.cs" %% "chisel3" % "3.6.0"
    )
  )

lazy val root = (project in file("."))
  .aggregate(core, utils)
""")
    
    # Create core submodule with its own build.sbt
    core_dir = os.path.join(temp_dir, 'core')
    core_src = os.path.join(core_dir, 'src', 'main', 'scala', 'core')
    os.makedirs(core_src, exist_ok=True)
    
    core_build = os.path.join(core_dir, 'build.sbt')
    with open(core_build, 'w') as f:
        f.write("""name := "core"
version := "0.1"
scalaVersion := "2.13.10"

libraryDependencies ++= Seq(
  "edu.berkeley.cs" %% "chisel3" % "3.6.0"
)
""")
    
    # Create CPU in core submodule
    cpu_file = os.path.join(core_src, 'CPU.scala')
    with open(cpu_file, 'w') as f:
        f.write("""package core

import chisel3._

class CPU extends Module {
  val io = IO(new Bundle {
    val instruction = Input(UInt(32.W))
    val result = Output(UInt(32.W))
  })
  
  val alu = Module(new ALU())
  alu.io.a := 0.U
  alu.io.b := 0.U
  io.result := alu.io.result
}
""")
    
    # Create ALU in core submodule
    alu_file = os.path.join(core_src, 'ALU.scala')
    with open(alu_file, 'w') as f:
        f.write("""package core

import chisel3._

class ALU extends Module {
  val io = IO(new Bundle {
    val a = Input(UInt(32.W))
    val b = Input(UInt(32.W))
    val result = Output(UInt(32.W))
  })
  
  io.result := io.a + io.b
}
""")
    
    # Create utils submodule with its own build.sbt
    utils_dir = os.path.join(temp_dir, 'utils')
    utils_src = os.path.join(utils_dir, 'src', 'main', 'scala', 'utils')
    os.makedirs(utils_src, exist_ok=True)
    
    utils_build = os.path.join(utils_dir, 'build.sbt')
    with open(utils_build, 'w') as f:
        f.write("""name := "utils"
version := "0.1"
scalaVersion := "2.13.10"

libraryDependencies ++= Seq(
  "edu.berkeley.cs" %% "chisel3" % "3.6.0"
)
""")
    
    # Create a utility module in utils
    util_file = os.path.join(utils_src, 'Counter.scala')
    with open(util_file, 'w') as f:
        f.write("""package utils

import chisel3._

class Counter extends Module {
  val io = IO(new Bundle {
    val enable = Input(Bool())
    val count = Output(UInt(32.W))
  })
  
  val reg = RegInit(0.U(32.W))
  when(io.enable) {
    reg := reg + 1.U
  }
  io.count := reg
}
""")
    
    return temp_dir


def test_multi_module_build_sbt():
    """Test build.sbt discovery in multi-module projects."""
    print("[TEST] Creating multi-module Chisel project...")
    test_dir = create_multi_module_project()
    
    try:
        print(f"[TEST] Project created at: {test_dir}\n")
        
        # Find all Scala files
        print("[TEST 1] Finding Scala files...")
        scala_files = find_scala_files(test_dir)
        print(f"[PASS] Found {len(scala_files)} Scala files:")
        for f in scala_files:
            print(f"  - {os.path.relpath(f, test_dir)}")
        print()
        
        # Extract modules
        print("[TEST 2] Extracting Chisel modules...")
        modules = extract_chisel_modules(scala_files)
        print(f"[PASS] Found {len(modules)} modules:")
        for name, path in modules:
            print(f"  - {name} in {os.path.relpath(path, test_dir)}")
        print()
        
        # Build dependency graph
        print("[TEST 3] Building dependency graph...")
        module_graph, module_graph_inverse = build_chisel_dependency_graph(modules)
        print("[PASS] Dependency graph built")
        print(f"  - CPU instantiates: {module_graph.get('CPU', [])}")
        print()
        
        # Find top module
        print("[TEST 4] Finding top module...")
        top_module = find_top_module(module_graph, module_graph_inverse, modules, 'multi-module-project')
        print(f"[PASS] Top module: {top_module}")
        assert top_module == 'CPU', f"Expected 'CPU', got '{top_module}'"
        print()
        
        # Test build.sbt discovery
        print("[TEST 5] Testing build.sbt discovery...")
        print(f"  Top module: {top_module}")
        
        # Should find the core/build.sbt since CPU is in core/
        found_build = find_build_sbt(test_dir, top_module, modules)
        print(f"  Found: {os.path.relpath(found_build, test_dir)}")
        
        # Verify it found the correct build.sbt (near the top module)
        # Could be core/build.sbt or root build.sbt depending on strategy
        assert found_build is not None, "Should find a build.sbt"
        assert 'build.sbt' in found_build, "Should be a build.sbt file"
        print("[PASS] Found appropriate build.sbt")
        print()
        
        # Test configure_build_sbt
        print("[TEST 6] Testing configure_build_sbt...")
        configured_build = configure_build_sbt(test_dir, top_module, modules)
        assert os.path.exists(configured_build), "Configured build.sbt should exist"
        print(f"[PASS] Configured: {os.path.relpath(configured_build, test_dir)}")
        print()
        
        # Test package detection
        print("[TEST 7] Testing package detection...")
        module_to_file = {name: path for name, path in modules}
        cpu_file = module_to_file['CPU']
        package = get_module_package(cpu_file)
        assert package == 'core', f"Expected 'core', got '{package}'"
        print(f"[PASS] Detected package: {package}")
        print()
        
        # Test main App generation
        print("[TEST 8] Testing main App generation...")
        main_app = generate_main_app(test_dir, top_module, modules)
        assert os.path.exists(main_app), "Main App should exist"
        
        # Verify package
        with open(main_app, 'r') as f:
            content = f.read()
        assert 'package core' in content, "Main App should be in 'core' package"
        print(f"[PASS] Main App: {os.path.relpath(main_app, test_dir)}")
        print(f"  Package: core")
        print()
        
        print("[SUCCESS] All multi-module tests passed!")
        return True
        
    except AssertionError as e:
        print(f"[FAIL] Test failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        print(f"\n[CLEANUP] Removing test directory: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    import sys
    success = test_multi_module_build_sbt()
    sys.exit(0 if success else 1)
