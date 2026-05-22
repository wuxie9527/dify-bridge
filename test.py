def main(faq_result: list[dict], wx_result: list[dict], memory_result: str):
    for faq in faq_result:
        faq_content = faq['content']
    for wx in wx_result:
        wx_content = wx['content']
    memory_content = memory_result.get("")
    return {
        "result": faq_result
    }
