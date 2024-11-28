## 缘起
+ 2024年11月的某一天，为知笔记服务端挂了，表现为在线搜索功能不可用、同步不可用。
+ 隔天，同步功能才恢复正常，但在线搜索却依然不可用，而为知的本地搜索实在太拉跨。而且出现每次修改笔记，保存很卡，真的很难忍。
+ 做为 all in wiz 的十几年重度老用户，觉得是时候搬家了。

## 简介

为知笔记 转 Obsidian（Markdown），支持：

+ markdown 笔记
  + 支持：附件
  + 图片：如果为 HTTP 链接会尝试下载图片至本地，下载失败（图片地址失效或无法访问）会继续使用 HTTP 地址
+ 普通笔记
  + 同 markdown 笔记，提取内容存为 markdown
  + **会丢失笔记的样式（加粗、字体、颜色、缩进 等）**
+ 任务清单（todolist2）
  + 不支持：附件、文档链接 等

> 建议 Obsidian 搭配 [obsidian-attachment-manager](https://github.com/chenfeicqq/obsidian-attachment-manager) 插件使用，获得更好的附件管理体验。

## 基本原理

1. 为知笔记 会在本地“笔记文件夹”下存放数据库文件 index.db
2. 为知笔记 ziw 本质是 zip 文件
3. 笔记的原始内容存放在 zip 文件中的 index.html
4. todolist2 格式的任务清单在 ziw 中有单独的文件 wiz_todolist.xml 记录了任务状态

转换的过程：
1. 读取 index.db 获取 笔记、附件 等信息；
2. 遍历笔记，解压 ziw 文件；
3. 根据笔记类型进行转换；

## 测试环境
+ Windows 11 23H2
+ python 3.12.2
+ 为知笔记 4.14.2

## 使用必读

1. 不支持加密笔记，需要先在 为知笔记 中进行解密；
2. 笔记的附件请提前下载至本地，未找到附件会继续执行，需要手工处理；
3. 转换失败会输出日志，继续转换后续的笔记；
4. 转换后的笔记，保存在`项目根目录\output\notes`目录，可在`Config.py`中调整
5. 支持断点续转，转换过程中会记录转换成功的笔记，重复执行会跳过已转换的笔记

## 运行前初始化
```bash
# 创建虚拟环境
python -m venv .venv
# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt -i https://mirrors.bfsu.edu.cn/pypi/web/simple/
```

## 运行
```bash
# 激活虚拟环境
.venv\Scripts\activate

# src 目录加到 sys.path 中，确保src目录下的包都可以正确被识别
set "PYTHONPATH=%CD%\src"

# 运行入口脚本
python src\main.py
```

## 参阅
+ [Beautiful Soup 文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh)
