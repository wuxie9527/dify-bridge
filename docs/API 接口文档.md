# 报告审核 API 接口文档

## 📦 接口概览

提供两个核心接口：
1. **数据提取** - 提取 Excel 评估报表
2. **批注写回** - 为 Excel 和 Word 添加审核批注

---

## 🔌 1. 数据提取接口

### 请求

```http
POST http://你的服务器 IP:8002/api/v1/report/extract
Content-Type: multipart/form-data

Parameters:
  excel_file: File (评估报表.xlsx)  # 必填
```

### 响应

```json
{
  "success": true,
  "excel_data": {
    "file_info": {
      "sheet_names": ["资产明细表", "负债明细表", "净资产表"],
      "extract_time": "2026-06-26T12:00:00"
    },
    "sheets": {
      "资产明细表": [
        ["科目", "账面值", "评估值", "备注"],
        ["货币资金", 100, 100, ""],
        ["应收账款", 500, 450, "见备注 2"]
      ]
    },
    "formulas": {
      "资产明细表": {
        "C3": "=B3-C4"
      }
    },
    "comments": {
      "资产明细表": {
        "D3": "坏账按 5% 计提，评估时已单独考虑"
      }
    },
    "simple_checks": []
  },
  "message": "Excel 提取完成，Word 请由 Dify 处理"
}
```

---

## 🔌 2. 批注写回接口

### 请求

```http
POST http://你的服务器 IP:8002/api/v1/report/annotate
Content-Type: multipart/form-data

Parameters:
  excel_file: File (原评估报表.xlsx)  # 可选
  report_file: File (原评估报告.docx)  # 可选
  explanation_file: File (原评估说明.docx)  # 可选
  audit_result: String (LLM 审核结果 JSON)  # 必填
```

### audit_result JSON 格式

```json
{
  "issues": [
    {
      "location": "资产明细表!C3",
      "description": "坏账准备未说明不计入依据",
      "severity": "高",
      "suggestion": "请补充不计入资产的依据说明"
    },
    {
      "location": "评估报告",
      "description": "折现率取值未说明依据",
      "severity": "中",
      "suggestion": "请补充折现率取值依据"
    },
    {
      "location": "评估说明",
      "description": "特别事项披露不充分",
      "severity": "低",
      "suggestion": "请补充抵押资产说明"
    }
  ]
}
```

**location 规则：**
- `资产明细表!C3` - Excel 单元格（包含 `!` 字符）
- `评估报告` - Word 评估报告
- `评估说明` - Word 评估说明

### 响应

```json
{
  "success": true,
  "annotated_files": {
    "excel": "/api/v1/report/download/评估报表_审核版_20260626_120000.xlsx",
    "report": "/api/v1/report/download/评估报告_审核版_20260626_120000.docx",
    "explanation": "/api/v1/report/download/评估说明_审核版_20260626_120000.docx"
  },
  "summary": {
    "excel_comments": 5,
    "excel_highlights": 2,
    "report_sections": 1,
    "explanation_sections": 1
  }
}
```

---

## 🔌 3. 下载接口

### 请求

```http
GET http://你的服务器 IP:8002/api/v1/report/download/{filename}
```

### 响应

- 文件流（application/octet-stream）

---

## 🧪 测试示例

### cURL 测试

```bash
# 测试 Excel 提取
curl -X POST http://localhost:8002/api/v1/report/extract \
  -F "excel_file=@测试报表.xlsx"

# 测试批注写回
curl -X POST http://localhost:8002/api/v1/report/annotate \
  -F "excel_file=@测试报表.xlsx" \
  -F "report_file=@测试报告.docx" \
  -F 'audit_result={"issues":[{"location":"资产明细表!C3","description":"测试","severity":"高","suggestion":"修改"}]}'

# 下载文件
curl http://localhost:8002/api/v1/report/download/评估报表_审核版_xxx.xlsx
```

### Python 测试

```python
import requests

# 测试 Excel 提取
with open("测试报表.xlsx", "rb") as f:
    response = requests.post(
        "http://localhost:8002/api/v1/report/extract",
        files={"excel_file": f}
    )
    print(response.json())

# 测试批注写回
with open("测试报表.xlsx", "rb") as f_excel, \
     open("测试报告.docx", "rb") as f_report:
    response = requests.post(
        "http://localhost:8002/api/v1/report/annotate",
        files={
            "excel_file": f_excel,
            "report_file": f_report
        },
        data={
            "audit_result": '{"issues":[{"location":"资产明细表!C3","description":"测试","severity":"高","suggestion":"修改"}]}'
        }
    )
    print(response.json())
```

---

## ⚠️ 注意事项

1. **文件大小限制**：建议不超过 50MB
2. **临时文件清理**：定期清理 `data/uploads` 和 `data/outputs`
3. **并发处理**：目前为单实例，大批量请 Docker 部署
4. **Word 批注**：Word 不支持单元格级批注，只在文档末尾添加审核汇总章节

---

## 📝 批注形式

| 文件类型 | 批注形式 |
|---------|---------|
| **Excel** | 单元格批注 + 高亮 + 审核意见汇总 Sheet |
| **Word** | 文档末尾添加审核意见汇总章节 |
