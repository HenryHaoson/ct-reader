---
name: ct-reader
description: |
  CT 报告智能解读技能。通过 Chrome DevTools MCP 打开 CT 影像页面（如东软睿影 PACS），
  自动浏览并截取 CT 图片，利用 Claude 视觉能力分析影像并生成结构化 HTML 报告。
  支持从图片中的二维码自动提取链接。
  触发词：CT 报告、CT 解读、读片、影像报告、CT 分析、医学影像、PACS、东软睿影
---

# CT 报告智能解读

通过 Chrome DevTools MCP 自动打开 CT 影像页面，截取关键图片，利用 Claude 视觉能力进行独立分析，并生成结构化 HTML 报告（诊断与图片一一对应）。

## 前置条件

- 已配置 `chrome-devtools` MCP Server（`npx chrome-devtools-mcp@latest`）
- Chrome 浏览器可用
- `zbarimg` 已安装（`brew install zbar`）—— 用于从图片解码二维码

## 输入方式（二选一）

1. **直接提供 URL**：CT 报告页面地址（如东软睿影短链接）
2. **提供含二维码的图片**：用户拍照/截图中包含二维码，自动解码提取 URL

```bash
# 二维码解码命令（项目内 decode_qr.sh）
zbarimg --quiet --raw <图片路径> 2>/dev/null | head -1
```

如果用户提供的是图片文件路径，先用 Read 工具查看图片确认含有二维码，再用 Bash 执行上述命令提取 URL。

## 输出

- **HTML 报告文件**：`output/ct_report.html`，可直接在浏览器中打开
- 所有截图内嵌为 base64，单文件即可分享
- 诊断发现与对应 CT 截图一一对应

## 执行流程

### Step 0：获取 URL

```
如果输入是图片：
  1. 用 Read 工具查看图片，确认有二维码
  2. 用 Bash 执行：zbarimg --quiet --raw <图片路径> 2>/dev/null | head -1
  3. 提取出的 URL 作为后续步骤的输入

如果输入是 URL：
  直接使用
```

### Step 1：打开页面并提取报告信息

```
1. 使用 navigate_page 打开 URL（短链接自动跳转到 M-Viewer/#/profilesign?check=...）
2. 使用 wait_for 等待页面加载，关键词：["图像", "影像", "报告", "Image", "检查", "患者"]
3. 使用 take_screenshot(filePath=output/screenshots/00_report_page.png) 保存报告页截图
4. 从 DOM snapshot 中提取患者信息和报告文本

注意：报告页有两种布局：
  - 简版：banner 中直接显示患者名和简要报告
  - 完整版：点击 "Report" 后显示医院正式报告单（含报告医师签名）
  如果能看到完整报告单，优先截取完整版
```

### Step 2：进入图像查看器

```
1. 在 DOM snapshot 中找到文本为 "Image" 的元素并 click
2. 页面跳转到 M-Viewer/#/display
3. wait_for ["Im:1", "1/"]，如看到 "序列加载中..." 需额外等待
```

### Step 3：按区域截取关键层面（保存到文件）

所有截图使用 `take_screenshot(filePath=...)` 保存到 `output/screenshots/` 目录。

**肺窗（lung 序列，W:1300/L:-600）：**
```javascript
// 切换：点击底部 "lung, iDose" 缩略图
// 翻片：
() => {
  const nextBtn = document.querySelector('a.nextone');
  for (let i = 0; i < N; i++) { nextBtn.click(); }
}

// 推荐截取层面（81 张序列，每隔 3-5 张截取一次）：
// Im:5  → 锁骨上区 → 01_lung_im05_supraclav.png
// Im:10 → 胸廓入口 → 02_lung_im10_inlet.png
// Im:15 → 颈根部/上纵隔 → 03_lung_im15_upper_mediastinum.png
// Im:20 → 气管上段 → 04_lung_im20_trachea.png
// Im:25 → 主动脉弓 → 05_lung_im25_aortic_arch.png
// Im:30 → 颈部/喉部 → 06_lung_im30_neck.png
// Im:35 → 气管分叉上方 → 07_lung_im35_pretracheal.png
// Im:40 → 肺尖 → 08_lung_im40_apex.png
// Im:45 → 上肺野 → 09_lung_im45_upper.png
// Im:48 → 主肺动脉窗 ★ → 10_lung_im48_ap_window.png
// Im:50 → 隆突 ★ → 11_lung_im50_carina.png
// Im:53 → 左右主支气管 → 12_lung_im53_bronchi.png
// Im:55 → 中肺野 → 13_lung_im55_mid.png
// Im:58 → 中肺野偏下 → 14_lung_im58_mid_lower.png
// Im:60 → 心脏层面 ★ → 15_lung_im60_heart.png
// Im:63 → 下肺野上部 → 16_lung_im63_lower_upper.png
// Im:65 → 下肺野 → 17_lung_im65_lower.png
// Im:68 → 肋膈角 → 18_lung_im68_costophrenic.png
// Im:72 → 膈肌层面 → 19_lung_im72_diaphragm.png
// Im:76 → 上腹部 → 20_lung_im76_upper_abdomen.png
```

**纵隔窗（STD 序列，W:350/L:60）：**
```
// 切换：点击底部 "STD, iDose" 缩略图
// 截取层面（与肺窗对应关键层面）：
// Im:25 → 主动脉弓 → 21_std_im25_aortic_arch.png
// Im:35 → 气管分叉上方 → 22_std_im35_pretracheal.png
// Im:40 → 肺尖/腋窝淋巴结 → 23_std_im40_apex.png
// Im:48 → 主肺动脉窗 ★ → 24_std_im48_ap_window.png
// Im:50 → 隆突 ★ → 25_std_im50_carina.png
// Im:55 → 心腔/肺门 → 26_std_im55_hilum.png
// Im:60 → 心脏 ★ → 27_std_im60_heart.png
// Im:65 → 下肺/下纵隔 → 28_std_im65_lower.png
// Im:72 → 膈肌 → 29_std_im72_diaphragm.png
```

**冠状位重建（LUNG 序列）：**
```
// 切换：点击底部 "LUNG, iDose" 缩略图
// 截取前、中、后三个层面：
// Im:20 → 前部（胸骨后） → 30_coronal_im20_anterior.png
// Im:40 → 中部（气管/主支气管）★ → 31_coronal_im40_mid.png
// Im:60 → 后部（脊柱旁） → 32_coronal_im60_posterior.png
```

**气道重建（Processed 序列）：**
```
// 切换：点击底部 "Processed" 缩略图
// 全部截取（通常 2-4 张）→ 33_processed_im1.png, 34_processed_im2.png, ...
```

### Step 4：独立分析影像

**重要：不要只复述原始报告，必须基于截图独立读片。**

对每个截图进行仔细分析，关注：
- 密度异常（磨玻璃影、实变、结节）
- 分布特征（弥漫/局灶、上肺/下肺、对称性）
- 特征性征象（马赛克灌注、树芽征、支气管壁增厚等）
- 与原始报告的异同

### Step 5：生成 HTML 报告

构建 JSON 数据结构，调用 `generate_report.py` 生成 HTML：

```bash
python3 generate_report.py output/report_data.json output/ct_report.html
```

**JSON 数据结构（report_data.json）：**
```json
{
  "patient": {
    "name": "***（脱敏）",
    "gender": "男",
    "age": "25月",
    "exam_date": "2026-03-27",
    "exam_type": "颈部+胸部+气道重建（CT）",
    "device": "Philips",
    "visit_type": "门诊"
  },
  "report": {
    "doctor": "报告医师",
    "date": "2026-03-27",
    "description": "影像所见原文...",
    "diagnosis": "诊断意见原文..."
  },
  "findings": [
    {
      "title": "区域名称（如：隆突及中肺野）",
      "description": "AI 独立分析描述，包含具体征象和分布特点",
      "images": [
        {
          "path": "output/screenshots/04_lung_im50_carina.png",
          "caption": "Im:50 肺窗 — 隆突层面，双肺马赛克灌注征 ★"
        }
      ]
    }
  ],
  "impressions": ["印象1（含鉴别诊断）", "印象2"],
  "recommendations": ["建议1", "建议2"],
  "screenshots": {
    "report_page": "output/screenshots/00_report_page.png"
  }
}
```

**findings 分区原则：**
按解剖区域组织，每个区域关联该区域的 CT 截图（肺窗 + 纵隔窗对照），确保诊断与图片一一对应：
1. 锁骨上区及颈根部 → Im:5-15 肺窗截图
2. 上纵隔及气管 → Im:20-30 肺窗 + Im:25 纵隔窗截图
3. 主动脉弓及肺尖 → Im:35-40 肺窗 + Im:35-40 纵隔窗截图
4. 肺动脉窗及隆突（关键区域）→ Im:45-53 肺窗 + Im:48-50 纵隔窗截图
5. 中肺野及肺门 → Im:55-58 肺窗 + Im:55 纵隔窗截图
6. 心脏及下肺野 → Im:60-65 肺窗 + Im:60-65 纵隔窗截图
7. 肋膈角及膈肌 → Im:68-76 肺窗 + Im:72 纵隔窗截图
8. 冠状位重建 → 前/中/后三个层面截图
9. 气道三维重建 → Processed 序列全部截图

最后用 `open output/ct_report.html` 在浏览器中打开报告。

## 东软睿影系统 DOM 参考（已验证）

### 报告页（profilesign）
```
- banner > heading "Neusoft Ruiying"
- banner > heading "患者名 性别 / 年龄"
- main > StaticText "Report" / "Image"  ← 点击 Image 进入查看器
- main > heading "Image description" → 影像所见
- main > heading "Diagnosis opinion" → 诊断意见
- 完整报告页（点击 Report 后）含医院抬头、三审医师签名
```

### 影像查看器（display）
```
- 导航按钮：a.lastone（上一张）、a.nextone（下一张）
- 底部序列缩略图栏（点击切换序列）
- canvas.figure 主图像画布
- 图像信息：Series、Im、W/L 值、层厚
- 翻片 JS：document.querySelector('a.nextone').click()
- 批量翻片：for (let i=0; i<N; i++) { nextBtn.click(); }
```

## 注意事项

1. **隐私保护**：报告中患者姓名必须脱敏（保留姓，名用***替换）
2. **医学免责**：每份报告必须包含免责声明
3. **独立读片**：不要只复述原始报告，必须基于截图做独立分析，指出具体征象和鉴别诊断
4. **截图保存**：所有截图用 filePath 参数保存到文件，用于 HTML 报告内嵌
5. **翻片方式**：只能用 `a.nextone`/`a.lastone` 的 click()，WheelEvent 无效
6. **序列选择**：优先厚层序列（3mm），加载快且信息足够
