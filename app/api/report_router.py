# -*- coding: utf-8 -*-
"""
报告审核 API（带严格校验）
提供两个核心接口：
1. Excel 提取
2. 批注写回（带文件 - 批注匹配校验）
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, Optional, List, Tuple
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.services.excel_extractor import ExcelExtractor
from app.services.excel_annotator import ExcelAnnotator
from app.services.word_annotator import WordAnnotator

router = APIRouter(prefix="/api/v1/report", tags=["报告审核"])

# 临时文件存储目录
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "outputs")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_temp_file(file: UploadFile, suffix: str = "") -> str:
    """保存上传的文件到临时目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}{suffix}"
    file_path = os.path.join(TEMP_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path


def validate_annotations(audit_data: Dict, files_provided: Dict[str, bool]):
    """
    校验文件和批注的匹配关系

    Args:
        audit_data: 审核结果 JSON 对象
        files_provided: 文件提供情况 {"excel": True/False, "report": True/False, "explanation": True/False}

    Raises:
        HTTPException: 校验失败时抛出
    """
    annotations = audit_data.get("annotations", {})

    errors = []

    # Excel 校验
    if files_provided.get("excel", False):
        excel_annotations = annotations.get("excel", [])
        if not excel_annotations:
            errors.append("上传了 Excel 文件，但 annotations.excel 为空。请提供 Excel 单元格的批注内容。")
        else:
            # 验证每个 Excel 批注的 location 格式
            for i, ann in enumerate(excel_annotations):
                location = ann.get("location", "")
                if "!" not in location:
                    errors.append(f"Excel 批注[{i}] 的 location 格式错误：'{location}'。应为 'Sheet 名!单元格' 格式，如 '资产明细表!C3'")
                if not ann.get("description"):
                    errors.append(f"Excel 批注[{i}] 缺少 description 字段")
                if not ann.get("suggestion"):
                    errors.append(f"Excel 批注[{i}] 缺少 suggestion 字段")

    # Word 报告校验
    if files_provided.get("report", False):
        report_annotations = annotations.get("report", [])
        if not report_annotations:
            errors.append("上传了评估报告 Word 文件，但 annotations.report 为空。请提供报告章节的批注内容。")
        else:
            for i, ann in enumerate(report_annotations):
                location = ann.get("location", "")
                if not location:
                    errors.append(f"报告批注[{i}] 缺少 location 字段（应为章节名称，如'评估方法'）")
                if not ann.get("description"):
                    errors.append(f"报告批注[{i}] 缺少 description 字段")
                if not ann.get("suggestion"):
                    errors.append(f"报告批注[{i}] 缺少 suggestion 字段")

    # Word 说明校验
    if files_provided.get("explanation", False):
        explanation_annotations = annotations.get("explanation", [])
        if not explanation_annotations:
            errors.append("上传了评估说明 Word 文件，但 annotations.explanation 为空。请提供说明章节的批注内容。")
        else:
            for i, ann in enumerate(explanation_annotations):
                location = ann.get("location", "")
                if not location:
                    errors.append(f"说明批注[{i}] 缺少 location 字段（应为章节名称，如'特别事项说明'）")
                if not ann.get("description"):
                    errors.append(f"说明批注[{i}] 缺少 description 字段")
                if not ann.get("suggestion"):
                    errors.append(f"说明批注[{i}] 缺少 suggestion 字段")

    # 如果没有上传任何文件
    if not any(files_provided.values()):
        errors.append("请至少上传一个文件（Excel 评估报表 / Word 评估报告 / Word 评估说明）")

    # 校验：如果上传了文件，必须至少有一个批注
    total_annotations = (
        len(annotations.get("excel", [])) +
        len(annotations.get("report", [])) +
        len(annotations.get("explanation", []))
    )
    if any(files_provided.values()) and total_annotations == 0:
        errors.append("已上传文件但 annotations 为空。请提供至少一条批注内容。")

    if errors:
        raise HTTPException(status_code=400, detail="\n".join(errors))


def process_excel_annotations(excel_path: str, annotations: List[Dict]) -> str:
    """
    处理 Excel 批注

    Returns:
        输出文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"评估报表_审核版_{timestamp}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with ExcelAnnotator(excel_path) as annotator:
        for issue in annotations:
            location = issue.get("location", "")
            if "!" in location:
                sheet_name, cell = location.split("!", 1)
                comment_text = f"{issue['description']}\n\n建议：{issue.get('suggestion', '')}"

                annotator.add_comment(
                    sheet_name=sheet_name,
                    cell=cell,
                    comment=comment_text,
                    author="审核 AI"
                )

                if issue.get("severity") == "高":
                    annotator.highlight_cell(sheet_name, cell, "FFFF00")

        annotator.create_audit_sheet(annotations)
        annotator.save(output_path)

    return output_filename


def process_word_annotations(word_path: str, annotations: List[Dict], file_type: str = "报告") -> Tuple[str, List[Dict]]:
    """
    处理 Word 批注（在原文位置添加，移除末尾汇总）

    Returns:
        (输出文件路径，匹配失败的警告列表)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"评估{file_type}_审核版_{timestamp}.docx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with WordAnnotator(word_path) as annotator:
        # 在原文位置添加批注
        warnings = annotator.annotate_document(annotations)

        # 调试：打印匹配结果
        logger.info(f"Word {file_type} 批注处理完成：{len(annotations)} 条批注，{len(warnings)} 条匹配失败")
        for w in warnings:
            logger.warning(f"  - {w['location']}: {w['reason']}")

        # 不再添加末尾汇总
        annotator.save(output_path)

    return output_filename, warnings


@router.post("/extract")
async def extract_excel(excel_file: UploadFile = File(..., description="评估报表 Excel")):
    """
    提取 Excel 评估报表数据
    """
    try:
        excel_path = save_temp_file(excel_file, ".xlsx")

        with ExcelExtractor(excel_path) as extractor:
            excel_data = extractor.extract_all()

        return {
            "success": True,
            "excel_data": excel_data,
            "message": "Excel 提取完成，Word 请由 Dify 处理"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取失败：{str(e)}")


@router.post("/annotate")
async def annotate_reports(
    excel_file: Optional[UploadFile] = File(None, description="评估报表 Excel"),
    report_file: Optional[UploadFile] = File(None, description="评估报告 Word"),
    explanation_file: Optional[UploadFile] = File(None, description="评估说明 Word"),
    audit_result: str = Form(..., description="LLM 审核结果 JSON")
):
    """
    根据审核结果添加批注（带严格校验）

    audit_result 格式:
    {
      "audit_conclusion": "通过/有条件通过/不通过",
      "score": 0-100,
      "annotations": {
        "excel": [
          {
            "location": "资产明细表!C3",
            "type": "cell_comment",
            "description": "问题描述",
            "severity": "高/中/低",
            "suggestion": "修改建议"
          }
        ],
        "report": [...],
        "explanation": [...]
      },
      "summary": {...}
    }
    """
    try:
        # 解析审核结果
        audit_data = json.loads(audit_result)

        # 校验文件和批注匹配
        files_provided = {
            "excel": excel_file is not None,
            "report": report_file is not None,
            "explanation": explanation_file is not None
        }
        validate_annotations(audit_data, files_provided)

        annotations = audit_data.get("annotations", {})
        result = {
            "success": True,
            "annotated_files": {},
            "summary": {}
        }

        # Excel 批注处理
        if excel_file and annotations.get("excel", []):
            excel_path = save_temp_file(excel_file, ".xlsx")
            output_filename = process_excel_annotations(excel_path, annotations["excel"])
            result["annotated_files"]["excel"] = f"/api/v1/report/download/{output_filename}"
            result["summary"]["excel_comments"] = len(annotations["excel"])
            result["summary"]["excel_highlights"] = len([
                i for i in annotations["excel"] if i.get("severity") == "高"
            ])

        # Word 报告批注处理
        report_warnings = []
        if report_file and annotations.get("report", []):
            report_path = save_temp_file(report_file, ".docx")
            output_filename, warnings = process_word_annotations(report_path, annotations["report"], "报告")
            result["annotated_files"]["report"] = f"/api/v1/report/download/{output_filename}"
            result["summary"]["report_annotations"] = len(annotations["report"])
            report_warnings = warnings
        elif report_file and not annotations.get("report", []):
            # 上传了报告但没有批注，跳过不生成
            logger.warning("上传了评估报告但没有批注，跳过不生成文件")
            result["skipped_files"] = result.get("skipped_files", [])
            result["skipped_files"].append({
                "file": "report",
                "reason": "annotations.report 为空"
            })

        # Word 说明批注处理
        explanation_warnings = []
        if explanation_file and annotations.get("explanation", []):
            explanation_path = save_temp_file(explanation_file, ".docx")
            output_filename, warnings = process_word_annotations(explanation_path, annotations["explanation"], "说明")
            result["annotated_files"]["explanation"] = f"/api/v1/report/download/{output_filename}"
            result["summary"]["explanation_annotations"] = len(annotations["explanation"])
            explanation_warnings = warnings
        elif explanation_file and not annotations.get("explanation", []):
            # 上传了说明但没有批注，跳过不生成
            logger.warning("上传了评估说明但没有批注，跳过不生成文件")
            result["skipped_files"] = result.get("skipped_files", [])
            result["skipped_files"].append({
                "file": "explanation",
                "reason": "annotations.explanation 为空"
            })

        # 添加匹配失败警告
        all_warnings = report_warnings + explanation_warnings
        if all_warnings:
            result["match_warnings"] = all_warnings
            result["warning_count"] = len(all_warnings)

        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="audit_result 格式错误，必须是有效的 JSON 字符串")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批注失败：{str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """下载带批注的文件"""
    from fastapi.responses import FileResponse

    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename
    )


@router.get("/rules")
async def get_rules():
    """获取审核规则"""
    return {
        "excel_rules": {
            "required_sheets": ["资产明细表", "负债明细表", "净资产表", "评估结果汇总表"],
            "calculation_checks": ["汇总=明细之和", "公式无错误"],
            "comment_checks": ["重要科目有备注说明"]
        },
        "annotation_rules": {
            "excel_location_format": "Sheet 名!单元格，如'资产明细表!C3'",
            "word_location_format": "章节名称，如'评估方法'、'特别事项说明'",
            "required_fields": ["location", "description", "suggestion", "severity"]
        }
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "dify-bridge-report-audit",
        "features": ["Excel 提取", "Excel 单元格批注", "Word 原生批注", "文件 - 批注匹配校验"],
        "validation": {
            "excel_required": "上传 Excel 时必须提供 annotations.excel",
            "report_required": "上传报告时必须提供 annotations.report",
            "explanation_required": "上传说明时必须提供 annotations.explanation"
        }
    }
