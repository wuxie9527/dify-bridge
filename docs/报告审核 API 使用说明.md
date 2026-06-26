# 报告审核 API 使用说明

提供 Excel 评估报表的数据提取和批注写回功能。

---

## 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/report/extract` | POST | 提取 Excel 评估报表数据 |
| `/api/v1/report/annotate` | POST | 根据审核结果添加批注 |
| `/api/v1/report/download/{filename}` | GET | 下载带批注的文件 |

---

## 1. Excel 数据提取

### 接口地址
```
POST /api/v1/report/extract
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `excel_file` | File | 是 | Excel 评估报表文件（.xlsx） |

### 请求示例

```bash
curl -X POST http://localhost:8002/api/v1/report/extract \
  -F "excel_file=@评估报表.xlsx"
```

### 响应格式

```json
{
  "success": true,
  "excel_data": {
    "file_info": {
      "path": "文件完整路径",
      "sheet_names": ["资产明细表", "负债明细表", "净资产表"],
      "extract_time": "2026-06-27T02:33:54.050580"
    },
    "sheets": {
      "资产明细表": [
        ["科目", "账面值", "评估值", "备注"],
        ["货币资金", 100000, 100000, null],
        ["应收账款", 500000, 450000, "见备注"],
        ["合计", "=SUM(B2:B5)", "=SUM(C2:C5)", null]
      ],
      "负债明细表": [...]
    },
    "formulas": {
      "资产明细表": {
        "B6": {
          "formula": "=SUM(B2:B5)",
          "display_value": "=SUM(B2:B5)",
          "row": 6,
          "column": "B"
        }
      }
    },
    "comments": {
      "资产明细表": {
        "C3": {
          "text": "坏账按 5% 计提",
          "author": "评估师",
          "row": 3,
          "column": "C"
        }
      }
    },
    "simple_checks": [
      {
        "type": "summary_row_found",
        "location": "资产明细表!A6",
        "message": "发现汇总行：合计"
      }
    ]
  },
  "message": "Excel 提取完成，Word 请由 Dify 处理"
}
```

### 响应字段说明

#### `excel_data.file_info`
| 字段 | 类型 | 说明 |
|------|------|------|
| `path` | string | 文件存储路径 |
| `sheet_names` | string[] | 所有 Sheet 名称列表 |
| `extract_time` | string | ISO8601 格式提取时间 |

#### `excel_data.sheets`
每个 Sheet 返回二维数组：
```json
{
  "资产明细表": [
    ["科目", "账面值", "评估值", "备注"],  // 行 1（表头）
    ["货币资金", 100000, 100000, null],   // 行 2
    ["应收账款", 500000, 450000, "见备注"] // 行 3
  ]
}
```

**单元格坐标对应关系：**
```
        A           B           C           D
     科目        账面值       评估值        备注
1    科目        账面值       评估值        备注
2    货币资金    100000      100000       (空)
3    应收账款    500000      450000       见备注
```

- `B3` = 500000（应收账款的账面值）
- `C3` = 450000（应收账款的评估值）

#### `excel_data.formulas`
| 字段 | 类型 | 说明 |
|------|------|------|
| `formula` | string | 公式内容 |
| `display_value` | string | 显示值（公式计算结果） |
| `row` | integer | 行号 |
| `column` | string | 列号 |

#### `excel_data.comments`
| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 批注内容 |
| `author` | string | 批注作者 |
| `row` | integer | 行号 |
| `column` | string | 列号 |

#### `excel_data.simple_checks`
自动执行的简单检查：
- `summary_row_found`：发现汇总行
- `formula_error`：公式错误

---

## 2. 批注写回

### 接口地址
```
POST /api/v1/report/annotate
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `excel_file` | File | 否 | 原评估报表 Excel 文件 |
| `report_file` | File | 否 | 原评估报告 Word 文件 |
| `explanation_file` | File | 否 | 原评估说明 Word 文件 |
| `audit_result` | String | 是 | LLM 审核结果（JSON 字符串） |

### `audit_result` JSON 格式

```json
{
  "audit_conclusion": "有条件通过",
  "score": 75,
  "annotations": {
    "excel": [
      {
        "location": "资产明细表!B3",
        "type": "cell_comment",
        "description": "货币资金账面值与银行对账单不符",
        "severity": "高",
        "suggestion": "请提供最新银行对账单进行核对"
      },
      {
        "location": "资产明细表!C4",
        "type": "cell_comment",
        "description": "存货评估值低于账面值，可能存在减值",
        "severity": "中",
        "suggestion": "请补充存货减值测试报告"
      }
    ],
    "report": [
      {
        "location": "一、评估目的",
        "type": "section_comment",
        "description": "评估目的描述完整",
        "severity": "低",
        "suggestion": "无需修改"
      },
      {
        "location": "特别事项说明",
        "type": "section_comment",
        "description": "特别事项披露不充分",
        "severity": "高",
        "suggestion": "请补充抵押、担保等事项说明"
      }
    ],
    "explanation": [
      {
        "location": "特别事项说明",
        "type": "section_comment",
        "description": "评估说明中特别事项披露不完整",
        "severity": "中",
        "suggestion": "请补充相关说明"
      }
    ]
  },
  "summary": {
    "total_issues": 5,
    "high_severity": 2,
    "medium_severity": 2,
    "low_severity": 1
  }
}
```

### `location` 格式规则

| 文件类型 | 格式 | 示例 |
|---------|------|------|
| **Excel** | `Sheet 名!单元格坐标` | `资产明细表!B3` |
| **Word 评估报告** | `章节名称` | `一、评估目的` |
| **Word 评估说明** | `章节名称` | `特别事项说明` |

### 批注字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `location` | string | 是 | 批注位置（Excel: `Sheet!单元格`，Word: `章节名`） |
| `type` | string | 是 | 批注类型：`cell_comment`（单元格）/ `section_comment`（章节） |
| `description` | string | 是 | 问题描述 |
| `severity` | string | 是 | 严重程度：`高` / `中` / `低` |
| `suggestion` | string | 是 | 修改建议 |

### 请求示例

```bash
curl -X POST http://localhost:8002/api/v1/report/annotate \
  -F "excel_file=@评估报表.xlsx" \
  -F "report_file=@评估报告.docx" \
  -F 'audit_result={
    "audit_conclusion": "有条件通过",
    "score": 75,
    "annotations": {
      "excel": [
        {
          "location": "资产明细表!B3",
          "type": "cell_comment",
          "description": "货币资金账面值与银行对账单不符",
          "severity": "高",
          "suggestion": "请提供银行对账单"
        }
      ],
      "report": [
        {
          "location": "特别事项说明",
          "type": "section_comment",
          "description": "特别事项披露不充分",
          "severity": "高",
          "suggestion": "请补充抵押事项说明"
        }
      ]
    }
  }'
```

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
    "excel_comments": 2,
    "excel_highlights": 1,
    "report_annotations": 1,
    "explanation_annotations": 1
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

| 字段 | 类型 | 说明 |
|------|------|------|
| `annotated_files.excel` | string | Excel 审核版下载路径 |
| `annotated_files.report` | string | Word 报告审核版下载路径 |
| `annotated_files.explanation` | string | Word 说明审核版下载路径 |
| `summary.excel_comments` | integer | Excel 批注数量 |
| `summary.excel_highlights` | integer | Excel 高亮单元格数量（严重程度"高"的） |
| `summary.report_annotations` | integer | Word 报告批注数量 |
| `summary.explanation_annotations` | integer | Word 说明批注数量 |
| `match_warnings` | array | 关键词匹配失败警告列表 |
| `warning_count` | integer | 警告数量 |

---

## 3. 下载审核版文件

### 接口地址
```
GET /api/v1/report/download/{filename}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | string | 是 | 文件名（从 annotate 接口响应中获取） |

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

## 完整工作流示例

```
1. 上传 Excel → /api/v1/report/extract
   ↓
   返回：sheets, formulas, comments
   
2. 将提取的数据发送给 LLM 审核
   ↓
   LLM 返回：annotations（问题列表）
   
3. 调用 /api/v1/report/annotate
   传入：原文件 + LLM 返回的 annotations
   ↓
   返回：annotated_files（审核版下载路径）
   
4. 下载审核版文件
   ↓
   完成！
```

---

## Python 调用示例

```python
import requests
import json

# 步骤 1: 提取 Excel 数据
with open("评估报表.xlsx", "rb") as f:
    response = requests.post(
        "http://localhost:8002/api/v1/report/extract",
        files={"excel_file": f}
    )
    excel_data = response.json()["excel_data"]

# 步骤 2: 模拟 LLM 审核结果
audit_result = {
    "audit_conclusion": "有条件通过",
    "score": 75,
    "annotations": {
        "excel": [
            {
                "location": "资产明细表!B3",
                "type": "cell_comment",
                "description": "货币资金账面值需要核实",
                "severity": "高",
                "suggestion": "请提供银行对账单"
            }
        ],
        "report": []
    }
}

# 步骤 3: 写入批注
with open("评估报表.xlsx", "rb") as f:
    response = requests.post(
        "http://localhost:8002/api/v1/report/annotate",
        files={"excel_file": ("评估报表.xlsx", f)},
        data={"audit_result": json.dumps(audit_result)}
    )
    result = response.json()

# 步骤 4: 下载审核版
for file_type, path in result["annotated_files"].items():
    filename = path.split("/")[-1]
    download_url = f"http://localhost:8002{path}"
    with requests.get(download_url, stream=True) as r:
        with open(f"审核版_{file_type}.xlsx", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

print("完成！")
```

---

## 注意事项

1. **文件大小限制**：建议不超过 50MB
2. **Excel 批注位置**：使用 `Sheet 名!单元格坐标` 格式，如 `资产明细表!B3`
3. **Word 批注位置**：使用文档中的章节名称作为关键词，如 `特别事项说明`
4. **临时文件清理**：定期清理 `data/uploads` 和 `data/outputs` 目录
5. **并发处理**：当前为单实例，大批量请使用 Docker 部署

---

## 批注形式

| 文件类型 | 批注形式 |
|---------|---------|
| **Excel** | 单元格批注 + 高亮 + 审核意见汇总 Sheet |
| **Word** | 文档末尾添加审核意见汇总章节 |

---

## 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-06-27 | 1.0.0 | 初始版本 |
