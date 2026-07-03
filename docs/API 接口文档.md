# 报告审核 API 接口文档

## 📦 接口概览

提供四个核心接口：

| 接口 | 说明 | 支持格式 |
|------|------|---------|
| `/api/v1/report/extract` | Excel 数据提取 | 文件上传 / URL |
| `/api/v1/report/extract/word` | Word 文本提取 | URL |
| `/api/v1/report/annotate` | 批注写回 | 文件上传 / URL |
| `/api/v1/report/download/{filename}` | 下载审核版文件 | - |

---

## 🔌 1. Excel 数据提取接口

### 接口地址

```http
POST http://你的服务器 IP:8002/api/v1/report/extract
Content-Type: multipart/form-data
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `excel_file` | File | 否 | Excel 文件（与 `excel_url` 二选一） |
| `excel_url` | String | 否 | Excel 文件 URL（与 `excel_file` 二选一） |
| `mode` | String | 否 | 提取模式：`audit`（精简） / `full`（完整），默认 `audit` |

### 提取模式说明

| 模式 | 返回字段 | 体积 | 适用场景 |
|------|---------|------|---------|
| `audit`（推荐） | `sheets`, `key_formulas`, `summary` | 约 300KB | LLM 审核（默认） |
| `full` | `sheets`, `formulas`, `comments`, `simple_checks` | 约 2.8MB | 完整数据备份 |

### 请求示例

```bash
# 方式 1：文件上传
curl -X POST http://localhost:8002/api/v1/report/extract \
  -F "excel_file=@评估报表.xlsx" \
  -F "mode=audit"

# 方式 2：URL 下载（推荐用于 Dify）
curl -X POST http://localhost:8002/api/v1/report/extract \
  -F "excel_url=http://dify/files/xxx.xlsx" \
  -F "mode=audit"
```

### 响应格式（精简模式）

```json
{
  "success": true,
  "excel_data": {
    "file_info": {
      "sheet_names": ["评估值测算", "营运资金", "预测利润表"],
      "sheet_count": 39,
      "extract_time": "2026-06-27T02:33:54"
    },
    "sheets": {
      "评估值测算": [
        ["项目", "2018 年", "2019 年", "2020 年"],
        ["营业收入", 5000, 6000, 7200],
        ["营业成本", 3500, 4200, 5040]
      ]
    },
    "key_formulas": {
      "评估值测算": {
        "B15": "=SUM(B14:I14)",
        "B21": "=B15+B16+D17-B18-B19+D20"
      }
    },
    "summary": {
      "评估值测算": {
        "row_count": 30,
        "col_count": 10,
        "has_formula": true,
        "has_total_row": true,
        "total_row_index": 25
      }
    }
  },
  "message": "Excel 提取完成，Word 请由 Dify 处理"
}
```

### 响应字段说明

| 字段 | 说明 |
|------|------|
| `file_info.sheet_names` | 所有 Sheet 名称列表 |
| `file_info.sheet_count` | Sheet 总数 |
| `sheets` | 各 Sheet 的二维数组数据（移除空行空列） |
| `key_formulas` | 关键公式（合计行/SUM 公式） |
| `summary` | 各 Sheet 汇总统计（行数、列数、是否有公式/合计行） |

---

## 🔌 2. Word 文本提取接口

### 接口地址

```http
POST http://你的服务器 IP:8002/api/v1/report/extract/word
Content-Type: multipart/form-data
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_url` | String | 是 | Word 文件 URL（支持 .docx 格式） |

### 请求示例

```bash
curl -X POST http://localhost:8002/api/v1/report/extract/word \
  -F "file_url=http://dify/files/xxx.docx"
```

### 响应格式

```json
{
  "success": true,
  "content": "本资产评估报告依据中国资产评估准则编制\n\n福建卫东新能源股份有限公司\n\n拟股权转让涉及其股东全部权益价值\n\n资产评估报告\n\n...",
  "paragraphs": ["段落 1", "段落 2", ...],
  "tables": [
    {
      "table_index": 0,
      "markdown": "| 项目 | 账面值 | 评估值 |\n|---|---|---|\n| 货币资金 | 100 | 100 |",
      "row_count": 10,
      "col_count": 3
    }
  ],
  "paragraph_count": 500,
  "table_count": 15,
  "message": "Word 文本提取完成"
}
```

### 响应字段说明

| 字段 | 说明 |
|------|------|
| `content` | 完整文本（段落 + 表格 Markdown 标记） |
| `paragraphs` | 纯段落列表（不含表格） |
| `tables` | 表格列表（Markdown 格式） |
| `paragraph_count` | 段落数量 |
| `table_count` | 表格数量 |

---

## 🔌 3. 批注写回接口

### 接口地址

```http
POST http://你的服务器 IP:8002/api/v1/report/annotate
Content-Type: multipart/form-data
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `excel_file` | File | 否 | Excel 文件（与 `excel_url` 二选一） |
| `excel_url` | String | 否 | Excel 文件 URL |
| `report_file` | File | 否 | 评估报告 Word 文件（与 `report_url` 二选一） |
| `report_url` | String | 否 | 评估报告 Word URL |
| `explanation_file` | File | 否 | 评估说明 Word 文件（与 `explanation_url` 二选一） |
| `explanation_url` | String | 否 | 评估说明 Word URL |
| `audit_result` | String | **是** | LLM 审核结果（JSON 字符串） |

### 参数对应关系

**根据 `audit_result` 中的批注类型，必须提供对应的文件参数：**

| `audit_result.annotations` 中的批注 | 必须提供的文件参数 |
|-------------------------------------|-------------------|
| `excel` 数组有数据 | `excel_file` **或** `excel_url`（二选一） |
| `report` 数组有数据 | `report_file` **或** `report_url`（二选一） |
| `explanation` 数组有数据 | `explanation_file` **或** `explanation_url`（二选一） |

**示例：**

```json
{
  "annotations": {
    "excel": [...],    // 有 Excel 批注 → 必须传 excel_url 或 excel_file
    "report": [...],   // 有报告批注 → 必须传 report_url 或 report_file
    "explanation": []  // 无说明批注 → 可不传 explanation 参数
  }
}
```

```bash
# 正确示例：有 Excel 批注，传了 excel_url
curl -X POST http://localhost:8002/api/v1/report/annotate \
  -F "excel_url=http://dify/files/xxx.xlsx" \
  -F 'audit_result={"annotations":{"excel":[...]}}'

# 错误示例：有 Excel 批注，但没传 Excel 文件 → 跳过处理
curl -X POST http://localhost:8002/api/v1/report/annotate \
  -F 'audit_result={"annotations":{"excel":[...]}}'
# 返回：{"success": true, "annotated_files": {}}  // excel 为空，未生成文件
```

### audit_result JSON 格式

```json
{
  "audit_conclusion": "有条件通过",
  "annotations": {
    "excel": [
      {
        "location": "评估值测算!B15",
        "description": "收益现值合计公式仅对 D14 至 I14 求和，遗漏了 2018 年（D14）之前的收益现值",
        "severity": "高",
        "suggestion": "建议将公式修改为 =SUM(B14:I14)"
      },
      {
        "location": "营运资金!C22",
        "description": "2018 年期初营运资金计算公式中包含硬编码数字",
        "severity": "中",
        "suggestion": "建议将公式修改为直接引用 2017 年营运资金单元格"
      }
    ],
    "report": [
      {
        "location": "特别事项说明",
        "description": "报告披露了经营场所租赁的特别事项，但未充分披露该租赁的详细信息",
        "severity": "高",
        "suggestion": "建议在特别事项说明中补充租赁合同的关键条款"
      }
    ],
    "explanation": [
      {
        "location": "收入预测分析",
        "description": "收入预测增长率缺乏充分的量化依据",
        "severity": "中",
        "suggestion": "建议补充行业增长率、公司产能扩张计划等量化依据"
      }
    ]
  },
  "summary": {
    "total_issues": 22,
    "high_severity": 6,
    "medium_severity": 10,
    "low_severity": 6
  }
}
```

### annotations 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `location` | 是 | 批注位置（Excel: `Sheet 名!单元格`，Word: `章节名称`） |
| `description` | 是 | 问题描述 |
| `severity` | 是 | 严重程度：`高` / `中` / `低` |
| `suggestion` | 是 | 修改建议 |

### location 格式规则

| 文件类型 | 格式 | 示例 |
|---------|------|------|
| **Excel** | `Sheet 名!单元格坐标` | `评估值测算!B15`、`营运资金!C22` |
| **Word 报告** | `章节名称` | `特别事项说明`、`评估结论` |
| **Word 说明** | `章节名称` | `收益法评估技术说明`、`收入预测分析` |

### 响应格式

```json
{
  "success": true,
  "annotated_files": {
    "excel": "/api/v1/report/download/评估报表_审核版_20260627_020836.xlsx",
    "report": "/api/v1/report/download/评估报告_审核版_20260627_020836.docx",
    "explanation": "/api/v1/report/download/评估说明_审核版_20260627_020836.docx"
  },
  "summary": {
    "excel_comments": 5,
    "excel_highlights": 2,
    "report_annotations": 3,
    "explanation_annotations": 2
  },
  "match_warnings": [
    {
      "annotation_index": 0,
      "location": "评估方法",
      "description": "评估方法描述",
      "reason": "在文档中未找到关键词 '评估方法'"
    }
  ],
  "warning_count": 1
}
```

### 响应字段说明

| 字段 | 说明 |
|------|------|
| `annotated_files.excel` | Excel 审核版下载路径 |
| `annotated_files.report` | Word 报告审核版下载路径 |
| `annotated_files.explanation` | Word 说明审核版下载路径 |
| `summary.excel_comments` | Excel 批注数量 |
| `summary.excel_highlights` | Excel 高亮单元格数量（严重程度"高"） |
| `summary.report_annotations` | Word 报告批注数量 |
| `match_warnings` | Word 关键词匹配失败警告 |

---

## 🔌 4. 下载审核版文件

### 接口地址

```http
GET http://你的服务器 IP:8002/api/v1/report/download/{filename}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | String | 是 | 文件名（从 annotate 接口响应中获取） |

### 请求示例

```bash
# 下载 Excel 审核版
curl -o 评估报表_审核版.xlsx \
  http://localhost:8002/api/v1/report/download/评估报表_审核版_20260627_020836.xlsx

# 下载 Word 报告审核版
curl -o 评估报告_审核版.docx \
  http://localhost:8002/api/v1/report/download/评估报告_审核版_20260627_020836.docx
```

### 响应

- 文件流（`application/octet-stream`）

---

## 🔄 完整工作流示例

### 1. 提取 Excel 数据

```python
import requests

# Excel 提取（精简模式）
response = requests.post(
    "http://localhost:8002/api/v1/report/extract",
    data={
        "excel_url": "http://dify/files/xxx.xlsx",
        "mode": "audit"  # 精简模式，约 300KB
    }
)
excel_data = response.json()["excel_data"]
```

### 2. 提取 Word 文本

```python
# Word 提取
response = requests.post(
    "http://localhost:8002/api/v1/report/extract/word",
    data={
        "file_url": "http://dify/files/xxx.docx"
    }
)
word_content = response.json()["content"]
```

### 3. LLM 审核

```python
# 调用大模型审核（伪代码）
llm_response = call_llm(
    excel_data=excel_data,
    word_content=word_content,
    prompt="你是资产评估审核专家，请审核以下文档..."
)

# LLM 返回 22 个问题
audit_result = llm_response["annotations"]
```

### 4. 格式转换（Code 节点）

```python
def main(llm_output: dict) -> dict:
    """将 LLM 输出转换为 API 要求的格式"""
    annotations = llm_output.get('annotations', [])
    
    excel_issues = []
    report_issues = []
    explanation_issues = []
    
    for issue in annotations:
        location = convert_location(issue['location'], issue['document'])
        audit_item = {
            "location": location,
            "description": issue['issue'],
            "suggestion": issue['suggestion'],
            "severity": issue['severity']
        }
        
        if 'xlsx' in issue.get('document', '') or '报表' in issue.get('document', ''):
            excel_issues.append(audit_item)
        elif '报告' in issue.get('document', ''):
            report_issues.append(audit_item)
        else:
            explanation_issues.append(audit_item)
    
    high_count = sum(1 for i in annotations if i['severity'] == '高')
    
    return {
        "audit_conclusion": "有条件通过" if high_count > 0 else "通过",
        "annotations": {
            "excel": excel_issues,
            "report": report_issues,
            "explanation": explanation_issues
        },
        "summary": {
            "total_issues": len(annotations),
            "high_severity": high_count
        }
    }
```

### 5. 写入批注

```python
# 批注写回
response = requests.post(
    "http://localhost:8002/api/v1/report/annotate",
    data={
        "excel_url": "http://dify/files/xxx.xlsx",
        "report_url": "http://dify/files/xxx.docx",
        "explanation_url": "http://dify/files/xxx_explanation.docx",
        "audit_result": json.dumps(converted_audit_result)
    }
)

# 获取下载链接
download_links = response.json()["annotated_files"]
# 生成完整 URL
base_url = "http://localhost:8002"
excel_download = f"{base_url}{download_links['excel']}"
report_download = f"{base_url}{download_links['report']}"
explanation_download = f"{base_url}{download_links['explanation']}"
```

---

## 🤖 Dify 集成完整配置

### 工作流结构

```
开始节点 (上传 3 个文件)
    ↓
Code 节点 1 - 文件分类并保存 URL
    ↓
    ├─────────────┬─────────────┬─────────────┐
    ↓             ↓             ↓             ↓
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ HTTP   │   │ HTTP   │   │ HTTP   │   │ LLM    │
│ Excel  │   │ 报告   │   │ 说明   │   │ 审核   │
│ 提取   │   │ 提取   │   │ 提取   │   │        │
└────────┘   └────────┘   └────────┘   └────────┘
    │             │             │             │
    └─────────────┴─────────────┴─────────────┘
                              ↓
                    Code 节点 2 - 格式转换
                              ↓
                    HTTP - /annotate (批注写回)
                              ↓
                    Code 节点 3 - 提取下载链接
                              ↓
                    结束节点 - 回复用户（含下载链接）
```

---

### 开始节点配置

**输入变量：**

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `eval_report` | File | 评估报表（Excel） |
| `eval_report_doc` | File | 评估报告（Word） |
| `eval_explanation` | File | 评估说明（Word） |

---

### Code 节点 1：文件分类并保存 URL

**输入：** `files` (Array) - 来自开始节点的文件列表

**代码：**

```python
def main(files: list) -> dict:
    """
    文件分类并保存原始 URL（后续写入时复用）
    """
    excel_url = None
    report_url = None
    explanation_url = None
    
    for f in files:
        ext = f.get('extension', '').lower()
        filename = f.get('filename', '').lower()
        url = f.get('url')
        
        if ext in ['.xlsx', '.xls']:
            excel_url = url
        elif ext == '.docx':
            if '报告' in filename:
                report_url = url
            elif '说明' in filename:
                explanation_url = url
    
    return {
        "excel_url": excel_url,
        "report_url": report_url,
        "explanation_url": explanation_url,
        "file_count": len([u for u in [excel_url, report_url, explanation_url] if u])
    }
```

**输出变量：**

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `excel_url` | String | Excel 文件 URL |
| `report_url` | String | 评估报告 URL |
| `explanation_url` | String | 评估说明 URL |
| `file_count` | Integer | 有效文件数量 |

---

### HTTP 请求节点：提取数据

**Excel 提取：**

```
URL: http://172.17.0.1:8002/api/v1/report/extract
Method: POST
Content-Type: form-data

Body:
  excel_url: {{#code1.excel_url#}}
  mode: audit
```

**Word 报告提取：**

```
URL: http://172.17.0.1:8002/api/v1/report/extract/word
Method: POST
Content-Type: form-data

Body:
  file_url: {{#code1.report_url#}}
```

**Word 说明提取：**

```
URL: http://172.17.0.1:8002/api/v1/report/extract/word
Method: POST
Content-Type: form-data

Body:
  file_url: {{#code1.explanation_url#}}
```

---

### LLM 节点：审核分析

**输入：**

```
excel_data: {{#http_excel.excel_data#}}
word_report: {{#http_report.content#}}
word_explanation: {{#http_explanation.content#}}
```

**Prompt 示例：**

```
你是资产评估审核专家，请审核以下文档：

【Excel 评估报表】
{{#excel_data#}}

【评估报告】
{{#word_report#}}

【评估说明】
{{#word_explanation#}}

【审核要点】
1. 计算准确性：检查公式、合计、勾稽关系
2. 数据一致性：报表、报告、说明之间数据是否一致
3. 假设合理性：收入增长率、折现率等参数是否有依据
4. 披露充分性：特别事项、风险是否充分披露
5. 文本校对：错别字、日期、名称是否正确

【输出格式】
严格输出 JSON：
{
  "annotations": [
    {
      "id": "A-001",
      "document": "评估报表.xlsx",
      "location": "Sheet: 评估值测算，单元格：B15",
      "severity": "高",
      "dimension": "算术与数据准确性",
      "issue": "问题描述",
      "suggestion": "修改建议"
    }
  ],
  "audit_conclusion": "通过/有条件通过/不通过",
  "score": 0-100
}
```

---

### Code 节点 2：格式转换

**输入：** `llm_output` (Object) - LLM 节点的输出

**代码：**

```python
def main(llm_output: dict) -> dict:
    """
    将 LLM 输出转换为 API 要求的格式
    """
    import re
    
    annotations = llm_output.get('annotations', [])
    
    # 分类问题
    excel_issues = []
    report_issues = []
    explanation_issues = []
    
    for issue in annotations:
        # 转换 location 格式
        location = convert_location(issue['location'], issue['document'])
        
        audit_item = {
            "location": location,
            "description": issue['issue'],
            "suggestion": issue['suggestion'],
            "severity": issue['severity']
        }
        
        # 根据文档分类
        doc = issue.get('document', '')
        if 'xlsx' in doc or '报表' in doc:
            excel_issues.append(audit_item)
        elif '报告' in doc:
            report_issues.append(audit_item)
        elif '说明' in doc:
            explanation_issues.append(audit_item)
    
    # 统计
    high_count = sum(1 for i in annotations if i['severity'] == '高')
    medium_count = sum(1 for i in annotations if i['severity'] == '中')
    low_count = sum(1 for i in annotations if i['severity'] == '低')
    
    # 生成审核结论
    if high_count > 3:
        conclusion = "不通过"
    elif high_count > 0 or medium_count > 5:
        conclusion = "有条件通过"
    else:
        conclusion = "通过"
    
    return {
        "audit_conclusion": conclusion,
        "annotations": {
            "excel": excel_issues,
            "report": report_issues,
            "explanation": explanation_issues
        },
        "summary": {
            "total_issues": len(annotations),
            "high_severity": high_count,
            "medium_severity": medium_count,
            "low_severity": low_count
        }
    }


def convert_location(raw_location: str, document: str) -> str:
    """
    转换 location 格式
    
    Excel: "Sheet: 评估值测算，单元格：B15" → "评估值测算!B15"
    Word: "第四部分...- (1) 营业收入..." → "营业收入分析预测"
    """
    import re
    
    if 'xlsx' in document or '报表' in document or '测算' in document:
        # Excel 格式转换
        match = re.search(r'Sheet:\s*([^,]+),?\s*单元格：?\s*([A-Z0-9]+)', raw_location)
        if match:
            sheet = match.group(1).strip()
            cell = match.group(2).strip()
            return f"{sheet}!{cell}"
        return raw_location
    else:
        # Word 格式转换 - 取最后一级章节名
        parts = raw_location.split('-')
        if parts:
            last_part = parts[-1].strip()
            last_part = re.sub(r'^[0-9(（][^)]*[).、]\s*', '', last_part)
            return last_part
        return raw_location
```

---

### HTTP 请求节点：批注写回

```
URL: http://172.17.0.1:8002/api/v1/report/annotate
Method: POST
Content-Type: form-data

Body:
  excel_url: {{#code1.excel_url#}}      # 复用保存的 URL
  report_url: {{#code1.report_url#}}    # 复用保存的 URL
  explanation_url: {{#code1.explanation_url#}}  # 复用保存的 URL
  audit_result: {{#code2.output#}}      # JSON 字符串
```

---

### Code 节点 3：提取下载链接

**输入：** `api_response` (Object) - annotate 接口的响应

**代码：**

```python
def main(api_response: dict) -> dict:
    """
    从 annotate API 响应中提取下载链接并生成提示
    """
    import json
    
    body = api_response.get('body', '{}')
    data = json.loads(body)
    
    annotated_files = data.get('annotated_files', {})
    summary = data.get('summary', {})
    
    # 生成完整下载 URL
    base_url = "http://110.42.222.40:8002"
    
    download_links = {}
    for file_type, path in annotated_files.items():
        download_links[file_type] = f"{base_url}{path}"
    
    # 生成提示文本
    messages = []
    if 'excel' in download_links:
        count = summary.get('excel_comments', 0)
        messages.append(f"📊 Excel 审核版：{download_links['excel']}（{count} 条批注）")
    if 'report' in download_links:
        count = summary.get('report_annotations', 0)
        messages.append(f"📄 报告审核版：{download_links['report']}（{count} 条批注）")
    if 'explanation' in download_links:
        count = summary.get('explanation_annotations', 0)
        messages.append(f"📋 说明审核版：{download_links['explanation']}（{count} 条批注）")
    
    if messages:
        message = "✅ 审核完成，点击下载审核版文件：\n\n" + "\n\n".join(messages)
    else:
        message = "⚠️ 未生成审核文件，请检查输入"
    
    return {
        "download_links": download_links,
        "summary": summary,
        "success": data.get('success', False),
        "message": message
    }
```

**输出变量：**

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `download_links` | Object | 下载链接字典（excel/report/explanation） |
| `summary` | Object | 审核摘要（批注数量等） |
| `message` | String | 友好的提示文本（含下载链接） |
| `success` | Boolean | 是否成功 |

---

### 结束节点：回复用户

**回复内容：**

```
{{#code3.message#}}
```

**输出示例：**

```
✅ 审核完成，点击下载审核版文件：

📊 Excel 审核版：http://110.42.222.40:8002/api/v1/report/download/评估报表_审核版_20260627_020836.xlsx（5 条批注）

📄 报告审核版：http://110.42.222.40:8002/api/v1/report/download/评估报告_审核版_20260627_020836.docx（3 条批注）

📋 说明审核版：http://110.42.222.40:8002/api/v1/report/download/评估说明_审核版_20260627_020836.docx（2 条批注）
```

---

## ⚠️ 注意事项

1. **文件大小限制**：建议不超过 50MB
2. **临时文件清理**：extract 接口会自动删除临时文件
3. **URL 有效期**：Dify 文件 URL 有时效性，建议尽快调用（5-10 分钟内完成流程）
4. **并发处理**：目前为单实例，大批量请 Docker 部署
5. **Word 批注**：Word 使用原生批注功能，批注会显示在对应段落旁
6. **Excel 批注**：高严重程度问题会黄色高亮单元格
```

---

## ⚠️ 注意事项

1. **文件大小限制**：建议不超过 50MB
2. **临时文件清理**：定期清理 `data/uploads` 和 `data/outputs`
3. **并发处理**：目前为单实例，大批量请 Docker 部署
4. **Word 批注**：Word 使用原生批注功能，批注会显示在对应段落旁
5. **Excel 批注**：高严重程度问题会黄色高亮单元格
6. **URL 有效期**：Dify 文件 URL 有时效性，建议尽快调用

---

## 📊 数据体积对比

| 文件类型 | 原始大小 | 提取后 JSON | 模式 |
|---------|---------|-----------|------|
| Excel（39 个 Sheet） | 993 KB | 319 KB | 精简 (audit) |
| Excel（39 个 Sheet） | 993 KB | 2,673 KB | 完整 (full) |
| Word 报告 | 213 KB | 19 KB | 纯文本 |
| Word 说明 | 1.57 MB | 43 KB | 纯文本 |

---

## 🔧 Dify 集成配置

### HTTP 请求节点配置

```
URL: http://172.17.0.1:8002/api/v1/report/extract
Method: POST
Content-Type: multipart/form-data

Body:
  excel_url: {{#arg1.0.url#}}
  mode: audit
```

### Code 节点（格式转换）

```python
def main(api_response: dict) -> dict:
    import json
    body = api_response.get('body', '{}')
    data = json.loads(body)
    
    content = data.get('content', '')
    return {
        "content": content,
        "text_length": len(content)
    }
```

---

## 📝 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-06-27 | 2.0 | 新增精简模式、Word 提取接口、URL 传参支持 |
| 2026-06-26 | 1.0 | 初始版本 |
