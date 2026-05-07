# overview
这是一个论文自动化下载和管理的项目，同时支持win和mac。主要流程是，拿到doi列表后，从doi.org跳转到出版社网站，进行论文和si的下载，必要时进行登陆下载。doi列表有2个来源，一是通过pubmed关键词搜索，获取rss链接，再从rss链接生成csv文件，最后由task_manager.py生成任务。另一个来源是用户上传csv文件，最后由task_manager.py生成任务。任务名就是文件名，同一存放到tasks目录下。所有任务的状态统计，最后写入到statistic.csv。所有csv的增删改查操作由csv_manager.py实现。下载后的论文和si统一放到download目录下的子文件夹下，每个任务对应一个子文件夹，比如task_20206_0505_1321。每个任务文件夹下分别有paper,si,html3个文件夹，用来存放论文，si，网页源文件。GUI分为首页-任务列表页，系统日志，任务详情页，系统配置页，共4个页面。任务列表页通过读取statistic.csv文件进行展示，支持分页。系统日志通过读取logs目录进行展示。任务详情页通过读取tasks目录进行展示。系统配置通过读取config目录进行展示。

# 技术栈
该项目主要是用pyautogui实现网页自动化操作。GUI使用tkinter实现，使用pyinstall进行打包。

# 代码风格
不要下面这种冗余的代码，尽量简单直接
```python
def _read_page_load_sec() -> float:
    cfg = get_config()
    return max(0.0, cfg.get_float("download", "page_load_sec", default=DEFAULT_PAGE_LOAD_SEC))
```

# 重要提示
1. 每次改代码前，先和我确认实现方案，得到肯定答复后再开始改代码
2. 所有的实现必须兼容mac和win，不要使用任何osascript


# 日志格式
2026-04-29 11:02:52 [任务获取] 任务名-task01  DOI总数-88条
2026-04-29 11:02:53 [任务进度] 共88条，当前第1条: DOI -   10.3390/jfb14040183
2026-04-29 11:02:53 [地址解析] 打开网页成功
2026-04-29 11:02:54 [地址解析] 等待网页加载60秒
2026-04-29 11:03:52 [地址解析] 地址解析成功: www.xxx.com
2026-04-29 11:04:52 [源码获取] 正在获取网页源码
2026-04-29 11:05:52 [网站登陆] 正在执行网站登陆 - cell
2026-04-29 11:06:52 [论文下载] 正在执行论文下载 - 模板下载
2026-04-29 11:07:52 [论文下载] 论文下载成功 - task01/paper/paper_01_10.3390_jfb14040183.pdf
2026-04-29 11:08:52 [资料下载] 正在执行si下载 - 关键词md
2026-04-29 11:09:52 [资料下载] si下载成功 - task01/si/si_01_10.3390_jfb14040183.pdf
2026-04-29 11:10:52 [执行结果] 第1条执行结束：论文下载-成功， si下载-成功
2026-04-29 11:11:52 [执行间隔] ——————等待30秒，开始执行第二条——————
2026-04-29 11:12:52 [任务进度] 共88条，当前第2条: DOI -   10.3290/jfb14040183


# 项目主流程
1. 获取任务csv文件，读取里面的doi列表
2. 拿到doi，调用resolve_doi_url.py打开网站，进行解析，返回出版社url。如果url为None，则在csv写入failedReason网页无法打开，不在执行后面流程，开启下一个循环。
3. 拿到url以后，开始网页登陆流程，不管成功与否，都继续下一步。如果登陆成功，则重新打开网站。如果登陆失败，则直接进入下一步。
4. 调用utils.get_html_content获取网站源码。如果无法打开网站，同上处理
5. 开始下载流程
6. 检测下载结果
7. 将结果写入csv文件
8. 执行等待间隔，开启下一轮


# 下载目录
1. 开发态（源码运行）：<project_root>/download
2. 打包态（pyinstaller 打成exe或者dmg安装后
mac: ~/Library/Application Support/AutoPaper/download
win: %LOCALAPPDATA%\\AutoPaper\\download
3. download目录下按任务名划分，任务名下分别有html,paper,si3个文件夹


# rss生成任务流程
1. 打开pubmed官网
2. 输入关键词并搜索
3. 点击 create rss
4. 点击生成rss订阅链接
5. 打开订阅链接
6. 获取里面的doi
7. 生成rss任务，命名格式为rss-keyword-mmdd,比如rss-pcl-0507,重复时rss-pcl-0507-02。
