from __future__ import annotations

import argparse
import math
import os
import random
import signal
import sys
import time
import traceback
from pathlib import Path
from typing import Any


IMAGE_NAMES = ["target.png", "target.jpeg", "target.jpg"]
CONFIDENCE = 0.8
CHECK_INTERVAL = 0.5
SEARCH_REGION = None
IS_MAC = sys.platform == "darwin"
RUNNING = True


def _log(message: str) -> None:
    print(f"[验证码] {message}", flush=True)


def _safe_reconfigure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(errors="replace")
        except Exception:
            pass


def _signal_handler(_signum: int, _frame: Any) -> None:
    global RUNNING
    RUNNING = False
    _log("收到停止信号，准备退出")


def _is_parent_alive(parent_pid: int) -> bool:
    if parent_pid <= 0:
        return True

    if os.name == "nt":
        import ctypes

        synchronize = 0x00100000
        wait_timeout = 0x00000102
        handle = ctypes.windll.kernel32.OpenProcess(synchronize, 0, int(parent_pid))
        if handle == 0:
            return False
        try:
            status = ctypes.windll.kernel32.WaitForSingleObject(handle, 0)
            return status == wait_timeout
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

    try:
        os.kill(parent_pid, 0)
    except OSError:
        return False
    return True


def _resolve_target_path(screen_width: int, screen_height: int) -> Path | None:
    project_root = Path(__file__).resolve().parents[1]
    photos_dir = project_root / "photos"
    if not photos_dir.exists():
        return None

    profile_prefix = "mac" if IS_MAC else "win"
    exact_profile = photos_dir / f"{profile_prefix}_{screen_width}_{screen_height}"
    profile_dirs: list[Path] = []
    if exact_profile.exists():
        profile_dirs.append(exact_profile)
    profile_dirs.extend(
        sorted(
            item for item in photos_dir.glob(f"{profile_prefix}_*") if item.is_dir() and item != exact_profile
        )
    )

    for profile_dir in profile_dirs:
        for image_name in IMAGE_NAMES:
            candidate = profile_dir / image_name
            if candidate.exists():
                _log(f"已匹配图片目录: {profile_dir.name}")
                return candidate
    return None


def get_bezier_point(t: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]) -> tuple[float, float]:
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = u * u * u
    ttt = tt * t
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return x, y


def human_move(pyautogui: Any, target_x: int, target_y: int, duration: float) -> None:
    start_x, start_y = pyautogui.position()
    dist = math.hypot(target_x - start_x, target_y - start_y)
    if dist < 50:
        pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeOutQuad)
        return

    offset = dist * random.uniform(0.2, 0.5)
    cp1_x = start_x + (target_x - start_x) * 0.3 + random.uniform(-offset, offset)
    cp1_y = start_y + (target_y - start_y) * 0.3 + random.uniform(-offset, offset)
    cp2_x = start_x + (target_x - start_x) * 0.7 + random.uniform(-offset, offset)
    cp2_y = start_y + (target_y - start_y) * 0.7 + random.uniform(-offset, offset)

    steps = int(duration * 60)
    if steps < 10:
        steps = 10

    old_pause = pyautogui.PAUSE
    pyautogui.PAUSE = 0
    start_time = time.time()
    for i in range(steps + 1):
        progress = i / steps
        eased_progress = 1 - (1 - progress) * (1 - progress)
        x, y = get_bezier_point(
            eased_progress,
            (start_x, start_y),
            (cp1_x, cp1_y),
            (cp2_x, cp2_y),
            (target_x, target_y),
        )
        pyautogui.moveTo(x, y)
        elapsed = time.time() - start_time
        expected = duration * progress
        if expected > elapsed:
            time.sleep(expected - elapsed)

    pyautogui.moveTo(target_x, target_y)
    pyautogui.PAUSE = old_pause


def simulate_human_click(pyautogui: Any, location: Any) -> bool:
    if not location:
        return False
    x, y = pyautogui.center(location)
    final_x = x + random.randint(-5, 5)
    final_y = y + random.randint(-5, 5)
    final_x = int(final_x / 2) if IS_MAC else final_x
    final_y = int(final_y / 2) if IS_MAC else final_y
    _log(f"检测到目标，坐标({final_x}, {final_y})，开始点击")
    move_time = random.uniform(0.5, 1.2)
    human_move(pyautogui, final_x, final_y, duration=move_time)
    time.sleep(random.uniform(0.1, 0.2))
    pyautogui.click()
    pyautogui.click()
    return True


def _is_image_not_found(exc: Exception) -> bool:
    return exc.__class__.__name__ == "ImageNotFoundException"


def run(parent_pid: int = 0) -> int:
    _safe_reconfigure_stdio()
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    try:
        import pyautogui  # type: ignore
    except ModuleNotFoundError:
        _log("错误: pyautogui 未安装")
        return 1

    pyautogui.FAILSAFE = False
    screen_width, screen_height = pyautogui.size()
    target_path = _resolve_target_path(screen_width, screen_height)

    _log(f"启动，系统={sys.platform} 分辨率={screen_width}x{screen_height} 父进程PID={parent_pid}")
    if SEARCH_REGION:
        _log(f"已启用区域搜索: {SEARCH_REGION}")
    if not target_path:
        _log("错误: 未找到 target 图片，请检查 photos/<系统_分辨率>/target.*")
        return 1
    _log(f"监听图片: {target_path}")

    while RUNNING:
        if not _is_parent_alive(parent_pid):
            _log(f"检测到父进程已退出(PID={parent_pid})，当前进程即将退出")
            break
        try:
            location = pyautogui.locateOnScreen(
                str(target_path),
                confidence=CONFIDENCE,
                grayscale=True,
                region=SEARCH_REGION,
            )
            if location:
                simulate_human_click(pyautogui, location)
                time.sleep(random.uniform(2.5, 4.0))
        except Exception as exc:
            if _is_image_not_found(exc):
                pass
            else:
                _log(f"异常: {exc}，3秒后重试")
                time.sleep(3)
        time.sleep(CHECK_INTERVAL)

    _log("已退出")
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Auto captcha click helper.")
    parser.add_argument("--parent-pid", type=int, default=0, help="task_executor pid")
    return parser


def main() -> None:
    try:
        args = _build_arg_parser().parse_args()
        raise SystemExit(run(parent_pid=max(0, int(args.parent_pid))))
    except SystemExit:
        raise
    except Exception:
        _log("异常退出:")
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
