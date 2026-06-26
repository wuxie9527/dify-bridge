# -*- coding: utf-8 -*-
"""
Excel 评估报表提取器
只负责提取数据，不做审核判断
"""
import openpyxl
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExcelExtractor:
    """Excel 数据提取器 - 只提取，不判断"""

    def __init__(self, file_path: str):
        """
        初始化提取器

        Args:
            file_path: Excel 文件路径
        """
        self.file_path = file_path
        # data_only=False 保留公式，keep_vba=True 保留宏
        self.wb = openpyxl.load_workbook(file_path, data_only=False, keep_vba=True)

    def extract_all(self) -> Dict[str, Any]:
        """
        提取所有数据为结构化格式

        Returns:
            结构化数据字典
        """
        result = {
            "file_info": {
                "path": self.file_path,
                "sheet_names": self.wb.sheetnames,
                "extract_time": datetime.now().isoformat()
            },
            "sheets": {},
            "formulas": {},
            "comments": {},
            "simple_checks": []
        }

        for sheet_name in self.wb.sheetnames:
            logger.info(f"提取 Sheet: {sheet_name}")
            sheet = self.wb[sheet_name]

            # 提取表格数据
            result["sheets"][sheet_name] = self._extract_sheet_data(sheet)

            # 提取公式
            result["formulas"][sheet_name] = self._extract_formulas(sheet)

            # 提取单元格备注/注释
            result["comments"][sheet_name] = self._extract_comments(sheet)

        # 执行简单勾稽检查（只记录，不判断）
        result["simple_checks"] = self._run_simple_checks()

        logger.info(f"提取完成：{len(result['sheets'])} 个 Sheet")
        return result

    def _extract_sheet_data(self, sheet) -> List[List[Any]]:
        """提取 Sheet 数据为二维数组"""
        data = []
        for row in sheet.iter_rows(values_only=True):
            # 将元组转换为列表，处理 None 值
            row_data = [None if v is None else v for v in row]
            if any(v is not None for v in row_data):  # 跳过全空行
                data.append(row_data)
        return data

    def _extract_formulas(self, sheet) -> Dict[str, Dict[str, Any]]:
        """提取单元格公式"""
        formulas = {}
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                    formulas[cell.coordinate] = {
                        "formula": cell.value,
                        "display_value": cell.value,  # 不计算，保留原样供 LLM 分析
                        "row": cell.row,
                        "column": cell.column_letter
                    }
        return formulas

    def _extract_comments(self, sheet) -> Dict[str, str]:
        """提取单元格备注/注释"""
        comments = {}
        for row in sheet.iter_rows():
            for cell in row:
                if cell.comment:
                    comments[cell.coordinate] = {
                        "text": cell.comment.text,
                        "author": cell.comment.author if hasattr(cell.comment, 'author') else "Unknown",
                        "row": cell.row,
                        "column": cell.column_letter
                    }
        return comments

    def _run_simple_checks(self) -> List[Dict[str, Any]]:
        """
        执行简单的勾稽关系检查
        只记录计算结果，不判断对错
        """
        checks = []

        # 示例：检查是否有公式错误
        for sheet_name in self.wb.sheetnames:
            sheet = self.wb[sheet_name]
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value in ['#REF!', '#VALUE!', '#DIV/0!', '#N/A']:
                        checks.append({
                            "type": "formula_error",
                            "location": f"{sheet_name}!{cell.coordinate}",
                            "error_type": cell.value,
                            "message": f"单元格存在公式错误：{cell.value}"
                        })

        # 示例：检查汇总行是否存在
        for sheet_name in self.wb.sheetnames:
            sheet = self.wb[sheet_name]
            last_row = sheet.max_row
            if last_row > 1:
                last_cell = sheet[f"A{last_row}"].value
                if last_cell and "合计" in str(last_cell) or "总计" in str(last_cell):
                    checks.append({
                        "type": "summary_row_found",
                        "location": f"{sheet_name}!A{last_row}",
                        "message": f"发现汇总行：{last_cell}"
                    })

        return checks

    def get_sheet_as_dataframe(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        将指定 Sheet 转换为 DataFrame（便于数据分析）

        Args:
            sheet_name: Sheet 名称

        Returns:
            pandas DataFrame 或 None
        """
        if sheet_name not in self.wb.sheetnames:
            return None

        # 读取为 DataFrame
        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        return df

    def extract_range(self, sheet_name: str, range_str: str) -> List[List[Any]]:
        """
        提取指定单元格范围的数据

        Args:
            sheet_name: Sheet 名称
            range_str: 范围字符串，如 "A1:C10"

        Returns:
            二维数组
        """
        if sheet_name not in self.wb.sheetnames:
            return []

        sheet = self.wb[sheet_name]
        data = []
        for row in sheet[range_str]:
            row_data = [cell.value for cell in row]
            data.append(row_data)
        return data

    def close(self):
        """关闭工作簿，释放资源"""
        if self.wb:
            self.wb.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 工具函数
def extract_excel(file_path: str) -> Dict[str, Any]:
    """
    便捷函数：提取 Excel 文件

    Args:
        file_path: Excel 文件路径

    Returns:
        结构化数据
    """
    with ExcelExtractor(file_path) as extractor:
        return extractor.extract_all()


# 测试代码
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python excel_extractor.py <excel_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = extract_excel(file_path)

    print(f"文件: {result['file_info']['path']}")
    print(f"Sheet 列表: {result['file_info']['sheet_names']}")
    print(f"\n示例数据 (第一个 Sheet 前 5 行):")

    first_sheet = result['file_info']['sheet_names'][0]
    data = result['sheets'].get(first_sheet, [])
    for i, row in enumerate(data[:5], 1):
        print(f"  行{i}: {row}")

    print(f"\n公式数量: {sum(len(f) for f in result['formulas'].values())}")
    print(f"备注数量: {sum(len(c) for c in result['comments'].values())}")
    print(f"简单检查项: {len(result['simple_checks'])}")
