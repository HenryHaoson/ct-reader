---
name: ct-reader
description: |
  CT 报告智能解读技能。通过 Chrome DevTools MCP 打开 CT 影像页面，
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

1. **直接提供 URL**：CT 报告页面地址
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

---

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

### Step 1：打开页面 → 识别系统 → 提取报告信息

```
1. 使用 navigate_page 打开 URL
2. 使用 wait_for 等待页面加载，关键词：["图像", "影像", "报告", "Image", "检查", "患者", "DICOM"]
3. 使用 take_screenshot 截图，保存为 output/screenshots/00_report_page.png
4. 使用 take_snapshot 获取 DOM 结构

5. 【识别系统】根据 DOM 特征判断 PACS 系统类型：
   - 查看页面标题、logo、heading 文本
   - 对照下方「已知系统适配」章节
   - 如果是未知系统，通过 DOM snapshot 自行探索页面结构

6. 从 DOM 中提取：
   - 患者信息（姓名、性别、年龄、检查日期）
   - 检查类型（检查部位、设备）
   - 报告文本（影像所见、诊断意见、报告医师）
```

### Step 2：识别检查类型 → 进入图像查看器

```
1. 根据提取到的检查信息，判断扫描类型：
   - 胸部 CT（含颈胸联合、胸部增强等）
   - 头颅 CT
   - 腹部 CT
   - 其他部位
   → 扫描类型决定 Step 3 的截图策略

2. 在 DOM 中找到进入影像查看器的入口并 click
   - 可能是文本 "Image"、"图像"、"影像"、图标按钮等
   - 对照已知系统适配章节

3. 等待查看器加载完成
```

### Step 3：探索序列 → 动态截图

**3a. 探索可用序列：**
```
1. take_snapshot 获取查看器 DOM
2. 识别底部/侧边的序列缩略图栏，列出所有可用序列
   - 记录每个序列的名称、描述文字
3. 逐个点击序列，记录：
   - 序列名称（如 "lung 3mm", "STD 3mm", "bone", "brain" 等）
   - 总张数（从页面上 "1/N" 或 "Im:1" 类信息获取）
   - 窗宽窗位（W/L 值）
   - 重建方向（轴位/冠状位/矢状位）
4. 回到第一个序列，准备截图
```

**3b. 制定截图计划：**

根据扫描类型和可用序列，动态制定截图计划。原则：
- **每个序列均匀采样**：总张数 / 期望截图数 = 步长，从序列开头到结尾均匀截取
- **关键窗位都要覆盖**：同一解剖层面，不同窗位（如肺窗+纵隔窗）都要截
- **重建序列全覆盖**：冠状位/矢状位/3D 重建张数通常较少，尽量多截
- **优先厚层序列**（3mm/5mm），加载快且信息足够

各扫描类型的截图策略：

**胸部 CT：**
```
软组织窗/肺窗轴位序列：~20 张（均匀覆盖从扫描起点到终点）
纵隔窗/软组织窗轴位序列：~9 张（对应肺窗的关键层面）
冠状位重建：3 张（前1/4、中间、后3/4 位置）
矢状位重建（如有）：3 张
特殊重建（气道/MIP/MinIP）：全部截取
```

**头颅 CT：**
```
脑窗轴位序列：~15 张（颅底到颅顶均匀覆盖）
骨窗轴位序列：~10 张（重点颅底、颞骨、鼻窦）
冠状位重建（如有）：3 张
矢状位重建（如有）：3 张
```

**腹部 CT：**
```
软组织窗轴位序列：~20 张（膈顶到盆腔均匀覆盖）
如有多期增强（平扫/动脉期/门脉期/延迟期）：每期 ~10 张
冠状位重建：3 张
```

**通用规则（适用于所有类型）：**
```
如果序列总张数 ≤ 10：全部截取
如果序列总张数 ≤ 30：每隔 2-3 张截取一次
如果序列总张数 ≤ 80：每隔 3-5 张截取一次
如果序列总张数 > 80：每隔 5-8 张截取一次
```

**3c. 执行截图：**
```
所有截图使用 take_screenshot(filePath=...) 保存到 output/screenshots/ 目录。

文件命名规则：{序号}_{序列名}_{im编号}_{解剖描述}.png
例如：
  01_lung_im05_pharynx.png
  15_std_im50_carina.png
  30_coronal_im40_mid.png

翻片方式：
  - 优先使用页面上的前进/后退导航按钮（通过 click）
  - 批量翻片用 evaluate_script 执行循环点击
  - 注意：合成 WheelEvent 和键盘事件在大多数 PACS 查看器中无效，
    必须找到实际的 DOM 按钮进行 click
```

### Step 4：独立分析影像

**重要：不要只复述原始报告，必须基于截图独立读片。**

根据扫描类型，重点关注不同内容：

**胸部 CT 关注点：**
- 肺实质：磨玻璃影、实变、结节、肿块、空洞
- 气道：支气管壁增厚、支气管扩张、管腔狭窄
- 分布特征：弥漫/局灶、上肺/下肺、对称性
- 特征性征象：马赛克灌注、树芽征、铺路石征、晕征
- 纵隔：淋巴结、大血管、食管
- 胸膜/胸壁：积液、气胸、胸膜增厚

**头颅 CT 关注点：**
- 脑实质：密度异常（高密度=出血/钙化、低密度=梗死/水肿）
- 脑室系统：大小、对称性、积水
- 中线结构：有无偏移
- 骨窗：骨折、颅缝异常
- 鼻窦/乳突：有无积液

**腹部 CT 关注点：**
- 实质脏器：肝脾肾胰形态、密度
- 空腔脏器：肠壁增厚、扩张、梗阻
- 腹腔：积液、淋巴结
- 血管：主动脉、门静脉
- 增强特征：强化方式、时相差异

**通用关注点：**
- 与原始报告的异同——发现原始报告未提及的异常
- 测量关键病变大小（如可测量）
- 提供鉴别诊断

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
      "title": "区域名称",
      "description": "AI 独立分析描述，包含具体征象和分布特点",
      "images": [
        {
          "path": "output/screenshots/11_lung_im50_carina.png",
          "caption": "Im:50 肺窗 — 隆突层面 ★"
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
按解剖区域组织，每个区域关联该区域的 CT 截图（多窗位对照），确保诊断与图片一一对应。
分区方式根据扫描类型动态决定：

- **胸部 CT**：颈部 → 胸廓入口 → 上纵隔 → 主动脉弓/肺尖 → 隆突/肺动脉窗 → 中肺野/肺门 → 心脏/下肺 → 膈肌 → 重建序列
- **头颅 CT**：颅底/后颅窝 → 小脑/脑干 → 颞叶/基底节 → 侧脑室体部 → 半卵圆中心 → 顶叶/颅顶 → 骨窗发现
- **腹部 CT**：膈下/肝顶 → 肝脾/胆囊 → 胰腺/肾上腺 → 肾脏 → 肠管/腹膜后 → 盆腔

最后用 `open output/ct_report.html` 在浏览器中打开报告。

---

## 已知系统适配

### 东软睿影（Neusoft Ruiying）云胶片 V1.0

**识别特征：** 页面 heading 含 "Neusoft Ruiying"，URL 含 `M-Viewer`

**报告页（profilesign）：**
```
- banner > heading "Neusoft Ruiying"
- banner > heading "患者名 性别 / 年龄"
- main > StaticText "Report"  ← 点击查看完整报告单（含三审医师签名）
- main > StaticText "Image"   ← 点击进入影像查看器
- main > heading "Image description" → 影像所见
- main > heading "Diagnosis opinion" → 诊断意见
```

**影像查看器（display）：**
```
- 导航按钮：a.lastone（上一张）、a.nextone（下一张）
- 底部序列缩略图栏（点击切换序列）
- canvas.figure 主图像画布
- 图像信息文本：Series、Im、W/L 值、层厚
- 翻片 JS：document.querySelector('a.nextone').click()
- 批量翻片：
  const nextBtn = document.querySelector('a.nextone');
  for (let i = 0; i < N; i++) { nextBtn.click(); }
- ⚠️ WheelEvent 和键盘事件（ArrowDown 等）无效，只能用按钮 click
```

**已知序列类型（Philips iDose 协议示例）：**
```
- "lung, iDose"（3mm 厚层肺窗轴位）→ W:1300/L:-600
- "STD, iDose"（3mm 厚层纵隔窗轴位）→ W:350/L:60
- "LUNG, iDose"（冠状位重建）
- "Processed"（气道 3D 重建，通常 2-4 张）
- "Exam Summary"（扫描摘要，通常 8 张，可跳过）
- 0.6mm 薄层序列（张数多 ~485 张，跳过，用厚层即可）
```

---

## 注意事项

1. **隐私保护**：报告中患者姓名必须脱敏（保留姓，名用***替换）
2. **医学免责**：每份报告必须包含免责声明
3. **独立读片**：不要只复述原始报告，必须基于截图做独立分析，指出具体征象和鉴别诊断
4. **截图保存**：所有截图用 filePath 参数保存到文件，用于 HTML 报告内嵌
5. **翻片方式**：合成 WheelEvent/键盘事件在多数 PACS 中无效，必须找 DOM 按钮 click
6. **序列选择**：优先厚层序列（3mm/5mm），加载快且信息足够
7. **未知系统**：遇到未适配的 PACS 系统，通过 take_snapshot 探索 DOM，找到导航元素后记录到本文件
