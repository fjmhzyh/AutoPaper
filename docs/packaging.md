# AutoPaper 打包说明（mac + win）

本项目使用 `PyInstaller` 构建应用，再分别生成：

- mac: `AutoPaper.app` + `AutoPaper-<version>-mac.dmg`
- win: `AutoPaper-<version>-win-setup.exe`（Inno Setup）

> 说明：当前为**无签名**方案。可稳定出包与安装，但无法从系统层面彻底消除 Gatekeeper/SmartScreen 提示。

## 1. 环境准备

### mac

```bash
python3 -m pip install pyinstaller
```

系统需有 `hdiutil`（macOS 自带）。

### windows

```powershell
pip install pyinstaller
```

并安装 Inno Setup 6（默认路径包含 `ISCC.exe`）。

## 2. 一键打包命令

### mac（在 mac 机器执行）

```bash
bash scripts/build_mac.sh
```

产物目录：

- `release/<version>/mac/AutoPaper-<version>-mac.dmg`

### windows（在 windows 机器执行）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_win.ps1
```

产物目录：

- `release/<version>/win/AutoPaper-<version>-win-setup.exe`

## 3. 无签名场景的可用性兜底

### mac 首次打开拦截

1. 先执行：

```bash
xattr -dr com.apple.quarantine /path/to/AutoPaper.app
```

或使用：

```bash
bash scripts/mac_first_launch_fix.sh /path/to/AutoPaper.app
```

2. 如果仍提示无法打开：
   - 打开“系统设置 -> 隐私与安全性”
   - 在底部选择“仍要打开”

### windows SmartScreen 提示

- 首次运行若出现“Windows 已保护你的电脑”，点击“更多信息” -> “仍要运行”。
- 无签名时这是系统默认行为，无法完全避免。

## 4. 构建脚本说明

- `build/autopaper.spec`: PyInstaller 规格，包含 `config/`、`photos/` 资源
- `scripts/make_release.py`: 统一版本读取与产物目录准备
- `scripts/build_mac.sh`: 构建 `.app` 和 `.dmg`
- `scripts/build_win.ps1`: 构建 `.exe` 和 Inno 安装包
- `packaging/windows/autopaper.iss`: Inno Setup 模板

### 打包硬校验

构建脚本会强校验以下内容，缺失即失败：

- `dist/AutoPaper/AutoPaperWorker`（win 为 `AutoPaperWorker.exe`）
- `dist/AutoPaper/config/`
- `dist/AutoPaper/photos/`

其中 `AutoPaperWorker` 用于后台执行任务与验证码进程，缺失会导致任务启动异常或出现重复 GUI 行为。

## 5. 常见问题

1. `pyinstaller not found`
   - 运行 `pip install pyinstaller`

2. `ISCC.exe not found`
   - 安装 Inno Setup 6，或在 `build_win.ps1` 传入 `-ISCC "<path-to-ISCC.exe>"`

3. 打包成功但运行找不到资源
   - 确认 `build/autopaper.spec` 中 `datas` 含 `config` 与 `photos`

4. 点击开始执行后行为异常
   - 先检查 `dist/AutoPaper/AutoPaperWorker` 是否存在
   - 若缺失，重新执行打包命令并查看构建脚本硬校验错误
