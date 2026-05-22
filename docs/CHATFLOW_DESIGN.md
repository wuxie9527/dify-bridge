# 换电运维助手 - 企业级详细设计文档

> 版本：v1.0  
> 更新日期：2026-05-22  
> 状态：待实现

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Dify Chatflow                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  意图识别    │  │  信息抽取    │  │  并行检索    │  │  诊断生成           │ │
│  │  (LLM)      │  │  (LLM)      │  │  (HTTP+RAG) │  │  (LLM)            │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                │                    │             │
│         ▼                ▼                ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        会话变量管理层                                    ││
│  │  device_id, error_code, symptoms, round_count, ticket_created          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              外部服务层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  长期记忆服务  │  │  Dify 知识库  │  │  工单系统     │  │  日志/监控       │ │
│  │  (dify-bridge)│  │  (Weaviate)  │  │  (待定)      │  │  (ELK/Prometheus)│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、会话变量详细设计

### 2.1 变量分类

| 类别 | 变量名 | 类型 | 生命周期 | 说明 |
|------|--------|------|---------|------|
| **核心变量** | `device_id` | String | 对话持续 | 设备编号 |
| | `device_name` | String | 对话持续 | 设备名称 |
| | `error_code` | String | 对话持续 | 故障码 |
| | `symptoms` | String | 对话持续 | 症状描述 |
| **流程控制** | `round_count` | Number | 对话持续 | 追问轮次（0-3） |
| | `ticket_created` | Boolean | 对话持续 | 是否已创建工单 |
| | `is_resolved` | Boolean | 单轮 | 问题是否解决 |
| **临时上下文** | `search_query` | String | 单轮 | 检索关键词 |
| | `memory_results` | Array | 单轮 | 长期记忆检索结果 |
| | `kb_results` | Array | 单轮 | 知识库检索结果 |
| | `diagnosis_output` | String | 单轮 | LLM 诊断输出 |

### 2.2 变量初始化（Chatflow 开始）

**节点类型**: 代码执行

**代码**:
```python
def main(conversation_id: str) -> dict:
    """
    新对话开始时重置变量
    conversation_id: Dify 会话 ID
    """
    import json
    from datetime import datetime
    
    return {
        "round_count": 0,
        "ticket_created": False,
        "is_resolved": False,
        "search_query": "",
        "memory_results": [],
        "kb_results": [],
        "diagnosis_output": "",
        "conversation_started_at": datetime.now().isoformat()
    }
```

---

## 三、节点详细配置

### 节点 1: 意图识别 + 信息抽取

**节点类型**: LLM

**模型配置**:
- 模型：qwen2.5:1.5b 或更高级模型
- Temperature: 0.1（保证输出稳定）
- Max Tokens: 500

**System Prompt**:
```markdown
你是换电运维助手的意图识别和信息抽取专家。

【任务】
1. 判断用户意图类型
2. 抽取关键实体信息
3. 生成检索关键词

【意图类型】
- fault_report: 故障上报（设备出现问题）
- status_query: 状态查询（询问设备状态）
- maintenance: 维护咨询（保养、巡检相关）
- manual_transfer: 转人工（要求人工客服）
- complaint: 投诉建议
- other: 其他

【抽取字段】
- device_id: 设备编号（格式：XXX-XX-XXX 或自定义编号）
- device_name: 设备名称（如 1 号充电桩、2 号电池包）
- error_code: 故障码（格式：E+ 数字，如 E001）
- symptoms: 症状描述（用户描述的问题现象）
- urgency_keywords: 紧急程度关键词（如"马上"、"紧急"、"快点"）

【查询改写】
将用户口语化描述改写为适合检索的专业关键词：
- 同义词扩展（断电→供电中断、停电、掉电）
- 添加相关故障码（如提到断电，添加 E001）
- 提取核心名词和动词

【输出格式】
只输出 JSON，不要其他内容：
{
  "intent": "fault_report|status_query|maintenance|manual_transfer|complaint|other",
  "entities": {
    "device_id": "提取的设备编号，没有则为 null",
    "device_name": "提取的设备名称，没有则为 null",
    "error_code": "提取的故障码，没有则为 null",
    "symptoms": "症状描述原文",
    "urgency_keywords": ["紧急词汇列表"]
  },
  "search_query": "改写后的检索关键词，用空格分隔",
  "has_device_info": true/false,
  "confidence": 0.0-1.0
}

【示例 1】
用户输入："IEVC-3.0-001 充电桩充电时突然断电，显示 E001，很着急！"
输出：
{
  "intent": "fault_report",
  "entities": {
    "device_id": "IEVC-3.0-001",
    "device_name": "充电桩",
    "error_code": "E001",
    "symptoms": "充电时突然断电",
    "urgency_keywords": ["很着急"]
  },
  "search_query": "充电断电 E001 供电中断 停电",
  "has_device_info": true,
  "confidence": 0.95
}

【示例 2】
用户输入："转人工客服"
输出：
{
  "intent": "manual_transfer",
  "entities": {
    "device_id": null,
    "device_name": null,
    "error_code": null,
    "symptoms": null,
    "urgency_keywords": []
  },
  "search_query": "",
  "has_device_info": false,
  "confidence": 1.0
}
```

**输出变量**: `#intent_extraction.text`

**后置处理**（代码节点）:
```python
def main(llm_output: str) -> dict:
    """解析 LLM 输出，设置会话变量"""
    import json
    
    try:
        data = json.loads(llm_output)
    except:
        # 解析失败，返回默认值
        return {
            "intent": "other",
            "entities": {},
            "search_query": "",
            "has_device_info": False,
            "parse_error": True
        }
    
    return {
        "intent": data.get("intent", "other"),
        "device_id": data.get("entities", {}).get("device_id"),
        "device_name": data.get("entities", {}).get("device_name"),
        "error_code": data.get("entities", {}).get("error_code"),
        "symptoms": data.get("entities", {}).get("symptoms"),
        "search_query": data.get("search_query", ""),
        "has_device_info": data.get("has_device_info", False),
        "confidence": data.get("confidence", 0),
        "parse_error": False
    }
```

---

### 节点 2: 意图分支处理

**节点类型**: 条件分支

**条件配置**:

| 分支 | 条件 | 下一节点 |
|------|------|---------|
| 转人工 | `#intent_extraction.intent` == "manual_transfer" | 节点 2.1: 转人工处理 |
| 投诉 | `#intent_extraction.intent` == "complaint" | 节点 2.2: 投诉处理 |
| 故障上报 | `#intent_extraction.intent` == "fault_report" | 节点 3: 并行检索 |
| 其他 | 默认 | 节点 3: 并行检索 |

---

### 节点 2.1: 转人工处理

**节点类型**: 直接回复

**回复内容**:
```
好的，已为您转接人工客服。

当前值班状态：{{#is_business_hours#}}
{{#IF is_business_hours == true}}
客服人员将在 1-2 分钟内响应您的问题。
{{#ELSE}}
当前是非工作时间（工作时间：工作日 9:00-18:00），值班人员将在下一个工作时间联系您。

如需紧急处理，请拨打值班电话：400-XXX-XXXX
{{#ENDIF}}

【已为您记录】
会话 ID: {{#conversation.id#}}
时间：{{#sys.time#}}
```

**并行操作**（HTTP 请求）:
```yaml
URL: http://<工单系统>/api/tickets
Method: POST
Body:
  type: manual_transfer
  conversation_id: {{#conversation.id#}}
  user_input: {{#sys.query#}}
  priority: high
  status: pending
```

---

### 节点 3: 长期记忆检索（并行）

**节点类型**: HTTP 请求

**超时设置**: 2 秒

**配置**:
```yaml
URL: http://172.17.0.1:8000/api/v1/dify/memory/search
Method: POST
Headers:
  Content-Type: application/json
  X-Request-Timeout: "2000"
Body:
  query: {{#intent_extraction.search_query#}}
  device_id: {{#conversationVariables.device_id#}}
  error_code: {{#conversationVariables.error_code#}}
  top_k: 5
```

**错误处理**:
```python
def main(response: dict, error: str) -> dict:
    """处理检索结果和错误"""
    if error:
        # API 调用失败，返回空结果（降级）
        return {
            "success": False,
            "cases": [],
            "total": 0,
            "error": error,
            "fallback": True
        }
    
    return {
        "success": True,
        "cases": response.body.get("cases", []),
        "total": response.body.get("total", 0),
        "error": None,
        "fallback": False
    }
```

**输出变量**: `#memory_search.*`

---

### 节点 4: 知识库检索（并行）

**节点类型**: 知识库检索

**配置**:
```yaml
知识库：
  - 维修方案（优先级：高）
  - 故障码表（优先级：高）
  - 维修手册（优先级：中）
查询变量：{{#intent_extraction.search_query#}}
最大召回：5
最低相似度：0.6
```

**错误处理**（代码节点）:
```python
def main(kb_result: dict) -> dict:
    """处理知识库检索结果"""
    chunks = kb_result.get("chunks", [])
    
    # 过滤低质量结果
    high_quality = [c for c in chunks if c.get("score", 0) >= 0.6]
    
    return {
        "success": True,
        "chunks": high_quality,
        "total": len(high_quality),
        "fallback": len(high_quality) == 0
    }
```

**输出变量**: `#kb_search.*`

---

### 节点 5: 结果合并与排序

**节点类型**: 代码执行

**代码**:
```python
def main(memory_result: dict, kb_result: dict, entities: dict) -> dict:
    """
    合并长期记忆和知识库检索结果
    去重、排序、标注来源
    """
    import json
    from datetime import datetime
    
    all_docs = []
    seen_contents = set()
    
    # 1. 先添加长期记忆（优先级高，因为是实际案例）
    for case in memory_result.get("cases", []):
        content = f"{case.get('symptoms')} - {case.get('solution')}"
        if content not in seen_contents:
            all_docs.append({
                "source": "历史维修记录",
                "source_type": "memory",
                "content": content,
                "error_code": case.get("error_code"),
                "hit_count": case.get("hit_count", 0),
                "created_at": case.get("created_at"),
                "score": 1.0 + case.get("hit_count", 0) * 0.1  # 命中次数加分
            })
            seen_contents.add(content)
    
    # 2. 添加知识库结果
    for chunk in kb_result.get("chunks", []):
        content = chunk.get("text", "")
        if content not in seen_contents:
            metadata = chunk.get("metadata", {})
            all_docs.append({
                "source": metadata.get("source", "知识库"),
                "source_type": "knowledge_base",
                "content": content,
                "score": chunk.get("score", 0.5)
            })
            seen_contents.add(content)
    
    # 3. 按分数排序
    all_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # 4. 更新会话变量（如果检索到新的 error_code）
    updated_error_code = entities.get("error_code")
    if not updated_error_code and all_docs:
        for doc in all_docs:
            if doc.get("error_code"):
                updated_error_code = doc["error_code"]
                break
    
    return {
        "merged_docs": all_docs,
        "total_count": len(all_docs),
        "has_data": len(all_docs) > 0,
        "sources": list(set(d.get("source") for d in all_docs)),
        "updated_error_code": updated_error_code
    }
```

**输出变量**: 
- `#merge_results.merged_docs`
- `#merge_results.total_count`
- `#merge_results.has_data`
- `#merge_results.sources`

---

### 节点 6: 会话变量更新

**节点类型**: 变量赋值

**赋值操作**:
```yaml
# 更新核心变量（如果检索到）
conversationVariables.device_id = {{#intent_extraction.device_id#}} OR {{#conversationVariables.device_id#}}
conversationVariables.device_name = {{#intent_extraction.device_name#}} OR {{#conversationVariables.device_name#}}
conversationVariables.error_code = {{#merge_results.updated_error_code#}} OR {{#conversationVariables.error_code#}}
conversationVariables.symptoms = {{#intent_extraction.symptoms#}} OR {{#conversationVariables.symptoms#}}

# 更新轮次计数
conversationVariables.round_count = {{#conversationVariables.round_count#}} + 1

# 存储临时上下文
conversationVariables.current_docs = {{#merge_results.merged_docs#}}
conversationVariables.current_sources = {{#merge_results.sources#}}
```

---

### 节点 7: LLM 诊断生成

**节点类型**: LLM

**模型配置**:
- 模型：qwen2.5:3b（推荐）或 qwen2.5:1.5b
- Temperature: 0.3
- Max Tokens: 1500

**System Prompt**:
```markdown
你是换电运维助手，专业的设备故障诊断专家。

【当前会话状态】
设备 ID: {{#conversationVariables.device_id#}}
设备名称：{{#conversationVariables.device_name#}}
故障码：{{#conversationVariables.error_code#}}
症状：{{#conversationVariables.symptoms#}}
追问轮次：{{#conversationVariables.round_count#}}/3

【检索到的文档】
{{#merge_results.merged_docs#}}

【文档来源】
{{#merge_results.sources#}}

【输出规则】

## 情况 1: 有文档数据 (has_data == true)

输出格式：
```
## 诊断分析
[根据文档内容分析故障原因，引用来源]

## 解决方案
[分步骤列出解决方案，每条标注来源]

## 注意事项
[安全提示、警告事项]

---
请问以上方案是否解决了您的问题？
👍 已解决  |  👎 未解决
```

## 情况 2: 无文档数据 (has_data == false)

输出格式：
```
抱歉，当前知识库中暂未找到该故障的处理方案。

为了进一步帮助您，已记录您的问题信息：
- 设备：{{#conversationVariables.device_id#}}
- 故障现象：{{#conversationVariables.symptoms#}}

{{#IF conversationVariables.round_count >= 3}}
由于问题较为复杂，已为您创建维修工单，技术人员将联系您处理。
{{#ELSE}}
为了更好地诊断，请补充以下信息：
1. 设备是否显示故障码？
2. 故障发生前有什么异常操作？
3. 之前是否出现过类似情况？
{{#ENDIF}}
```

## 情况 3: 置信度低 (confidence < 0.6)

输出格式：
```
根据您描述的问题，我找到一些可能相关的案例，但不完全匹配。

[列出最相似的 1-2 个案例]

建议：
1. 请先尝试上述方案
2. 如未解决，我将为您转接专业技术人员
```

【语气要求】
- 专业、准确
- 避免绝对化表述（"一定"、"肯定"）
- 涉及安全的内容要突出提示
- 不确定的内容要说明
```

**输出变量**: `#diagnosis.text`

---

### 节点 8: 用户反馈判断

**节点类型**: 条件分支

**判断逻辑**:

**条件 1 (已解决)**:
```
用户输入包含以下任一关键词：
- "好了"、"解决了"、"可以了"、"谢谢"、"有用"、"👍"
- "是的"、"对的"（针对"是否解决"的肯定回答）
```

**条件 2 (未解决)**:
```
用户输入包含以下任一关键词：
- "没有"、"还是"、"不行"、"没用"、"不对"、"👎"
- "但是"、"可是"（转折词，表示问题仍在）
```

**条件 3 (继续追问)**:
```
以上都不是 → 默认未解决，继续诊断流程
```

**条件 4 (转人工)**:
```
用户输入包含：
- "转人工"、"找客服"、"投诉"、"叫人来"
```

---

### 节点 9: 保存长期记忆

**节点类型**: HTTP 请求

**前置条件**: 
- `#feedback.is_resolved` == true
- `#merge_results.has_data` == true
- LLM 置信度 > 0.7（可选）

**配置**:
```yaml
URL: http://172.17.0.1:8000/api/v1/dify/memory
Method: POST
Headers:
  Content-Type: application/json
Body:
  device_id: {{#conversationVariables.device_id#}}
  device_name: {{#conversationVariables.device_name#}}
  error_code: {{#conversationVariables.error_code#}}
  symptoms: {{#conversationVariables.symptoms#}}
  solution: {{#diagnosis.text#}}
  primary_cause: {{#conversationVariables.error_code#}}
  conversation_id: {{#conversation.id#}}
  metadata:
    sources: {{#merge_results.sources#}}
    round_count: {{#conversationVariables.round_count#}}
    user_feedback: "resolved"
```

**后置处理**（日志记录）:
```python
def main(response: dict, conversation_id: str) -> dict:
    """记录记忆保存日志"""
    is_new = response.body.get("is_new", False)
    
    # 发送到日志系统
    log_event = {
        "event": "memory_saved",
        "conversation_id": conversation_id,
        "is_new_record": is_new,
        "error_code": response.body.get("error_code"),
        "timestamp": datetime.now().isoformat()
    }
    
    # HTTP POST 到日志服务
    # requests.post("http://log-service/api/events", json=log_event)
    
    return {
        "saved": True,
        "is_new": is_new,
        "memory_id": response.body.get("id")
    }
```

---

### 节点 10: 工单创建判断

**节点类型**: 条件分支

**触发条件**:
- `#conversationVariables.round_count` >= 3
- OR 用户主动要求创建工单

**检查必要信息**:
```
条件 1 (信息完整):
  conversationVariables.device_id != null AND
  conversationVariables.error_code != null AND
  conversationVariables.symptoms != null

条件 2 (信息缺失):
  以上任一为空
```

---

### 节点 11: 工单创建

**节点类型**: HTTP 请求

**前置检查**（代码节点）:
```python
def main(ticket_created: bool, conversation_id: str) -> dict:
    """幂等性检查"""
    if ticket_created:
        return {
            "skip": True,
            "message": "工单已创建，请勿重复提交"
        }
    
    return {
        "skip": False,
        "message": "可以创建工单"
    }
```

**工单 API 配置**:
```yaml
URL: http://<工单系统>/api/tickets
Method: POST
Headers:
  Content-Type: application/json
  Authorization: Bearer {{#secrets.ticket_api_token#}}
Body:
  type: fault_report
  priority: {{#calculate_priority#}}
  source: dify_chatbot
  conversation_id: {{#conversation.id#}}
  device_id: {{#conversationVariables.device_id#}}
  device_name: {{#conversationVariables.device_name#}}
  error_code: {{#conversationVariables.error_code#}}
  description: {{#conversationVariables.symptoms#}}
  diagnosis_log: {{#diagnosis.text#}}
  conversation_history: {{#conversation.history#}}
  submitted_at: {{#sys.time#}}
```

**成功后处理**:
```yaml
# 设置变量
conversationVariables.ticket_created = true

# 回复用户
"工单已创建（工单号：{{#ticket_create.response.ticket_id#}}）"
```

---

### 节点 12: 澄清追问

**节点类型**: LLM 或直接回复

**System Prompt** (LLM 模式):
```markdown
你是换电运维助手的澄清专家。

【当前缺失信息】
{{#missing_fields#}}

【任务】
用友好的语气向用户询问缺失的信息。

【示例】
- 缺失 device_id: "请问您是哪台设备出现了问题？请提供设备编号（如 IEVC-3.0-001）"
- 缺失 error_code: "设备屏幕上显示什么故障码或错误代码？"
- 缺失 symptoms: "请详细描述一下设备的异常现象，比如有什么声音、显示、气味等"
```

---

## 四、异常处理设计

### 4.1 超时处理

| 节点 | 超时时间 | 降级策略 |
|------|---------|---------|
| 长期记忆检索 | 2 秒 | 继续知识库检索 |
| 知识库检索 | 3 秒 | 使用缓存结果或返回空 |
| 工单创建 | 5 秒 | 记录待重试队列 |
| LLM 生成 | 10 秒 | 返回默认回复 |

### 4.2 错误码定义

| 错误码 | 说明 | 用户可见提示 |
|--------|------|-------------|
| MEMORY_TIMEOUT | 长期记忆服务超时 | "正在查询历史案例..." |
| KB_EMPTY | 知识库无匹配 | "暂未找到相关文档" |
| LLM_PARSE_ERROR | LLM 输出解析失败 | "正在处理您的问题..." |
| TICKET_CREATE_FAIL | 工单创建失败 | "稍后会有工作人员联系您" |

### 4.3 降级策略

```python
def fallback_handler(error_type: str) -> str:
    """降级回复模板"""
    
    fallbacks = {
        "MEMORY_TIMEOUT": "正在查询历史案例，请稍候...",
        "KB_EMPTY": "当前知识库暂未收录该问题的解决方案，已记录您的问题。",
        "ALL_FAILED": "抱歉，系统暂时无法处理您的问题。已为您转接人工客服。",
        "LLM_ERROR": "正在生成诊断建议，请稍候..."
    }
    
    return fallbacks.get(error_type, "请稍后重试")
```

---

## 五、监控与日志

### 5.1 关键事件日志

```python
# 事件定义
EVENTS = {
    "CONVERSATION_STARTED": "对话开始",
    "INTENT_RECOGNIZED": "意图识别完成",
    "MEMORY_SEARCHED": "长期记忆检索完成",
    "KB_SEARCHED": "知识库检索完成",
    "SOLUTION_PROVIDED": "解决方案已提供",
    "FEEDBACK_COLLECTED": "用户反馈已收集",
    "MEMORY_SAVED": "长期记忆已保存",
    "TICKET_CREATED": "工单已创建",
    "MANUAL_TRANSFERRED": "已转人工"
}

# 日志格式
log_entry = {
    "event": "事件名",
    "conversation_id": "会话 ID",
    "timestamp": "ISO8601 时间",
    "latency_ms": 123,
    "metadata": {
        "intent": "fault_report",
        "round_count": 2,
        "has_device_info": True,
        "memory_results_count": 3,
        "kb_results_count": 5,
        "user_feedback": "resolved"
    }
}
```

### 5.2 核心指标

| 指标 | 计算方式 | 告警阈值 |
|------|---------|---------|
| 平均响应时间 | 总耗时 / 对话数 | > 5s |
| 问题解决率 | resolved / total | < 60% |
| 工单转化率 | tickets / total | > 30% |
| 用户满意度 | useful / (useful + useless) | < 70% |
| 长期记忆命中率 | memory_results > 0 / total | - |

---

## 六、安全与权限

### 6.1 设备权限校验

```python
def check_device_permission(user_id: str, device_id: str) -> bool:
    """校验用户是否有权访问该设备"""
    # 调用权限服务
    response = requests.get(
        f"http://auth-service/api/permissions",
        params={"user_id": user_id, "device_id": device_id}
    )
    return response.json().get("has_permission", False)
```

### 6.2 敏感信息脱敏

```python
def sanitize_output(text: str) -> str:
    """脱敏处理"""
    # 手机号
    text = re.sub(r'1[3-9]\d{9}', '1****\g<0>', text)
    # 身份证
    text = re.sub(r'\d{17}[\dXx]', '****************X', text)
    # 密码
    text = re.sub(r'密码 [：:]\S+', '密码：***', text)
    return text
```

---

## 七、部署配置

### 7.1 环境变量

```bash
# 长期记忆服务
MEMORY_SERVICE_URL=http://172.17.0.1:8000
MEMORY_API_TIMEOUT=2000

# 工单系统
TICKET_SERVICE_URL=http://ticket-system/api
TICKET_API_TOKEN=xxx

# 日志服务
LOG_SERVICE_URL=http://log-service/api
LOG_LEVEL=INFO

# 业务配置
BUSINESS_HOURS_START=9
BUSINESS_HOURS_END=18
MAX_ROUND_COUNT=3
ONCALL_PHONE=400-XXX-XXXX
```

### 7.2 限流配置

```yaml
# Nginx 限流
location /api/v1/dify/ {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
```

---

## 八、附录

### 8.1 API 接口清单

| 接口 | 地址 | 调用时机 |
|------|------|---------|
| 长期记忆 - 检索 | `POST /api/v1/dify/memory/search` | 并行检索阶段 |
| 长期记忆 - 保存 | `POST /api/v1/dify/memory` | 问题解决后 |
| 知识库检索 | Dify RAG 节点 | 并行检索阶段 |
| 工单创建 | `POST /api/tickets` | 三轮未解决时 |

### 8.2 流程图

```
用户输入
   │
   ▼
┌─────────────────┐
│ 1. 意图识别 + 抽取 │
└─────────────────┘
   │
   ▼
┌─────────────────┐
│ 2. 意图分支处理   │
└─────────────────┘
   │
   ├───────────────┬───────────────┐
   ▼               ▼               ▼
转人工处理       投诉处理       并行检索
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
           ┌─────────────────┐       ┌─────────────────┐
           │ 长期记忆检索     │       │ 知识库检索       │
           │ (HTTP, 2s 超时)  │       │ (RAG, 3s 超时)    │
           └─────────────────┘       └─────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │ 5. 结果合并与排序         │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ 6. 会话变量更新          │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ 7. LLM 诊断生成           │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ 8. 用户反馈判断          │
                    └─────────────────────────┘
                          │               │
              ┌───────────┴───────┐       │
              ▼                   ▼       ▼
         已解决               未解决    转人工
              │                   │
              ▼                   ▼
    ┌─────────────────┐   ┌─────────────────┐
    │ 9. 保存长期记忆  │   │ 检查 round_count │
    └─────────────────┘   └─────────────────┘
                                  │
                          ┌───────┴───────┐
                          │               │
                      < 3 轮           >= 3 轮
                          │               │
                          │               ▼
                          │     ┌─────────────────┐
                          │     │ 10. 工单创建判断  │
                          │     └─────────────────┘
                          │               │
                          │     ┌─────────┴─────────┐
                          │     ▼                   ▼
                          │  信息完整            信息缺失
                          │     │                   │
                          │     ▼                   ▼
                          │  创建工单          澄清追问
                          │     │                   │
                          │     └─────────┬─────────┘
                          │               │
                          └───────────────┘
                                  │
                                  ▼
                          回复用户
```

### 8.3 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-05-22 | 初始版本 | - |
