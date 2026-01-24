# 政策库Demo技术方案

## 一、整体架构

### 1.1 系统架构图
```
┌─────────────────────────────────────────────────────────┐
│         Streamlit前端应用 (我们的Python项目)              │
│                   http://localhost:8501                  │
├─────────────────────────────────────────────────────────┤
│ 页面模块 │ 服务客户端 │ 业务逻辑 │ 知识图谱 │             │
│ ┌─────┐ │ ┌───────┐ │ ┌─────┐ │ ┌─────┐ │             │
│ │搜索 │ │ │RAGFlow│ │ │元数据│ │ │Network│ │             │
│ │图谱 │ │ │客户端 │ │ │提取 │ │ │ X    │ │             │
│ │语音 │ │ │Whisper│ │ │标签 │ │ │Pyvis │ │             │
│ │文档 │ │ │客户端 │ │ │生成 │ │ │      │ │             │
│ │分析 │ │ │       │ │ │时效 │ │ │      │ │             │
│ └─────┘ │ └───────┘ │ │监控 │ │ └─────┘ │             │
│         │           │ │影响 │ │          │             │
│         │           │ │分析 │ │          │             │
│         │           │ └─────┘ │          │             │
└─────────┼───────────┴─────────┼──────────┴─────────────┘
          │ HTTP API调用         │ HTTP API调用
┌─────────▼──────────┐ ┌────────▼──────────┐
│    RAGFlow服务     │ │   Whisper服务     │
│ (外部Docker容器)   │ │ (外部Docker容器)   │
│   端口: 9380       │ │   端口: 9000       │
└────────────────────┘ └────────────────────┘
```

### 1.2 技术栈分工
- **我们的Python项目**：Streamlit前端 + 业务逻辑 + 知识图谱
- **外部服务1**：RAGFlow（文档处理和AI能力）
- **外部服务2**：Whisper（语音转文字）
- **集成方式**：Python项目通过HTTP API调用外部服务

## 二、三大政策领域定义

### 2.1 专项债政策领域
**核心内容：**
- 专项债发行管理办法
- 专项债券项目申报指南
- 专项债资金使用规范
- 专项债绩效评价办法
- 专项债风险防控指引

**关键要素：**
```
发行管理：
├─ 发行条件：主体资格、项目要求
├─ 审批流程：申报、评审、批复
├─ 额度管理：总额控制、地区分配
└─ 利率定价：市场定价机制

资金使用：
├─ 使用范围：项目清单、负面清单
├─ 支付流程：专户管理、进度拨付
└─ 监管要求：定期报告、现场检查

偿还机制：
├─ 偿还来源：项目收益、财政资金
├─ 偿还期限：期限结构、展期规则
└─ 风险缓释：担保措施、风险准备金
```

### 2.2 特许经营政策领域
**核心内容：**
- 基础设施特许经营管理办法
- PPP项目操作指南
- 特许经营期限与收费规定
- 特许经营项目监管办法
- 特许经营合同范本

**关键要素：**
```
适用范围：
├─ 行业领域：交通、市政、环保等
├─ 项目类型：新建、改扩建、存量
└─ 准入条件：资质要求、经验要求

操作流程：
├─ 前期准备：可行性研究、实施方案
├─ 招标投标：资格预审、投标评审
└─ 合同签订：谈判、签约、备案

运营管理：
├─ 运营期限：固定期限、弹性机制
├─ 收费标准：定价机制、调整规则
└─ 服务标准：服务质量、考核指标
```

### 2.3 数据资产政策领域
**核心内容：**
- 数据资产入表会计处理规定
- 数据要素市场化配置方案
- 数据资产登记管理办法
- 数据资产交易规则
- 数据资产评估指引

**关键要素：**
```
会计处理：
├─ 确认条件：控制权、经济利益
├─ 计量方法：成本法、收益法
└─ 披露要求：报表项目、附注说明

交易流转：
├─ 交易规则：定价、结算、交割
├─ 交易平台：登记、挂牌、撮合
└─ 交易监管：备案、监控、合规

价值管理：
├─ 评估方法：成本法、市场法、收益法
├─ 价值类型：市场价值、在用价值
└─ 价值维护：更新、维护、重估
```

## 三、政策库核心功能实现

### 3.1 政策来源标注系统
**自动提取规则：**
```python
# 专项债政策提取规则
SPECIAL_BONDS_PATTERNS = {
    "document_number": r"(财预|财库)〔\d{4}〕\d+号",
    "issuing_authority": r"(财政部|国家发改委|地方政府)",
    "date_patterns": [
        r"自(\d{4}年\d{1,2}月\d{1,2}日)起施行",
        r"发布日期[:：]\s*(\d{4}-\d{2}-\d{2})"
    ]
}

# 特许经营政策提取规则
FRANCHISE_PATTERNS = {
    "document_number": r"(发改投资|建设)〔\d{4}〕\d+号",
    "issuing_authority": r"(国家发改委|住房城乡建设部)",
    "project_types": ["PPP", "BOT", "TOT", "ROT"]
}

# 数据资产政策提取规则
DATA_ASSETS_PATTERNS = {
    "document_number": r"(财会|工信)〔\d{4}〕\d+号",
    "issuing_authority": r"(财政部|工信部|网信办)",
    "key_concepts": ["数据资产", "数据要素", "数据入表"]
}
```

**提取流程：**
1. 文档解析 → 2. 规则匹配 → 3. 信息提取 → 4. 人工校验 → 5. 结构化存储

### 3.2 标签体系实现
**三级标签结构：**
```
专项债标签体系：
├─ 一级：专项债
├─ 二级：发行管理/资金使用/偿还机制/绩效评价
└─ 三级：
    ├─ 发行管理 → 额度管理/利率定价/发行方式
    ├─ 资金使用 → 使用范围/支付流程/监管要求
    ├─ 偿还机制 → 偿还来源/偿还期限/风险缓释
    └─ 绩效评价 → 评价指标/评价方法/结果应用

特许经营标签体系：
├─ 一级：特许经营
├─ 二级：适用范围/操作流程/运营管理/风险管理
└─ 三级：
    ├─ 适用范围 → 行业领域/项目类型/准入条件
    ├─ 操作流程 → 招标投标/合同签订/项目实施
    ├─ 运营管理 → 运营期限/收费标准/服务标准
    └─ 风险管理 → 风险识别/风险分担/风险应对

数据资产标签体系：
├─ 一级：数据资产
├─ 二级：会计处理/交易流转/合规管理/价值管理
└─ 三级：
    ├─ 会计处理 → 确认条件/计量方法/披露要求
    ├─ 交易流转 → 交易规则/交易平台/交易监管
    ├─ 合规管理 → 数据安全/隐私保护/跨境传输
    └─ 价值管理 → 评估方法/价值类型/价值维护
```

**标签生成逻辑：**
- 基于规则的关键词匹配
- 基于内容的相似度计算
- 手动标注与自动标注结合

### 3.3 时效性监控机制
**监控规则：**
```python
class PolicyValidityMonitor:
    """政策时效性监控"""
    
    def check_validity(self, policy):
        """检查政策有效性"""
        checks = [
            self._check_expiration_date(policy),
            self._check_replacement(policy),
            self._check_implementation_status(policy),
            self._check_reference_status(policy)
        ]
        
        if any(check == "失效" for check in checks):
            return "已失效"
        elif any(check == "已更新" for check in checks):
            return "已更新"
        else:
            return "有效"
    
    def _check_expiration_date(self, policy):
        """检查失效日期"""
        if not policy.expiration_date:
            return "有效"
        return "失效" if policy.expiration_date < today else "有效"
    
    def _check_replacement(self, policy):
        """检查是否被替代"""
        newer_policies = self.find_newer_versions(policy)
        return "已更新" if newer_policies else "有效"
```

**监控策略：**
- 每日自动检查
- 失效前30天预警
- 新政策自动关联旧版本
- 状态变更通知

### 3.4 影响分析系统
**分析维度：**
```
专项债政策影响分析：
├─ 对地方政府的影响：
│   ├─ 融资渠道变化
│   ├─ 债务结构优化
│   └─ 项目管理要求
├─ 对金融机构的影响：
│   ├─ 投资机会变化
│   ├─ 风险管理要求
│   └─ 业务合规要求
├─ 对项目单位的影响：
│   ├─ 申报条件变化
│   ├─ 资金使用要求
│   └─ 绩效管理要求
└─ 对中介机构的影响：
    ├─ 咨询业务机会
    ├─ 评估认证要求
    └─ 法律服务需求

特许经营政策影响分析：
├─ 对社会资本的影响：
│   ├─ 投资机会变化
│   ├─ 回报机制调整
│   └─ 风险分担变化
├─ 对政府部门的影响：
│   ├─ 监管职责变化
│   ├─ 财政支出影响
│   └─ 公共服务优化
├─ 对实施机构的影响：
│   ├─ 运营要求变化
│   ├─ 收费标准调整
│   └─ 考核指标变化
└─ 对服务机构的影响：
    ├─ 咨询需求变化
    ├─ 法律服务需求
    └─ 技术支持需求

数据资产政策影响分析：
├─ 对企业单位的影响：
│   ├─ 财务报表变化
│   ├─ 资产管理要求
│   └─ 价值实现路径
├─ 对金融机构的影响：
│   ├─ 信贷评估变化
│   ├─ 投资标的扩展
│   └─ 风险管理要求
├─ 对中介机构的影响：
│   ├─ 评估业务机会
│   ├─ 交易服务需求
│   └─ 合规服务需求
└─ 对政府部门的影响：
    ├─ 数据治理要求
    ├─ 市场监管职责
    └─ 统计核算变化
```

**分析方法：**
1. 政策条款解析 → 2. 影响范围识别 → 3. 影响程度评估 → 4. 实施建议生成

## 四、核心功能模块设计

### 4.1 政策搜索模块
**搜索界面设计：**
```
搜索区域：
├─ 快速搜索框：自然语言输入
├─ 高级搜索面板：
│   ├─ 政策领域：专项债/特许经营/数据资产
│   ├─ 地区范围：全国/省份/城市
│   ├─ 时间范围：起始日期 - 结束日期
│   ├─ 政策状态：有效/失效/更新
│   └─ 发文机关：多选下拉
└─ 搜索按钮：执行搜索

搜索结果展示：
├─ 列表视图：
│   ├─ 政策标题（带类型图标）
│   ├─ 发文机关 + 文号
│   ├─ 发布日期 + 状态标签
│   ├─ 内容摘要（前200字）
│   └─ 查看详情按钮
├─ 详情面板：
│   ├─ 完整政策内容
│   ├─ 元数据展示
│   ├─ 标签体系
│   ├─ 影响分析摘要
│   └─ 相关推荐
└─ 侧边栏筛选：
    ├─ 按标签筛选
    ├─ 按领域筛选
    ├─ 按地区筛选
    └─ 按时间筛选
```

**搜索逻辑：**
```python
class PolicySearch:
    def search(self, query, filters):
        # 1. 调用RAGFlow进行语义搜索
        semantic_results = self.ragflow_client.search(query)
        
        # 2. 本地元数据筛选
        filtered_results = self.filter_by_metadata(semantic_results, filters)
        
        # 3. 结果排序
        sorted_results = self.rank_results(filtered_results, query)
        
        # 4. 补充本地信息
        enriched_results = self.enrich_with_local_data(sorted_results)
        
        return enriched_results
```

### 4.2 知识图谱模块
**图谱数据结构：**
```python
class PolicyGraph:
    def __init__(self):
        # 使用NetworkX内存图
        self.graph = nx.Graph()
        
        # 节点类型定义
        self.node_types = {
            "policy": "政策节点",
            "authority": "发文机构",
            "region": "适用地区", 
            "concept": "关键概念",
            "project": "项目类型"
        }
        
        # 边关系定义
        self.edge_relations = {
            "issued_by": "发布关系",
            "applies_to": "适用关系", 
            "references": "引用关系",
            "affects": "影响关系",
            "replaces": "替代关系"
        }
```

**可视化界面：**
```
图谱控制面板：
├─ 视图选择：
│   ├─ 全局视图：显示所有节点
│   ├─ 子图视图：聚焦特定领域
│   └─ 时间线视图：按时间排序
├─ 布局算法：
│   ├─ 力导向布局
│   ├─ 圆形布局
│   └─ 层次布局
└─ 交互控制：
    ├─ 缩放：鼠标滚轮
    ├─ 拖拽：按住节点移动
    ├─ 点击：查看节点详情
    └─ 搜索：高亮相关节点

节点展示：
├─ 政策节点：
│   ├─ 颜色：按领域区分
│   ├─ 大小：按重要性区分
│   └─ 标签：政策标题缩写
├─ 机构节点：
│   ├─ 形状：方形
│   └─ 颜色：按级别区分
└─ 地区节点：
    ├─ 形状：圆形
    └─ 颜色：按地区区分

边关系展示：
├─ 实线：强关联关系
├─ 虚线：弱关联关系
├─ 箭头：方向性关系
└─ 标签：关系类型
```

### 4.3 语音问答模块
**语音处理流程：**
```
语音输入 → 音频处理 → 语音识别 → 文本清洗 → 
问题分类 → 查询构建 → 政策检索 → 答案生成 → 
结果展示
```

**界面设计：**
```
语音控制区域：
├─ 录音控制：
│   ├─ 开始录音按钮
│   ├─ 停止录音按钮
│   └─ 录音时长显示
├─ 音频波形：
│   └─ 实时波形显示
├─ 文件上传：
│   ├─ 选择文件按钮
│   ├─ 支持格式提示
│   └─ 上传进度显示
└─ 语音设置：
    ├─ 语言选择：中文/英文
    ├─ 模型选择：质量优先/速度优先
    └─ 降噪选项：开启/关闭

问答结果显示：
├─ 语音转写结果：
│   ├─ 识别文本显示
│   ├─ 置信度指示器
│   └─ 编辑修正功能
├─ 政策答案：
│   ├─ 结构化答案展示
│   ├─ 引用政策标注
│   └─ 相关建议提示
└─ 历史记录：
    ├─ 最近查询列表
    ├─ 查询时间记录
    └─ 答案质量反馈
```

### 4.4 文档管理模块
**文档处理流程：**
```
文档上传 → 格式检测 → 内容解析 → 元数据提取 → 
标签标注 → 向量化 → 索引更新 → 图谱更新
```

**管理界面：**
```
文档列表视图：
├─ 表格展示：
│   ├─ 文件名
│   ├─ 政策类型
│   ├─ 处理状态
│   ├─ 上传时间
│   └─ 操作按钮
├─ 状态筛选：
│   ├─ 全部文档
│   ├─ 已处理完成
│   ├─ 处理中
│   └─ 处理失败
└─ 批量操作：
    ├─ 批量上传
    ├─ 批量删除
    ├─ 批量重新处理
    └─ 批量导出

文档详情视图：
├─ 基本信息：
│   ├─ 文件名和路径
│   ├─ 文件大小和格式
│   ├─ 上传时间和用户
│   └─ 处理日志
├─ 元数据编辑：
│   ├─ 基础信息编辑
│   ├─ 标签管理
│   └─ 状态设置
├─ 内容预览：
│   └─ 文档内容显示
└─ 相关操作：
    ├─ 重新处理
    ├─ 下载原始文件
    ├─ 查看处理结果
    └─ 删除文档
```

### 4.5 政策分析模块
**分析界面设计：**
```
时效性分析面板：
├─ 状态统计：
│   ├─ 有效政策数量
│   ├─ 失效政策数量
│   ├─ 更新政策数量
│   └─ 即将失效预警
├─ 趋势分析：
│   ├─ 月度发布趋势图
│   ├─ 年度有效性统计
│   └─ 领域分布变化
└─ 详细列表：
    ├─ 即将失效政策列表
    ├─ 近期更新政策列表
    └─ 长期有效政策列表

影响分析面板：
├─ 影响范围分析：
│   ├─ 影响地区分布图
│   ├─ 影响行业分布图
│   └─ 影响对象分布图
├─ 影响程度评估：
│   ├─ 高影响政策列表
│   ├─ 中影响政策列表
│   └─ 低影响政策列表
└─ 实施建议：
    ├─ 关键要点总结
    ├─ 实施步骤建议
    └─ 风险提示列表
```

## 五、知识图谱构建

### 5.1 实体识别
**实体类型定义：**
```python
# 专项债实体类型
SPECIAL_BONDS_ENTITIES = {
    "POLICY": "专项债政策",
    "AUTHORITY": "发文机构",
    "PROJECT": "项目类型", 
    "REGION": "适用地区",
    "FUND": "资金类型",
    "RISK": "风险类型"
}

# 特许经营实体类型
FRANCHISE_ENTITIES = {
    "POLICY": "特许经营政策",
    "AUTHORITY": "监管机构",
    "INDUSTRY": "行业领域",
    "CONTRACT": "合同类型",
    "RISK": "风险因素",
    "EVALUATION": "评价指标"
}

# 数据资产实体类型
DATA_ASSETS_ENTITIES = {
    "POLICY": "数据资产政策",
    "AUTHORITY": "主管机构",
    "DATA_TYPE": "数据类型",
    "VALUE_METHOD": "评估方法",
    "TRANSACTION": "交易方式",
    "COMPLIANCE": "合规要求"
}
```

**实体提取规则：**
1. 基于规则的提取：正则表达式匹配
2. 基于字典的提取：预定义实体词典
3. 基于模型的提取：NER模型识别

### 5.2 关系抽取
**关系类型定义：**
```python
# 政策间关系
POLICY_RELATIONS = {
    "REPLACES": "替代关系",
    "AMENDS": "修订关系",
    "REFERENCES": "引用关系",
    "RELATES_TO": "相关关系"
}

# 政策与实体关系
ENTITY_RELATIONS = {
    "ISSUED_BY": "由...发布",
    "APPLIES_TO": "适用于...",
    "AFFECTS": "影响...",
    "MENTIONS": "提及..."
}
```

**关系提取方法：**
1. 基于句式模板：匹配特定句式结构
2. 基于依存分析：分析句法依存关系
3. 基于共现统计：统计实体共现频率

### 5.3 图谱构建流程
```
图谱构建流程：
1. 数据准备：
   ├─ 政策文档集合
   ├─ 元数据信息
   └─ 处理历史记录

2. 实体提取：
   ├─ 政策实体提取
   ├─ 机构实体提取
   ├─ 地区实体提取
   └─ 概念实体提取

3. 关系抽取：
   ├─ 发布关系抽取
   ├─ 引用关系抽取
   ├─ 适用关系抽取
   └─ 影响关系抽取

4. 图谱构建：
   ├─ 节点创建和属性设置
   ├─ 边创建和属性设置
   ├─ 图谱布局计算
   └─ 可视化生成

5. 质量检查：
   ├─ 一致性检查
   ├─ 完整性检查
   ├─ 准确性检查
   └─ 可视化效果检查
```

### 5.4 图谱更新机制
**更新策略：**
- 增量更新：新政策加入时更新相关子图
- 定时更新：每日自动检查并更新图谱
- 手动更新：用户触发更新特定部分

**版本管理：**
- 图谱快照保存
- 变更记录跟踪
- 版本回滚能力

## 六、数据流程设计

### 6.1 政策数据入库流程
```
原始文档收集 → 格式转换 → 文本提取 → 预处理 → 
元数据提取 → 内容分析 → 向量化处理 → 索引建立 → 
知识图谱构建 → 分析处理 → 存储入库
```

**详细步骤：**
1. **文档收集**：
   - 从各渠道收集政策文档
   - 格式统一化处理
   - 文件命名规范化

2. **内容提取**：
   - PDF/DOCX/Excel格式解析
   - 文本内容提取和清洗
   - 表格和图片内容处理

3. **元数据处理**：
   - 发文机关识别
   - 文号提取
   - 日期识别
   - 适用范围分析

4. **向量化处理**：
   - 文本分块处理
   - 向量嵌入生成
   - 相似度计算

5. **图谱构建**：
   - 实体识别和提取
   - 关系抽取和验证
   - 图谱存储和索引

6. **分析处理**：
   - 时效性分析
   - 影响分析
   - 趋势分析

### 6.2 用户查询处理流程
```
用户输入 → 输入解析 → 意图识别 → 查询构建 → 
检索执行 → 结果处理 → 答案生成 → 结果展示 → 
用户反馈
```

**详细步骤：**
1. **输入解析**：
   - 文本查询解析
   - 语音查询转文字
   - 查询条件提取

2. **意图识别**：
   - 查询类型分类
   - 领域识别
   - 需求分析

3. **查询构建**：
   - 关键词提取
   - 查询条件组合
   - 检索参数设置

4. **检索执行**：
   - 向量检索
   - 关键词检索
   - 元数据过滤

5. **结果处理**：
   - 结果去重
   - 相关性排序
   - 结果摘要生成

6. **答案生成**：
   - 基于检索结果
   - 结构化答案组织
   - 引用来源标注

7. **结果展示**：
   - 分页展示
   - 详细视图
   - 相关推荐

### 6.3 语音处理流程
```
语音输入 → 音频预处理 → 语音识别 → 文本后处理 → 
问题解析 → 领域判断 → 查询执行 → 答案生成 → 
结果格式化 → 返回展示
```

**详细步骤：**
1. **音频预处理**：
   - 降噪处理
   - 音量标准化
   - 格式转换

2. **语音识别**：
   - 调用Whisper服务
   - 语音转文字
   - 时间戳对齐

3. **文本后处理**：
   - 标点符号恢复
   - 数字标准化
   - 专业术语校正

4. **问题解析**：
   - 关键词提取
   - 意图识别
   - 实体识别

5. **查询执行**：
   - 构建查询参数
   - 执行政策检索
   - 获取相关结果

6. **答案生成**：
   - 总结检索结果
   - 生成结构化答案
   - 添加引用说明

7. **结果展示**：
   - 显示识别文本
   - 展示政策答案
   - 提供相关链接

---

## 七、外部系统配置

### 7.1 RAGFlow服务配置

#### Docker部署配置
```yaml
# docker-compose.ragflow.yml
version: '3.8'

services:
  ragflow:
    image: infiniflow/ragflow:latest
    container_name: ragflow-policy-demo
    restart: unless-stopped
    ports:
      - "9380:9380"
    volumes:
      - ./data/ragflow:/app/data
      - ./docs:/app/docs
      - ./config/ragflow:/app/config
    environment:
      # 基础配置
      - RAGFLOW_SERVER_PORT=9380
      - LOG_LEVEL=INFO
      
      # 嵌入模型配置
      - EMBEDDING_MODEL=bge-m3
      - EMBEDDING_MODEL_DIM=1024
      - EMBEDDING_DEVICE=cpu
      
      # LLM配置（使用DeepSeek API）
      - LLM_MODEL=deepseek-chat
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - LLM_MAX_TOKENS=2000
      - LLM_TEMPERATURE=0.1
      
      # 向量数据库配置
      - VECTOR_DB=chroma
      - CHROMA_PERSIST_DIR=/app/data/chroma
      
      # 文档处理配置
      - CHUNK_SIZE=500
      - CHUNK_OVERLAP=50
      - SMART_CHUNKING=true
      
      # 检索配置
      - SEARCH_TYPE=hybrid
      - TOP_K=10
      - SCORE_THRESHOLD=0.7
```

#### RAGFlow定制配置
```yaml
# config/ragflow/custom_config.yaml
knowledge_base:
  name: "policy_demo_kb"
  description: "政策知识库 - 专项债/特许经营/数据资产"
  
document_processing:
  parsers:
    pdf:
      extract_tables: true
      extract_images: false
      ocr_enabled: false
      
    docx:
      extract_styles: true
      preserve_formatting: true
      
    excel:
      sheet_strategy: "all"
      header_detection: true
      
  chunking:
    strategy: "semantic"
    chunk_size: 500
    chunk_overlap: 50
    preserve_structure: true
    
  metadata_extraction:
    enabled: true
    fields:
      - name: "document_number"
        pattern: "文号[:：]\s*([^\\s]+)"
        
      - name: "issuing_authority"
        pattern: "发文机关[:：]\s*([^\\n]+)"
        
      - name: "publish_date"
        pattern: "发布日期[:：]\s*(\d{4}年\d{1,2}月\d{1,2}日)"
        
      - name: "effective_date"
        pattern: "自(\d{4}年\d{1,2}月\d{1,2}日)起"

retrieval:
  hybrid_search:
    vector_weight: 0.7
    keyword_weight: 0.2
    metadata_weight: 0.1
    
  reranking:
    enabled: true
    model: "bge-reranker-base"
    
  filters:
    policy_types: ["专项债", "特许经营", "数据资产"]
    date_range: ["2020-01-01", "2024-12-31"]
    
qa_prompts:
  policy_qa_template: |
    你是一个政策咨询专家，请根据以下政策内容回答问题。
    
    相关政策：
    {context}
    
    问题：{question}
    
    回答要求：
    1. 基于政策内容，准确回答问题
    2. 引用具体的政策条款和规定
    3. 如果政策中有时间要求，请明确指出
    4. 如果政策中有适用条件，请详细说明
    5. 如果政策内容不相关，请说明无法回答
    
    回答格式：
    【政策依据】相关条款内容
    【核心要点】主要规定和要求
    【注意事项】需要特别关注的内容
    【适用建议】实际操作建议
    
    回答：
```

#### API接口配置
```python
# 我们的Python项目中调用RAGFlow的配置
RAGFLOW_CONFIG = {
    "base_url": "http://localhost:9380",
    "endpoints": {
        "health": "/api/health",
        "upload": "/api/upload",
        "search": "/api/search",
        "ask": "/api/ask",
        "documents": "/api/documents",
        "delete": "/api/documents/{id}"
    },
    "timeout": 30,
    "retry_times": 3,
    "headers": {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
}
```

### 7.2 Whisper服务配置

#### Docker部署配置
```yaml
# docker-compose.whisper.yml
version: '3.8'

services:
  whisper-api:
    image: onerahmet/openai-whisper-asr-webservice:latest
    container_name: whisper-policy-demo
    restart: unless-stopped
    ports:
      - "9000:9000"
    volumes:
      - ./data/whisper/cache:/root/.cache/whisper
    environment:
      # 模型配置
      - ASR_MODEL=base
      - ASR_MODEL_SIZE=base
      - ASR_DEVICE=cpu
      
      # 语言配置
      - ASR_LANGUAGE=zh
      - ASR_TASK=transcribe
      
      # 性能配置
      - ASR_COMPUTE_TYPE=float32
      - ASR_BATCH_SIZE=16
      - ASR_THREADS=4
      
      # 服务配置
      - ASR_HOST=0.0.0.0
      - ASR_PORT=9000
      - ASR_WORKERS=2
      
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### API接口说明
```python
# Whisper服务API接口定义
WHISPER_API = {
    # 健康检查
    "health": {
        "method": "GET",
        "path": "/health",
        "response": {"status": "healthy"}
    },
    
    # 语音转文字
    "transcribe": {
        "method": "POST",
        "path": "/asr",
        "parameters": {
            "task": "transcribe|translate",
            "language": "zh|en|ja|ko",
            "word_timestamps": "true|false"
        },
        "file_parameter": "audio_file",
        "response_format": {
            "text": "识别文本",
            "segments": [
                {
                    "text": "分段文本",
                    "start": 0.0,
                    "end": 5.0,
                    "confidence": 0.95
                }
            ]
        }
    },
    
    # 支持的语言列表
    "languages": {
        "method": "GET",
        "path": "/languages",
        "response": ["zh", "en", "ja", "ko"]
    }
}
```

#### 我们的Python项目集成配置
```python
# config/whisper_config.py
WHISPER_CONFIG = {
    "base_url": "http://localhost:9000",
    "endpoints": {
        "transcribe": "/asr",
        "health": "/health",
        "languages": "/languages"
    },
    "default_params": {
        "task": "transcribe",
        "language": "zh",
        "word_timestamps": False
    },
    "timeout": 60,  # 语音识别可能较慢
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
    
    # 音频预处理配置
    "audio_preprocessing": {
        "sample_rate": 16000,
        "channels": 1,
        "normalize": True,
        "remove_silence": False,
        "max_duration": 300  # 最大5分钟
    }
}
```

### 7.3 综合部署脚本
```bash
#!/bin/bash
# deploy.sh - 一键部署所有外部服务

echo "=== 政策库Demo外部服务部署 ==="

# 创建目录结构
mkdir -p data/{ragflow,whisper/cache,documents}
mkdir -p config/{ragflow,whisper}

# 1. 部署RAGFlow服务
echo "部署RAGFlow服务..."
docker-compose -f docker-compose.ragflow.yml up -d

# 2. 部署Whisper服务
echo "部署Whisper服务..."
docker-compose -f docker-compose.whisper.yml up -d

# 3. 等待服务启动
echo "等待服务启动..."
sleep 10

# 4. 检查服务状态
echo "检查服务状态..."
curl -f http://localhost:9380/api/health && echo "RAGFlow服务正常"
curl -f http://localhost:9000/health && echo "Whisper服务正常"

# 5. 创建测试文档目录
echo "创建文档目录..."
mkdir -p test_documents/{special_bonds,franchise,data_assets}

echo "=== 部署完成 ==="
echo "RAGFlow服务: http://localhost:9380"
echo "Whisper服务: http://localhost:9000"
echo "我们的Python项目需要配置以上地址"
```

### 7.4 环境变量配置
```bash
# .env 文件
# RAGFlow配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
RAGFLOW_DATA_DIR=./data/ragflow
RAGFLOW_DOCS_DIR=./docs

# Whisper配置
WHISPER_MODEL=base
WHISPER_LANGUAGE=zh

# 应用配置
APP_PORT=8501
APP_DEBUG=false

# 网络配置
RAGFLOW_HOST=localhost
RAGFLOW_PORT=9380
WHISPER_HOST=localhost
WHISPER_PORT=9000
```

### 7.5 监控和日志配置
```yaml
# 监控配置
monitoring:
  ragflow:
    health_check: "http://localhost:9380/api/health"
    metrics_endpoint: "http://localhost:9380/metrics"
    log_file: "./logs/ragflow.log"
    
  whisper:
    health_check: "http://localhost:9000/health"
    log_file: "./logs/whisper.log"
    
  our_app:
    log_level: "INFO"
    log_file: "./logs/app.log"
    access_log: "./logs/access.log"
```

### 7.6 服务依赖检查脚本
```python
# check_services.py - 检查外部服务状态
import requests
import time

def check_service(name, url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}服务正常: {url}")
            return True
        else:
            print(f"❌ {name}服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}服务无法连接: {str(e)}")
        return False

def main():
    services = {
        "RAGFlow": "http://localhost:9380/api/health",
        "Whisper": "http://localhost:9000/health"
    }
    
    print("正在检查外部服务状态...")
    all_ok = True
    
    for name, url in services.items():
        if not check_service(name, url):
            all_ok = False
    
    if all_ok:
        print("所有外部服务运行正常！")
    else:
        print("部分服务异常，请检查部署状态。")

if __name__ == "__main__":
    main()
```

---

**部署总结：**

1. **RAGFlow服务**：提供文档处理和AI能力，通过Docker部署在9380端口
2. **Whisper服务**：提供语音转文字能力，通过Docker部署在9000端口  
3. **我们的Python项目**：包含前端界面和业务逻辑，调用以上两个服务
4. **知识图谱**：直接在我们的Python项目中用NetworkX+Pyvis实现，不需要额外部署

这样划分清晰，部署简单，各服务职责明确。
