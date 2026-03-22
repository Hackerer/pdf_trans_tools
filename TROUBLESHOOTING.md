# PDF翻译工具 - 故障排除指南

## 服务器启动

### 方法1: 使用启动脚本 (推荐)
```bash
cd /Users/max/Documents/pdf_trans_tools
python start_web.py
```

### 方法2: 手动启动
```bash
cd /Users/max/Documents/pdf_trans_tools
PYTHONPATH=src python -m pdf_trans_tools.web
```

### 方法3: 直接运行web.py
```bash
cd /Users/max/Documents/pdf_trans_tools/src/pdf_trans_tools
PYTHONPATH=../../../src python web.py
```

启动成功后，应该看到:
```
* Running on http://127.0.0.1:5000
* Debug mode: on
```

## 打开浏览器

在浏览器中打开: http://127.0.0.1:5000

**注意**: 如果修改了代码，需要重启服务器才能生效。

## 常见问题

### 1. "上传文件不成功"

**可能原因**:

1. **PDF文件问题** - 如果PDF是扫描件（图片），没有可提取的文本
   - 状态栏会显示: "提取失败: PDF marker not found"
   - 解决方案: 使用文字型PDF，不是扫描件

2. **浏览器缓存** - 旧的JavaScript代码还在缓存中
   - 解决方案: 按 Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows) 强制刷新

3. **服务器未正确启动** - 检查终端是否有错误信息
   - 解决方案: 重启服务器

4. **文件太大** - 超过50MB限制
   - 解决方案: 压缩PDF或分割成多个小文件

### 2. "翻译成功但下载不了"

可能原因:
- 输出目录不存在或没有写入权限
- 解决方案: 检查 `~/pdf_trans_tools_output/` 目录

### 3. 页面显示不正常

- 按 F12 打开开发者工具
- 检查 Console 标签页的错误信息
- 检查 Network 标签页的网络请求

## 调试步骤

### 步骤1: 检查服务器日志

启动服务器后，观察终端输出:

```
INFO:pdf_trans_tools.web:OUTPUT_DIR: /Users/max/pdf_trans_tools_output
INFO:pdf_trans_tools.web:Template folder: templates
INFO:pdf_trans_tools.web:Translator initialized successfully
```

### 步骤2: 检查网络请求

1. 按 F12 打开开发者工具
2. 选择 Network 标签
3. 上传文件
4. 检查是否有请求发出，以及响应是什么

### 步骤3: 检查控制台错误

1. 选择 Console 标签
2. 查找红色错误信息
3. 查找 console.log() 输出的调试信息

## 测试PDF文件

如果您没有测试用的PDF文件，可以用以下方法创建一个:

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

pdf = canvas.Canvas("test.pdf", pagesize=letter)
pdf.drawString(100, 750, "Hello, this is a test PDF.")
pdf.save()
```

或者在终端运行:
```bash
# 安装reportlab (如果还没安装)
pip install reportlab

# 创建测试PDF
python -c "
from reportlab.pdfgen import canvas
c = canvas.Canvas('/tmp/test.pdf')
c.drawString(100, 750, 'Test PDF for translation')
c.save()
"
```

然后用 `/tmp/test.pdf` 测试。

## 联系支持

如果以上步骤都无法解决问题:
1. 截屏错误信息
2. 打开浏览器开发者工具的 Console 标签，复制所有错误
3. 打开 Network 标签，右键点击失败的请求，选择 "Copy as cURL"
4. 将这些信息提供给我们
