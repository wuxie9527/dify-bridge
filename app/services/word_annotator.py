# -*- coding: utf-8 -*-
"""
Word 评估报告批注写回
使用 python-docx>=1.2.0 原生 add_comment() 方法 - 兼容 WPS 和 Microsoft Office
"""
from docx import Document
from typing import List, Dict, Any, Tuple
import datetime
import logging
import os

logger = logging.getLogger(__name__)


class WordAnnotator:
    """Word 原生批注写回 - 使用 python-docx>=1.2.0 add_comment() 方法"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = Document(file_path)
        self.match_warnings = []

    def find_paragraph_by_keyword(self, keyword: str) -> Tuple[int, bool]:
        """根据关键词查找段落索引"""
        for i, para in enumerate(self.doc.paragraphs):
            if keyword in para.text:
                return i, True
        return -1, False

    def add_comment_to_paragraph(self, para_index: int, comment_text: str,
                                  author: str = "审核 AI", initials: str = "SHR"):
        """
        在指定段落添加原生批注

        使用 python-docx-2023 的 add_comment() 方法
        """
        if para_index < 0 or para_index >= len(self.doc.paragraphs):
            logger.warning(f"段落索引超出范围：{para_index}")
            return False

        para = self.doc.paragraphs[para_index]

        # 如果段落没有 runs，添加一个空白 run 作为批注锚点
        if not para.runs:
            para.add_run()

        # 使用文档对象的 add_comment 方法添加批注
        try:
            self.doc.add_comment(
                runs=para.runs,
                text=comment_text,
                author=author,
                initials=initials
            )
            logger.info(f"✅ 在段落{para_index}添加批注")
            return True
        except Exception as e:
            logger.error(f"添加批注失败：{e}")
            return False

    def annotate_document(self, annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理批注"""
        warnings = []

        for i, ann in enumerate(annotations):
            location = ann.get("location", "")
            description = ann.get("description", "")
            suggestion = ann.get("suggestion", "")

            para_index, found = self.find_paragraph_by_keyword(location)

            if found:
                comment_text = f"{description}\n\n建议：{suggestion}"
                self.add_comment_to_paragraph(para_index, comment_text, "审核 AI", "AI")
                logger.info(f"✅ 在'{location}'后添加批注")
            else:
                warning = {
                    "annotation_index": i,
                    "location": location,
                    "description": description,
                    "reason": f"在文档中未找到关键词 '{location}'"
                }
                warnings.append(warning)
                self.match_warnings.append(warning)
                logger.warning(f"❌ 未找到关键词 '{location}'")

        return warnings

    def get_match_warnings(self) -> List[Dict[str, Any]]:
        return self.match_warnings

    def save(self, output_path: str):
        """保存文档"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.doc.save(output_path)
        logger.info(f"保存文件到：{output_path}")

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
