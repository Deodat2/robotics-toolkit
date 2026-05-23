#!/bin/bash
# ============================================================
# FILE        : launch_amr.sh
# PROJECT     : amr_ros2
# DESCRIPTION : One-command launcher for the complete AMR system.
#
# USAGE:
#   ./scripts/launch_amr.sh              # full system
#   ./scripts/launch_amr.sh --no-vision  # without vision AI
#   ./scripts/launch_amr.sh --no-fleet   # without fleet
#   ./scripts/launch_amr.sh --slam-only  # robot + SLAM only
# ============================================================

set -e  # exit on any error

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Default options ---
VISION="true"
FLEET="true"
SLAM="true"
NAV="true"

# --- Parse arguments ---
for arg in "$@"; do
    case $arg in
        --no-vision)  VISION="false" ;;
        --no-fleet)   FLEET="false"  ;;
        --no-nav)     NAV="false"    ;;
        --slam-only)
        VISION="false"
        FLEET="false"
        NAV="false"
        ;;
        --help)
        echo "Usage: $0 [--no-vision] [--no-fleet] [--no-nav] [--slam-only]"
        exit 0
        ;;
    esac
done

# --- Paths ---
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLKIT_DIR="$(cd "$WORKSPACE_DIR/../.." && pwd)"
VENV_DIR="$TOOLKIT_DIR/venv_vision"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  AMR ROS 2 Toolkit — Launch Script${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "Workspace : $WORKSPACE_DIR"
echo -e "Vision    : $VISION"
echo -e "Fleet     : $FLEET"
echo -e "SLAM      : $SLAM"
echo -e "Nav2      : $NAV"
echo ""

# --- Source ROS 2 ---
echo -e "${YELLOW}[1/3] Sourcing ROS 2 Humble...${NC}"
source /opt/ros/humble/setup.bash

# --- Source venv (for YOLO + pyzbar) ---
if [ "$VISION" = "true" ]; then
    echo -e "${YELLOW}[2/3] Activating vision venv...${NC}"
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${RED}WARNING: venv_vision not found at $VENV_DIR${NC}"
        echo "Run: python3 -m venv $VENV_DIR --system-site-packages"
        echo "     source $VENV_DIR/bin/activate"
        echo "     pip install -r $WORKSPACE_DIR/requirements_vision.txt"
    fi
fi

# --- Source workspace ---
echo -e "${YELLOW}[3/3] Sourcing AMR workspace...${NC}"
cd "$WORKSPACE_DIR"

# Build first if install/ doesn't exist
if [ ! -f "$WORKSPACE_DIR/install/setup.bash" ]; then
    echo -e "${YELLOW}First run detected — building workspace...${NC}"
    colcon build --symlink-install
fi

source "$WORKSPACE_DIR/install/setup.bash"

# --- Launch ---
echo ""
echo -e "${GREEN}Launching AMR system...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all nodes${NC}"
echo ""

ros2 launch amr_ros2_bringup amr_full.launch.py \
    vision:=$VISION \
    fleet:=$FLEET \
    slam:=$SLAM \
    nav:=$NAV