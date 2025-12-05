#!/usr/bin/env python3
"""
Test script for Chisel support

This script creates a minimal Chisel test project and verifies
that the Chisel manager can process it correctly.
"""

import os
import shutil
import tempfile
from core.chisel_manager import (
    find_scala_files,
    extract_chisel_modules,
    build_chisel_dependency_graph,
    find_top_module,
)


def create_test_chisel_project():
    """Create a minimal Chisel test project."""
    temp_dir = tempfile.mkdtemp(prefix='chisel_test_')
    
    # Create directory structure
    src_dir = os.path.join(temp_dir, 'src', 'main', 'scala')
    os.makedirs(src_dir, exist_ok=True)
    
    # Create a simple ALU module
    alu_file = os.path.join(src_dir, 'ALU.scala')
    alu_content = """package example

import chisel3._

class ALU extends Module {
  val io = IO(new Bundle {
    val a = Input(UInt(32.W))
    val b = Input(UInt(32.W))
    val op = Input(UInt(2.W))
    val result = Output(UInt(32.W))
  })
  
  io.result := MuxLookup(io.op, 0.U)(Seq(
    0.U -> (io.a + io.b),
    1.U -> (io.a - io.b),
    2.U -> (io.a & io.b),
    3.U -> (io.a | io.b)
  ))
}
"""
    
    with open(alu_file, 'w') as f:
        f.write(alu_content)
    
    # Create a register file module
    regfile_file = os.path.join(src_dir, 'RegisterFile.scala')
    regfile_content = """package example

import chisel3._
import chisel3.util._

class RegisterFile extends Module {
  val io = IO(new Bundle {
    val rs1_addr = Input(UInt(5.W))
    val rs2_addr = Input(UInt(5.W))
    val rd_addr = Input(UInt(5.W))
    val rd_data = Input(UInt(32.W))
    val write_enable = Input(Bool())
    val rs1_data = Output(UInt(32.W))
    val rs2_data = Output(UInt(32.W))
  })
  
  val regs = Reg(Vec(32, UInt(32.W)))
  
  io.rs1_data := Mux(io.rs1_addr === 0.U, 0.U, regs(io.rs1_addr))
  io.rs2_data := Mux(io.rs2_addr === 0.U, 0.U, regs(io.rs2_addr))
  
  when(io.write_enable && io.rd_addr =/= 0.U) {
    regs(io.rd_addr) := io.rd_data
  }
}
"""
    
    with open(regfile_file, 'w') as f:
        f.write(regfile_content)
    
    # Create a simple CPU top module that instantiates ALU and RegisterFile
    cpu_file = os.path.join(src_dir, 'SimpleCPU.scala')
    cpu_content = """package example

import chisel3._

class SimpleCPU extends Module {
  val io = IO(new Bundle {
    val instruction = Input(UInt(32.W))
    val result = Output(UInt(32.W))
  })
  
  // Instantiate ALU
  val alu = Module(new ALU())
  
  // Instantiate RegisterFile
  val regfile = Module(new RegisterFile())
  
  // Connect modules
  alu.io.a := regfile.io.rs1_data
  alu.io.b := regfile.io.rs2_data
  alu.io.op := io.instruction(1, 0)
  
  regfile.io.rs1_addr := io.instruction(19, 15)
  regfile.io.rs2_addr := io.instruction(24, 20)
  regfile.io.rd_addr := io.instruction(11, 7)
  regfile.io.rd_data := alu.io.result
  regfile.io.write_enable := true.B
  
  io.result := alu.io.result
}
"""
    
    with open(cpu_file, 'w') as f:
        f.write(cpu_content)
    
    # Create build.sbt
    build_sbt = os.path.join(temp_dir, 'build.sbt')
    build_content = """name := "chisel-test"

version := "0.1"

scalaVersion := "2.13.10"

libraryDependencies ++= Seq(
  "edu.berkeley.cs" %% "chisel3" % "3.6.0"
)
"""
    
    with open(build_sbt, 'w') as f:
        f.write(build_content)
    
    return temp_dir


def test_chisel_manager():
    """Test the Chisel manager functions."""
    print("[TEST] Creating test Chisel project...")
    test_dir = create_test_chisel_project()
    
    try:
        print(f"[TEST] Test project created at: {test_dir}\n")
        
        # Test 1: Find Scala files
        print("[TEST 1] Finding Scala files...")
        scala_files = find_scala_files(test_dir)
        assert len(scala_files) == 3, f"Expected 3 Scala files, found {len(scala_files)}"
        print(f"[PASS] Found {len(scala_files)} Scala files")
        for f in scala_files:
            print(f"  - {os.path.basename(f)}")
        print()
        
        # Test 2: Extract Chisel modules
        print("[TEST 2] Extracting Chisel modules...")
        modules = extract_chisel_modules(scala_files)
        assert len(modules) == 3, f"Expected 3 modules, found {len(modules)}"
        print(f"[PASS] Found {len(modules)} modules:")
        for name, path in modules:
            print(f"  - {name} in {os.path.basename(path)}")
        print()
        
        # Test 3: Build dependency graph
        print("[TEST 3] Building dependency graph...")
        module_graph, module_graph_inverse = build_chisel_dependency_graph(modules)
        
        # Verify SimpleCPU instantiates ALU and RegisterFile
        assert 'SimpleCPU' in module_graph, "SimpleCPU not in module_graph"
        assert 'ALU' in module_graph['SimpleCPU'], "SimpleCPU should instantiate ALU"
        assert 'RegisterFile' in module_graph['SimpleCPU'], "SimpleCPU should instantiate RegisterFile"
        print("[PASS] Dependency graph correct:")
        print("  - SimpleCPU instantiates: ALU, RegisterFile")
        
        # Verify ALU and RegisterFile are instantiated by SimpleCPU
        assert 'SimpleCPU' in module_graph_inverse['ALU'], "ALU should be instantiated by SimpleCPU"
        assert 'SimpleCPU' in module_graph_inverse['RegisterFile'], "RegisterFile should be instantiated by SimpleCPU"
        print("  - ALU instantiated by: SimpleCPU")
        print("  - RegisterFile instantiated by: SimpleCPU")
        print()
        
        # Test 4: Find top module
        print("[TEST 4] Finding top module...")
        top_module = find_top_module(module_graph, module_graph_inverse, modules, 'chisel-test')
        assert top_module == 'SimpleCPU', f"Expected top module 'SimpleCPU', got '{top_module}'"
        print(f"[PASS] Top module correctly identified: {top_module}")
        print()
        
        # Test 5: Test build.sbt discovery with multiple files
        print("[TEST 5] Testing build.sbt discovery...")
        from core.chisel_manager import find_build_sbt, configure_build_sbt
        
        # Create a secondary build.sbt in a subdirectory
        sub_dir = os.path.join(test_dir, 'subproject')
        os.makedirs(sub_dir, exist_ok=True)
        sub_build_sbt = os.path.join(sub_dir, 'build.sbt')
        with open(sub_build_sbt, 'w') as f:
            f.write('name := "subproject"\n')
        
        # Should find root build.sbt first
        found_build_sbt = find_build_sbt(test_dir, top_module, modules)
        expected_root = os.path.join(test_dir, 'build.sbt')
        assert found_build_sbt == expected_root, f"Expected {expected_root}, got {found_build_sbt}"
        print(f"[PASS] Correctly found root build.sbt")
        
        # Test configure_build_sbt with modules
        configured_build_sbt = configure_build_sbt(test_dir, top_module, modules)
        assert os.path.exists(configured_build_sbt), "build.sbt should exist"
        print(f"[PASS] build.sbt configured at: {os.path.relpath(configured_build_sbt, test_dir)}")
        print()
        
        # Test 6: Test main App generation with package detection
        print("[TEST 6] Testing main App generation...")
        from core.chisel_manager import generate_main_app, get_module_package
        
        # Get package from SimpleCPU
        module_to_file = {name: path for name, path in modules}
        cpu_file = module_to_file['SimpleCPU']
        package = get_module_package(cpu_file)
        assert package == 'example', f"Expected package 'example', got '{package}'"
        print(f"[PASS] Detected package: {package}")
        
        # Generate main App
        main_app = generate_main_app(test_dir, top_module, modules)
        assert os.path.exists(main_app), "Main App should be generated"
        
        # Verify it's in the correct package
        with open(main_app, 'r') as f:
            app_content = f.read()
        assert 'package example' in app_content, "Main App should be in 'example' package"
        assert f'new {top_module}()' in app_content, f"Main App should instantiate {top_module}"
        print(f"[PASS] Main App generated in correct package")
        print()
        
        print("[SUCCESS] All tests passed!")
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
    success = test_chisel_manager()
    sys.exit(0 if success else 1)
