import json

def main(llm_output):
    try:
        info = json.loads(llm_output)
    except:
        info = {}

    query_parts = []

    if info.get("location"):
        query_parts.append(info["location"])
    if info.get("device_id"):
        query_parts.append(info["device_id"])
    if info.get("device_name"):
        query_parts.append(info["device_name"])
    if info.get("error_code"):
        query_parts.append(info["error_code"])
    if info.get("symptoms"):
        query_parts.append(info["symptoms"])

    enhanced_query = " ".join(query_parts)


    return {
        "enhanced_query" :enhanced_query,
        "extracted_data" : info,
    }
