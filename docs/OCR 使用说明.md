# OCR 识别功能使用说明

## 1. 配置阿里云 AccessKey

### 1.1 获取 AccessKey

1. 登录 [阿里云 RAM 控制台](https://ram.console.aliyun.com/manage/ak)
2. 创建 AccessKey（建议使用子账号，不要使用主账号）
3. 保存 `AccessKey ID` 和 `AccessKey Secret`

### 1.2 配置文件

复制 `.env.example` 为 `.env` 并填写：

```bash
# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///data/battery.db

# 日志级别
LOG_LEVEL=INFO

# 阿里云 OCR 配置
ALIYUN_ACCESS_KEY_ID=LTAI5txxxxxxxxxx
ALIYUN_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
ALIYUN_OCR_REGION=cn-shanghai
```

## 2. 安装依赖

```bash
cd D:\users\a7e18db2a7e2165c\dify-bridge

# 激活虚拟环境（如果有）
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 3. 测试 OCR 功能

### 方式 1：运行测试脚本

```bash
python test_ocr.py
```

按提示选择测试模式：
- 通用文字识别
- 行驶证识别
- 驾驶证识别
- HTTP API 测试

### 方式 2：启动服务后通过 API 测试

```bash
# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问 http://localhost:8000/docs 查看 API 文档
```

## 4. API 接口说明

### 4.1 通用文字识别

```bash
POST http://localhost:8000/api/v1/ocr/recognize/general

{
    "image_url": "https://example.com/image.jpg"
}

# 或 base64
{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

### 4.2 行驶证识别

```bash
POST http://localhost:8000/api/v1/ocr/recognize/vehicle-license

{
    "image_url": "https://example.com/vehicle_license.jpg"
}
```

返回示例：
```json
{
    "success": true,
    "data": {
        "plate_number": "京 A12345",
        "vehicle_type": "小型轿车",
        "owner": "张三",
        "use_character": "非营运",
        "model": "宝马牌 BMW7201MM",
        "vin": "LBV3E3109HNS12345",
        "engine_number": "12345678",
        "register_date": "2018-03-15"
    }
}
```

### 4.3 驾驶证识别

```bash
POST http://localhost:8000/api/v1/ocr/recognize/driving_license

{
    "image_url": "https://example.com/driving_license.jpg"
}
```

### 4.4 统一识别接口（指定 mode）

```bash
POST http://localhost:8000/api/v1/ocr/recognize

{
    "image_url": "https://example.com/image.jpg",
    "mode": "general"  // general | vehicle_license | driving_license
}
```

## 5. 在 Dify 中使用

### 5.1 创建 Custom Tool

在 Dify 中创建一个 HTTP 请求类型的 Tool：

**Tool 配置**:
- **Name**: `ocr_recognize`
- **Method**: `POST`
- **URL**: `http://your-dify-bridge:8000/api/v1/ocr/recognize`
- **Headers**: `Content-Type: application/json`

**Request Body**:
```json
{
    "image_url": "{{image_url}}",
    "mode": "{{mode}}"
}
```

**Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "data": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "lines": {"type": "array"}
            }
        },
        "error": {"type": "string"}
    }
}
```

### 5.2 在 Workflow 中调用

```
[开始] → [用户输入图片 URL] → [OCR 识别 Tool] → [提取 VIN/车牌等信息] → [估值查询] → [返回结果]
```

## 6. 常见问题

### Q1: 提示"ClientException: SDK.InvalidRegionId"
**A**: 检查 `ALIYUN_OCR_REGION` 配置，确保是你开通 OCR 服务的区域

### Q2: 提示"Access Denied"
**A**: 检查 AccessKey 是否正确，确保 RAM 用户有 OCR 服务权限

### Q3: 识别失败返回"InvalidImageURL"
**A**: 图片 URL 必须是公网可访问的，不能用本地路径

### Q4: Base64 识别失败
**A**: Base64 字符串不能包含 `data:image/jpeg;base64,` 前缀，需要纯 Base64 编码

## 7. 计费说明

- 通用文字识别：¥0.005/次
- 行驶证识别：¥0.03/次
- 驾驶证识别：¥0.03/次

新用户有免费额度，详见 [阿里云 OCR 定价](https://help.aliyun.com/document_detail/122498.html)
