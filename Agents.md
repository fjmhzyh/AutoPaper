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
2. 不要使用任何osascript