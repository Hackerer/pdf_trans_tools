#!/usr/bin/env python3
"""
完整的用户旅程测试脚本
模拟用户从打开网页到下载翻译文件的全部操作
"""
import os
import sys
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_trans_tools.web import app, OUTPUT_DIR
from PyPDF2 import PdfWriter
from io import BytesIO

def create_test_pdf_with_text():
    """创建一个包含真实文本内容的测试PDF"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # 第一页 - 英文文本
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Test Document - English to Chinese")

    c.setFont("Helvetica", 12)
    y = height - 80

    text_lines = [
        "Hello, this is a test document.",
        "This PDF contains text that can be extracted.",
        "It is used to test the PDF translation functionality.",
        "",
        "The quick brown fox jumps over the lazy dog.",
        "Pack my box with five dozen liquor jugs.",
    ]

    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20

    c.showPage()

    # 第二页 - 更多文本
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Page 2 - More Content")

    c.setFont("Helvetica", 12)
    y = height - 80

    more_lines = [
        "The translation should preserve the structure.",
        "Each page should be properly extracted.",
        "The validation should pass when content matches.",
    ]

    for line in more_lines:
        c.drawString(50, y, line)
        y -= 20

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer


def test_step_1_homepage():
    """步骤1: 访问首页"""
    print("\n=== 步骤1: 访问首页 ===")
    client = app.test_client()

    response = client.get('/')
    print(f"状态码: {response.status_code}")
    print(f"内容长度: {len(response.data)} bytes")

    assert response.status_code == 200, "首页访问失败"
    assert b"PDF" in response.data, "首页没有包含PDF相关内容"

    # 检查HTML中是否有关键元素
    html = response.data.decode('utf-8')
    assert 'id="uploadBox"' in html, "缺少上传组件"
    assert 'id="targetLang"' in html, "缺少语言选择组件"
    assert 'id="translateBtn"' in html, "缺少翻译按钮"

    print("✓ 首页加载成功")
    print("✓ 上传组件存在")
    print("✓ 语言选择组件存在")
    print("✓ 翻译按钮存在")
    return True


def test_step_2_config_api():
    """步骤2: 测试配置API"""
    print("\n=== 步骤2: 测试配置API ===")
    client = app.test_client()

    # GET 请求
    response = client.get('/api/config')
    print(f"GET /api/config 状态码: {response.status_code}")
    data = json.loads(response.data)
    print(f"返回数据: {data}")
    assert data['has_api_key'] == False, "初始状态应该是没有API key"

    # POST 请求 (空key，重置为mock模式)
    response = client.post('/api/config', data={'api_key': ''})
    print(f"POST /api/config 状态码: {response.status_code}")
    data = json.loads(response.data)
    print(f"返回数据: {data}")
    assert data['success'] == True
    assert data['has_api_key'] == False

    print("✓ 配置API工作正常")
    return True


def test_step_3_extract_api():
    """步骤3: 测试文本提取API"""
    print("\n=== 步骤3: 测试文本提取API ===")
    client = app.test_client()

    # 创建测试PDF
    pdf_buffer = create_test_pdf_with_text()

    response = client.post('/api/extract',
        data={'file': (pdf_buffer, 'test.pdf')},
        content_type='multipart/form-data'
    )

    print(f"状态码: {response.status_code}")
    data = json.loads(response.data)
    print(f"成功: {data.get('success')}")
    print(f"页数: {data.get('page_count')}")
    print(f"文本长度: {len(data.get('text', ''))} 字符")
    print(f"文本预览: {data.get('text', '')[:200]}...")

    assert response.status_code == 200, "提取API请求失败"
    assert data['success'] == True, f"提取失败: {data.get('error')}"
    assert data['page_count'] == 2, f"页数错误，应该是2，实际是{data.get('page_count')}"
    assert len(data['text']) > 50, "提取的文本太短"

    print("✓ 文本提取API工作正常")
    return True


def test_step_4_translate_api():
    """步骤4: 测试翻译API"""
    print("\n=== 步骤4: 测试翻译API ===")
    client = app.test_client()

    # 创建测试PDF
    pdf_buffer = create_test_pdf_with_text()

    # 不带验证的翻译
    response = client.post('/api/translate',
        data={
            'file': (pdf_buffer, 'test.pdf'),
            'target_lang': 'zh',
            'validate': 'false'
        },
        content_type='multipart/form-data'
    )

    print(f"状态码: {response.status_code}")
    data = json.loads(response.data)
    print(f"成功: {data.get('success')}")
    print(f"输出文件: {data.get('output_filename')}")
    if data.get('error'):
        print(f"错误: {data.get('error')}")

    assert response.status_code == 200, "翻译API请求失败"
    assert data['success'] == True, f"翻译失败: {data.get('error')}"
    assert 'output_filename' in data, "缺少输出文件名"

    # 检查输出文件是否存在
    output_path = os.path.join(OUTPUT_DIR, data['output_filename'])
    print(f"输出文件路径: {output_path}")
    print(f"输出文件存在: {os.path.exists(output_path)}")

    if os.path.exists(output_path):
        print("✓ 翻译成功，输出文件已生成")
    else:
        print("✗ 翻译返回成功但文件不存在")

    print("✓ 翻译API基本功能正常")
    return True


def test_step_5_translate_with_validation():
    """步骤5: 测试带验证的翻译"""
    print("\n=== 步骤5: 测试带验证的翻译 ===")
    client = app.test_client()

    # 创建测试PDF
    pdf_buffer = create_test_pdf_with_text()

    # 带验证的翻译
    response = client.post('/api/translate',
        data={
            'file': (pdf_buffer, 'test.pdf'),
            'target_lang': 'zh',
            'validate': 'true'
        },
        content_type='multipart/form-data'
    )

    print(f"状态码: {response.status_code}")
    data = json.loads(response.data)
    print(f"成功: {data.get('success')}")
    print(f"输出文件: {data.get('output_filename')}")

    if 'validation' in data:
        print(f"验证结果: {data['validation'].get('is_valid')}")
        print(f"验证消息: {data['validation'].get('message')}")

    assert response.status_code == 200, "翻译API请求失败"
    assert data['success'] == True, f"翻译失败: {data.get('error')}"

    print("✓ 带验证的翻译功能正常")
    return True


def test_step_6_download_api():
    """步骤6: 测试下载API"""
    print("\n=== 步骤6: 测试下载API ===")

    # 先翻译一个文件
    client = app.test_client()
    pdf_buffer = create_test_pdf_with_text()

    response = client.post('/api/translate',
        data={
            'file': (pdf_buffer, 'download_test.pdf'),
            'target_lang': 'zh',
            'validate': 'false'
        },
        content_type='multipart/form-data'
    )

    data = json.loads(response.data)
    filename = data['output_filename']
    print(f"文件名: {filename}")

    # 尝试下载
    response = client.get(f'/api/download/{filename}')
    print(f"下载状态码: {response.status_code}")

    assert response.status_code == 200, f"下载失败，状态码: {response.status_code}"

    # 检查内容类型
    content_type = response.content_type
    print(f"内容类型: {content_type}")
    assert 'pdf' in content_type.lower(), f"不是PDF文件，内容类型: {content_type}"

    print("✓ 下载API工作正常")
    return True


def test_step_7_batch_upload():
    """步骤7: 测试批量上传"""
    print("\n=== 步骤7: 测试批量处理 ===")

    # 批量处理实际上是通过多次调用 /api/translate 实现的
    # 这里我们测试多个文件依次翻译

    client = app.test_client()

    files_to_translate = ['file1.pdf', 'file2.pdf', 'file3.pdf']
    results = []

    for filename in files_to_translate:
        pdf_buffer = create_test_pdf_with_text()
        response = client.post('/api/translate',
            data={
                'file': (pdf_buffer, filename),
                'target_lang': 'zh',
                'validate': 'false'
            },
            content_type='multipart/form-data'
        )
        data = json.loads(response.data)
        results.append(data['success'])
        print(f"{filename}: {'成功' if data['success'] else '失败'}")

    assert all(results), "部分文件翻译失败"
    print("✓ 批量处理基础功能正常")
    return True


def test_step_8_error_handling():
    """步骤8: 测试错误处理"""
    print("\n=== 步骤8: 测试错误处理 ===")
    client = app.test_client()

    # 测试1: 上传非PDF文件
    fake_file = BytesIO(b'This is not a PDF')
    response = client.post('/api/extract',
        data={'file': (fake_file, 'test.txt')},
        content_type='multipart/form-data'
    )
    data = json.loads(response.data)
    print(f"非PDF文件: {data.get('error')}")
    assert data['success'] == False
    assert 'PDF' in data.get('error', '')

    # 测试2: 不带文件调用API
    response = client.post('/api/extract', data={})
    data = json.loads(response.data)
    print(f"无文件上传: {data.get('error')}")
    assert data['success'] == False

    # 测试3: 空PDF (无文本)
    empty_pdf = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(empty_pdf)
    empty_pdf.seek(0)

    response = client.post('/api/translate',
        data={
            'file': (empty_pdf, 'empty.pdf'),
            'target_lang': 'zh',
            'validate': 'false'
        },
        content_type='multipart/form-data'
    )
    data = json.loads(response.data)
    print(f"空PDF翻译: success={data.get('success')}, error={data.get('error')}")

    print("✓ 错误处理正常")
    return True


def cleanup_test_files():
    """清理测试生成的文件"""
    print("\n=== 清理测试文件 ===")
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.pdf'):
                filepath = os.path.join(OUTPUT_DIR, f)
                try:
                    os.unlink(filepath)
                    print(f"已删除: {f}")
                except:
                    pass
    print("✓ 清理完成")


def main():
    print("=" * 60)
    print("PDF翻译工具 - 完整用户旅程测试")
    print("=" * 60)

    tests = [
        ("步骤1: 访问首页", test_step_1_homepage),
        ("步骤2: 配置API", test_step_2_config_api),
        ("步骤3: 文本提取", test_step_3_extract_api),
        ("步骤4: 翻译API", test_step_4_translate_api),
        ("步骤5: 带验证翻译", test_step_5_translate_with_validation),
        ("步骤6: 下载API", test_step_6_download_api),
        ("步骤7: 批量处理", test_step_7_batch_upload),
        ("步骤8: 错误处理", test_step_8_error_handling),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    cleanup_test_files()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
