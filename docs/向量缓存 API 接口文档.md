# 向量缓存 API 接口文档

## 📦 接口概览

设备诊断向量化缓存,支持 **"标量精确过滤 + 语义检索"** 的混合检索模式:
查询时先用 **设备 ID** 和 **错误码** 精确过滤,再对剩余记录按 **用户提问** 做向量语义检索。

提供三个核心接口:

| 接口 | 说明 | 典型调用时机 |
|------|------|---------|
| `/api/v1/dify/cache` | 写入缓存(提问自动向量化) | 诊断完成后,保存本次诊断记录 |
| `/api/v1/dify/cache/search` | 语义检索缓存 | 诊断开始前,查找历史相似案例 |
| `/api/v1/dify/cache/{key}` | 删除缓存记录 | 管理员清理错误数据 |

### 底层架构

| 组件 | 说明 |
|------|------|
| 向量存储 | 阿里云 Tair(TairVector),HNSW 索引 + L2 距离,1024 维 |
| 向量化服务 | 阿里云百炼 DashScope `text-embedding-v3`(OpenAI 兼容接口) |
| 检索策略 | 前置过滤(PreFilter):先按标量倒排索引精确过滤,再做 KNN 语义检索 |
| 去重策略 | 记录 key = md5(设备ID\|错误码\|提问),相同组合重复写入自动覆盖更新 |

---

## 🔌 1. 写入缓存接口

诊断完成后调用。将 **设备名称、设备 ID、错误码、用户提问、维修方案** 存入向量缓存,用户提问会先经 DashScope 向量化后存入 TairVector。

### 接口地址

```http
POST http://你的服务器 IP:8000/api/v1/dify/cache
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | String | 是 | 设备 ID |
| `device_name` | String | 否 | 设备名称 |
| `error_code` | String | 否 | 错误码 |
| `question` | String | 是 | 用户提问(将向量化后存入) |
| `solution` | String | 否 | 维修方案 |

### 请求示例

```bash
curl -X POST http://localhost:8000/api/v1/dify/cache \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "IEVC-3.0-001",
    "device_name": "1 号充电桩",
    "error_code": "E001",
    "question": "充电的时候经常突然断电,充不进去",
    "solution": "检查充电模块保险丝,更换熔断的保险丝"
  }'
```

### 响应格式

```json
{
  "status": "success",
  "key": "a5bb8e3ed6b6aa7ac2b635d9c70b83d6",
  "is_update": false
}
```

### 响应字段说明

| 字段 | 说明 |
|------|------|
| `status` | 固定为 `success` |
| `key` | 记录唯一标识(md5),**删除时需使用此值** |
| `is_update` | `true`=已存在相同记录,本次为覆盖更新;`false`=新建 |

### 覆盖更新规则

同一 **设备 ID + 错误码 + 用户提问** 组合生成相同的 key,重复写入时自动覆盖旧记录(包括设备名称和维修方案的更新)。

---

## 🔌 2. 语义检索接口

诊断开始前调用。先用设备 ID / 错误码**精确过滤**缩小范围,再对剩余记录按用户提问做**语义检索**,返回按相似度降序的历史维修方案。

### 接口地址

```http
POST http://你的服务器 IP:8000/api/v1/dify/cache/search
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | String | 是 | 用户提问(语义检索的查询文本) |
| `device_id` | String | 否 | 设备 ID 精确过滤(空字符串等价于不过滤) |
| `error_code` | String | 否 | 错误码精确过滤(空字符串等价于不过滤) |
| `top_k` | Integer | 否 | 返回数量,默认 `5`,范围 1-20 |
| `max_distance` | Float | 否 | 距离阈值,**默认 `1.0`**(约等于相似度 0.5),超过阈值的不相关结果自动丢弃。换算: `similarity = 1 - distance²/2`,如 `0.8`≈相似度 0.8、`1.0`≈相似度 0.5;传 `2.0` 可近似关闭阈值 |

> **为什么需要阈值**:KNN 检索只返回"最接近的 top_k 条",不判断"是否足够相似"。当库中数据很少时,即使完全不相关的内容也会被返回(相似度可能只有 0.3~0.4),因此服务端默认用 `max_distance=1.0` 过滤弱相关结果。

### 检索逻辑

```
输入 query ──► DashScope 向量化 ──► ┌─ 第 1 步:按 device_id / error_code 精确过滤(前置)
                                    └─ 第 2 步:剩余记录做 KNN 向量语义检索
                                                    ↓
                                          按 similarity 降序返回
```

- `device_id` 和 `error_code` 均为可选,至少提供一个过滤条件可显著提升检索精度
- 不提供过滤条件时对全库做语义检索

### 请求示例

```bash
# 设备 + 错误码双精确过滤,再语义检索(推荐)
curl -X POST http://localhost:8000/api/v1/dify/cache/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "充电中老是自动停下来,断断续续的",
    "device_id": "IEVC-3.0-001",
    "error_code": "E001",
    "top_k": 5
  }'

# 调严阈值:只返回相似度 ≥ 0.8(distance ≤ 0.632)的结果
curl -X POST http://localhost:8000/api/v1/dify/cache/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "充不满电",
    "device_id": "IEVC-3.0-001",
    "max_distance": 0.632
  }'
```

### 响应格式

```json
{
  "results": [
    {
      "key": "a5bb8e3ed6b6aa7ac2b635d9c70b83d6",
      "device_id": "IEVC-3.0-001",
      "device_name": "1 号充电桩",
      "error_code": "E001",
      "question": "充电的时候经常突然断电,充不进去",
      "solution": "检查充电模块保险丝,更换熔断的保险丝",
      "created_at": 1792130573,
      "distance": 0.304329,
      "similarity": 0.953692
    }
  ],
  "total": 1
}
```

### 响应字段说明

| 字段 | 说明 |
|------|------|
| `results` | 检索结果列表,按 `similarity` 降序排列 |
| `total` | 结果数量 |
| `results[].key` | 记录唯一标识(md5) |
| `results[].question` | 历史用户提问 |
| `results[].solution` | 历史维修方案 |
| `results[].created_at` | 写入时间(Unix 时间戳,秒) |
| `results[].distance` | 向量距离,**越小越相似**(0=完全相同) |
| `results[].similarity` | 语义相似度,**越大越相似**(0~1,实测同义不同措辞约 0.9+) |

### 语义效果实测参考

| 存储的提问 | 检索措辞(无共同关键词) | similarity |
|------------|----------------------|-----------|
| 充电的时候经常突然断电,充不进去 | 充电中老是自动停下来,断断续续的 | 0.954 |
| 屏幕黑屏不显示任何内容 | 显示器不亮 | 0.904 |
| 充电枪拔不下来,卡住了 | 充电中老是自动停下来(弱相关) | 0.861 |

---

## 🔌 3. 删除缓存记录接口

按写入时返回的 `key`(md5)删除指定缓存记录。

### 接口地址

```http
DELETE http://你的服务器 IP:8000/api/v1/dify/cache/{key}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key` | String | 是 | 记录唯一标识(写入接口返回的 md5) |

### 请求示例

```bash
curl -X DELETE http://localhost:8000/api/v1/dify/cache/a5bb8e3ed6b6aa7ac2b635d9c70b83d6
```

### 响应格式

```json
{
  "status": "success",
  "key": "a5bb8e3ed6b6aa7ac2b635d9c70b83d6"
}
```

---

## ⚠️ 错误码说明

| 状态码 | 场景 | 处理建议 |
|--------|------|---------|
| `200` | 成功 | - |
| `404` | 删除时记录不存在 | 确认 key 是否正确 |
| `422` | 参数校验失败 | 检查必填字段、类型和取值范围 |
| `503` | 向量化服务不可用 | 检查 `.env` 中 `DASHSCOPE_API_KEY` 是否配置、百炼服务是否可用 |
| `503` | 向量存储连接失败 | 检查 `.env` 中 `TAIR_HOST`/`TAIR_PASSWORD`、Tair 白名单是否放行服务出口 IP |
| `500` | 其他内部错误 | 查看服务日志 `logs/app.log` |

---

## 🤖 Dify 集成:诊断缓存工作流

推荐在 Dify Chatflow 中按以下模式集成,实现"命中缓存直接返回,未命中走 LLM 再写入":

```
开始节点 (device_id / error_code / 用户提问)
    ↓
HTTP 节点 - POST /api/v1/dify/cache/search   (语义检索历史案例)
    ↓
条件分支节点
    ├─ 命中(similarity ≥ 0.9)──► 直接回复历史维修方案
    └─ 未命中 ──► LLM 节点诊断 ──► HTTP 节点 - POST /api/v1/dify/cache (写入缓存)
                                    ↓
                                  回复用户
```

### HTTP 节点配置:检索缓存

```
URL: http://172.17.0.1:8000/api/v1/dify/cache/search
Method: POST
Content-Type: application/json

Body:
{
  "query": "{{#sys.query#}}",
  "device_id": "{{#start.device_id#}}",
  "error_code": "{{#start.error_code#}}",
  "top_k": 3
}
```

### Code 节点:判断是否命中

```python
def main(api_response: dict) -> dict:
    """从检索响应中提取最优结果,判断是否命中"""
    import json

    body = api_response.get('body', '{}')
    data = json.loads(body)

    results = data.get('results', [])
    if results and results[0].get('similarity', 0) >= 0.9:
        best = results[0]
        return {
            "hit": True,
            "solution": best.get('solution', ''),
            "question": best.get('question', ''),
            "similarity": best.get('similarity', 0)
        }
    return {"hit": False, "solution": "", "question": "", "similarity": 0}
```

### HTTP 节点配置:写入缓存(LLM 诊断完成后)

```
URL: http://172.17.0.1:8000/api/v1/dify/cache
Method: POST
Content-Type: application/json

Body:
{
  "device_id": "{{#start.device_id#}}",
  "device_name": "{{#start.device_name#}}",
  "error_code": "{{#start.error_code#}}",
  "question": "{{#sys.query#}}",
  "solution": "{{#llm.solution#}}"
}
```

---

## ⚠️ 注意事项

1. **环境变量**:使用本模块前需在 `.env` 中配置 `TAIR_HOST`、`TAIR_PASSWORD`、`DASHSCOPE_API_KEY`(百炼 API-KEY 与 OCR 的 AccessKey 不同,需在 https://bailian.console.aliyun.com/ 单独开通获取)
2. **服务启动**:应用启动时自动创建向量索引 `diagnosis_cache`(HNSW,1024 维)并检查配置,未配置时相关接口返回 503,不影响其他功能
3. **维度绑定**:embedding 维度(`EMBEDDING_DIMENSION`)与索引维度强绑定,更换向量模型或维度后需删除索引 `diagnosis_cache` 重建(重启服务自动重建)
4. **相似度阈值**:服务端默认 `max_distance=1.0`(相似度≈0.5),不相关结果自动过滤;Dify 中可再按 `similarity ≥ 0.9` 判定强命中,避免弱相关结果误导用户
5. **网络要求**:生产环境建议 Tair 使用内网地址(服务与实例同 VPC);本地调试用公网地址时,需将出口 IP 加入 Tair 白名单
6. **计费**:每次写入/检索各调用一次 DashScope embedding(text-embedding-v3 定价低廉,但高频调用需留意)

---

## 📝 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-10-16 | 1.0 | 初始版本:写入、语义检索(前置过滤)、删除三个接口 |
