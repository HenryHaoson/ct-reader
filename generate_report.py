#!/usr/bin/env python3
"""
Generate an HTML CT report with embedded images.
Usage: python3 generate_report.py <data.json> <output.html>
"""

import json
import base64
import sys
import os
from datetime import datetime


def image_to_base64(image_path):
    """Convert an image file to base64 data URI."""
    ext = os.path.splitext(image_path)[1].lower()
    mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}.get(ext, 'image/png')
    with open(image_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    return f'data:{mime};base64,{data}'


def generate_html(data, output_path):
    """
    Generate HTML report from structured data.

    data structure:
    {
        "patient": { "name": "...", "gender": "...", "age": "...", "exam_date": "...", "exam_type": "...", "device": "...", "visit_type": "..." },
        "report": { "doctor": "...", "date": "...", "description": "...", "diagnosis": "..." },
        "findings": [
            { "title": "区域名称", "description": "描述", "images": [{"path": "截图路径", "caption": "Im:50 肺窗 隆突层面"}] }
        ],
        "impressions": ["印象1", "印象2"],
        "recommendations": ["建议1", "建议2"],
        "screenshots": { "report_page": "path", "overview": "path" }
    }
    """

    patient = data.get('patient', {})
    report = data.get('report', {})
    findings = data.get('findings', [])
    impressions = data.get('impressions', [])
    recommendations = data.get('recommendations', [])
    screenshots = data.get('screenshots', {})

    # Build findings HTML
    findings_html = ''
    for f in findings:
        images_html = ''
        for img in f.get('images', []):
            img_path = img.get('path', '')
            caption = img.get('caption', '')
            if os.path.exists(img_path):
                src = image_to_base64(img_path)
                images_html += f'''
                <div class="image-card">
                    <img src="{src}" alt="{caption}" loading="lazy">
                    <div class="image-caption">{caption}</div>
                </div>'''

        findings_html += f'''
        <div class="finding-section">
            <h3>{f.get("title", "")}</h3>
            <p>{f.get("description", "")}</p>
            <div class="image-grid">{images_html}</div>
        </div>'''

    # Build impressions HTML
    impressions_html = '\n'.join(f'<li>{imp}</li>' for imp in impressions)
    recommendations_html = '\n'.join(f'<li>{rec}</li>' for rec in recommendations)

    # Report page screenshot
    report_page_html = ''
    rp = screenshots.get('report_page', '')
    if rp and os.path.exists(rp):
        src = image_to_base64(rp)
        report_page_html = f'<img src="{src}" alt="原始报告页" class="report-page-img">'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CT 影像 AI 辅助分析报告 - {patient.get("name", "")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1a237e, #283593);
            color: white;
            padding: 30px 40px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .header .subtitle {{
            font-size: 14px;
            opacity: 0.8;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card h2 {{
            font-size: 18px;
            color: #1a237e;
            border-bottom: 2px solid #e8eaf6;
            padding-bottom: 10px;
            margin-bottom: 16px;
        }}
        .patient-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
        }}
        .patient-item {{
            display: flex;
            flex-direction: column;
        }}
        .patient-item .label {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
        }}
        .patient-item .value {{
            font-size: 15px;
            font-weight: 500;
            color: #333;
        }}
        .finding-section {{
            margin-bottom: 24px;
        }}
        .finding-section h3 {{
            font-size: 16px;
            color: #283593;
            margin-bottom: 8px;
        }}
        .finding-section p {{
            color: #555;
            margin-bottom: 12px;
        }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }}
        .image-card {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            background: #000;
        }}
        .image-card img {{
            width: 100%;
            display: block;
        }}
        .image-caption {{
            padding: 8px 12px;
            font-size: 13px;
            color: #666;
            background: #fafafa;
            border-top: 1px solid #e0e0e0;
        }}
        .impression-list, .recommendation-list {{
            padding-left: 20px;
        }}
        .impression-list li {{
            margin-bottom: 8px;
            font-size: 15px;
            font-weight: 500;
            color: #d84315;
        }}
        .recommendation-list li {{
            margin-bottom: 6px;
            color: #555;
        }}
        .original-report {{
            background: #f9f9f9;
            border-left: 4px solid #1a237e;
            padding: 16px 20px;
            margin: 12px 0;
            font-size: 14px;
            color: #555;
        }}
        .disclaimer {{
            background: #fff3e0;
            border: 1px solid #ffe0b2;
            border-radius: 8px;
            padding: 16px 20px;
            margin-top: 24px;
            font-size: 13px;
            color: #e65100;
        }}
        .report-page-img {{
            max-width: 100%;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        .timestamp {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 20px;
            padding-bottom: 40px;
        }}
        @media print {{
            body {{ background: white; }}
            .card {{ box-shadow: none; border: 1px solid #ddd; }}
            .image-card img {{ max-height: 300px; object-fit: contain; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>CT 影像 AI 辅助分析报告</h1>
        <div class="subtitle">基于 Claude 视觉能力的智能影像分析 | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>

    <div class="card">
        <h2>患者信息</h2>
        <div class="patient-grid">
            <div class="patient-item">
                <span class="label">姓名</span>
                <span class="value">{patient.get("name", "***")}</span>
            </div>
            <div class="patient-item">
                <span class="label">性别</span>
                <span class="value">{patient.get("gender", "-")}</span>
            </div>
            <div class="patient-item">
                <span class="label">年龄</span>
                <span class="value">{patient.get("age", "-")}</span>
            </div>
            <div class="patient-item">
                <span class="label">检查日期</span>
                <span class="value">{patient.get("exam_date", "-")}</span>
            </div>
            <div class="patient-item">
                <span class="label">检查部位</span>
                <span class="value">{patient.get("exam_type", "-")}</span>
            </div>
            <div class="patient-item">
                <span class="label">设备</span>
                <span class="value">{patient.get("device", "-")}</span>
            </div>
            <div class="patient-item">
                <span class="label">就诊类型</span>
                <span class="value">{patient.get("visit_type", "-")}</span>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>原始报告（{report.get("doctor", "")} {report.get("date", "")}）</h2>
        <h3 style="font-size:14px; color:#666; margin-bottom:6px;">影像所见</h3>
        <div class="original-report">{report.get("description", "-")}</div>
        <h3 style="font-size:14px; color:#666; margin: 12px 0 6px;">诊断意见</h3>
        <div class="original-report">{report.get("diagnosis", "-")}</div>
        {report_page_html}
    </div>

    <div class="card">
        <h2>AI 影像分析</h2>
        {findings_html}
    </div>

    <div class="card">
        <h2>印象</h2>
        <ol class="impression-list">
            {impressions_html}
        </ol>
    </div>

    <div class="card">
        <h2>建议</h2>
        <ul class="recommendation-list">
            {recommendations_html}
        </ul>
    </div>

    <div class="disclaimer">
        <strong>&#9888;&#65039; 免责声明：</strong>本报告由 AI 辅助生成，仅供参考，不构成医疗诊断。
        所有医疗决策请以执业放射科医师的正式报告为准。如有健康问题，请及时就医。
    </div>

    <div class="timestamp">
        报告生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Powered by Claude + Chrome DevTools MCP
    </div>
</div>
</body>
</html>'''

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 generate_report.py <data.json> <output.html>")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)

    out = generate_html(data, sys.argv[2])
    print(f"Report generated: {out}")
