# RAGFlow 前置设置指南

## 📋 必须完成的前置步骤

系统启动前，**必须在RAGFlow中手动创建知识库**。否则文件上传会失败。

---

## 1️⃣ 启动RAGFlow服务

### Docker方式（推荐）
```bash
# 启动RAGFlow容器
docker-compose -f docker/docker-compose.ragflow.yml up -d

# 验证RAGFlow是否正常运行
docker ps | grep ragflow
```

### 直接运行（如已安装）
```bash
# 启动RAGFlow服务（具体命令取决于安装方式）
# 默认访问地址：http://localhost:9380
```

**验证服务是否启动：**
```bash
curl http://localhost:9380
# 返回 404 或页面说明服务正常
```

---

## 2️⃣ 在RAGFlow中创建知识库

### Step 1: 登录RAGFlow管理界面
```
访问：http://localhost:9380
（如果使用远程服务器，替换localhost为实际IP地址）
```

### Step 2: 创建知识库（Knowledge Base）

在RAGFlow Web界面中：
1. 点击 "知识库" 或 "Knowledge Base" 菜单
2. 点击 "新建知识库" 或 "Create"
3. 填写知识库信息：
   - **知识库名称**：`policy_demo_kb`
   - **描述**：`政策知识库 - 专项债/特许经营/数据资产`
   - 其他选项保持默认

### Step 3: 记录知识库信息

创建成功后，记下：
- 知识库ID（如有）
- 知识库名称：`policy_demo_kb`

---

## 3️⃣ 更新配置文件

### 复制模板文件
```bash
cp config/config.ini.template config/config.ini
```

### 编辑 config.ini
打开 `config/config.ini`，修改 `[RAGFLOW]` 部分：

```ini
[RAGFLOW]
# RAGFlow服务地址
host = localhost          # 改为实际的RAGFlow服务器地址
port = 9380              # RAGFlow端口（默认9380）

# RAGFlow API认证（如果需要）
api_key =                # 如果RAGFlow需要认证，填入API Key

# 知识库配置
kb_name = policy_demo_kb  # 必须与RAGFlow中创建的名称一致！
kb_description = 政策知识库 - 专项债/特许经营/数据资产
```

**⚠️ 重要：**
- `kb_name` 必须与RAGFlow中创建的知识库名称**完全一致**（包括大小写）
- 如果不一致，上传文件时会提示知识库不存在

---

## 4️⃣ 验证RAGFlow连接

运行诊断脚本验证配置是否正确：

```bash
python3 test_ragflow_upload.py
```

预期输出：
```
✅ 连接成功，状态码: 404
✅ RAGFlow健康检查: 正常
✅ 文档上传成功！文档ID: ...
```

---

## 5️⃣ 启动应用

```bash
streamlit run app.py
```

现在应该可以正常使用文档上传功能了！

---

## 🔧 故障排除

### 问题1：连接失败 - "RAGFlow服务不可用"

**原因：** RAGFlow服务未启动或地址配置错误

**解决方案：**
```bash
# 1. 检查RAGFlow是否运行
docker ps | grep ragflow

# 2. 验证服务连接
curl http://localhost:9380

# 3. 检查config.ini中的host/port是否正确
cat config/config.ini | grep -A 2 "^\[RAGFLOW\]"
```

### 问题2：上传失败 - "知识库不存在"

**原因：** 
- 没有在RAGFlow中创建知识库
- config.ini中的 `kb_name` 与RAGFlow中创建的名称不一致

**解决方案：**
```bash
# 1. 检查config.ini中的kb_name
grep "kb_name" config/config.ini

# 2. 登录RAGFlow Web界面
#    验证是否存在该名称的知识库
#    如果不存在，手动创建

# 3. 如果存在但名称不同，更新config.ini
#    确保两者名称完全一致
```

### 问题3：上传失败 - "文件格式不支持"

**原因：** RAGFlow不支持该文件格式

**解决方案：**
- 检查上传的文件格式是否为 PDF/DOCX/TXT
- 对于PDF，确保文件不是扫描图像（需要可提取的文本）

### 问题4：API Key错误

**原因：** RAGFlow API Key无效或过期

**解决方案：**
```bash
# 1. 在RAGFlow Web界面重新生成API Key
# 2. 复制新的API Key到config.ini
# 3. 确保格式正确：api_key = ragflow-xxxxx
```

---

## 📊 配置文件对应关系

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `host` | RAGFlow服务器地址 | localhost / 117.21.184.150 |
| `port` | RAGFlow服务端口 | 9380 |
| `api_key` | RAGFlow API认证密钥 | ragflow-xxxxx |
| `kb_name` | **必须与RAGFlow中创建的知识库名称一致** | policy_demo_kb |
| `kb_description` | 知识库描述（可选） | 政策知识库 - 专项债/特许经营/数据资产 |

---

## 💡 快速检查清单

在启动应用前，确保：

- [ ] RAGFlow服务已启动
- [ ] 可以访问RAGFlow Web界面（http://host:port）
- [ ] 在RAGFlow中创建了知识库
- [ ] 知识库名称记录下来
- [ ] config.ini已创建（从template复制）
- [ ] config.ini中的 `kb_name` 与RAGFlow中的名称一致
- [ ] 运行 `test_ragflow_upload.py` 通过验证
- [ ] Streamlit应用可正常启动

✅ 全部完成后，应用就可以正常使用了！

---

## 📝 文件上传流程

```
用户点击"上传文档"
  ↓
选择文件 (PDF/DOCX/TXT)
  ↓
填写政策信息（标题、类型、地区等）
  ↓
点击"上传"
  ↓
系统检查RAGFlow连接 ← 必须成功！
  ↓
上传文件到RAGFlow
  ↓
RAGFlow处理文件 ← 需要知识库存在！
  ↓
返回文档ID
  ↓
保存元数据到SQLite数据库
  ↓
✅ 上传成功
```

**如果在任何一步失败，都会显示详细的错误信息。**

---

## 🎯 核心要点

1. **RAGFlow必须提前启动** - 应用启动前就要运行
2. **知识库必须提前创建** - 在RAGFlow Web界面手动创建
3. **配置必须匹配** - config.ini中的 `kb_name` 必须与RAGFlow中的名称完全一致
4. **验证很重要** - 用 `test_ragflow_upload.py` 测试

这样就能避免90%的上传失败问题！
