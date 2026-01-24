# 🚀 快速开始指南

> 这是一个快速参考文档，包含最重要的信息

---

## 📊 当前状态一览

**项目完成度：69%** ✅ 大部分框架已完成，正在进入实现阶段

| 模块 | 状态 | 完成度 |
|------|------|--------|
| 配置系统 | ✅ 完成 | 100% |
| 外部服务（RAGFlow/Whisper） | ✅ 完成 | 100% |
| 数据模型 | ✅ 完成 | 100% |
| 业务逻辑 | ✅ 完成 | 100% |
| 工具函数 | ✅ 完成 | 100% |
| **页面实现** | 🔴 待做 | 0% |
| **代码注释** | 🟡 部分 | 30% |
| **测试验证** | 🔴 待做 | 0% |

---

## 🔴 立即需要做的事（优先级最高）

### 1. 修复 app.py 配置导入 (30分钟)

**问题：** app.py还在导入已删除的`config.app_config`
**解决方案：** 改为使用新的`src.config.get_config()`

**快速修复步骤：**
```bash
# 1. 打开 app.py 第17-25行
# 2. 替换导入语句（详见 IMPLEMENTATION_PLAN.md 第一部分）
# 3. 测试应用
streamlit run app.py
```

**修改内容摘要：**
```python
# ❌ 旧（错误）
from config.app_config import APP_NAME, ...

# ✅ 新（正确）
from src.config import get_config
config = get_config()
APP_NAME = config.app_name
```

### 2. 验证数据库兼容性 (20分钟)

检查这两个文件中是否有旧的配置导入：
- `src/database/db_manager.py`
- `src/database/policy_dao.py`

如果有`from config.`的导入，改为：
```python
from src.config import get_config
config = get_config()
```

---

## 📚 关键文档导航

| 文档 | 用途 | 阅读时间 |
|------|------|---------|
| **PROGRESS.md** | 详细的进度报告和统计 | 10分钟 |
| **TODO.md** | 所有待做任务的详细清单 | 20分钟 |
| **IMPLEMENTATION_PLAN.md** | 实现指导和代码模板 | 30分钟 |
| **README.md** | 项目说明和快速开始 | 10分钟 |
| **config/config.ini.template** | 配置文件模板 | 5分钟 |

---

## 🎯 接下来的工作计划（优先级排序）

### 第1阶段（1-2小时）：配置修复
- [ ] TASK-0.1：修复app.py配置导入
- [ ] TASK-0.2：验证db_manager兼容性
- [ ] 手工测试应用启动

### 第2阶段（3-4小时）：代码注释
- [ ] 为所有已完成的模块添加详细的中文注释
- 任务列表见 TODO.md 中的阶段1

### 第3阶段（8-10小时）：页面实现
实现5个页面，优先级从高到低：
1. **搜索页面** (search_page.py) - 3小时
2. **文档管理页面** (documents_page.py) - 3.5小时
3. **知识图谱页面** (graph_page.py) - 2.5小时
4. **语音问答页面** (voice_page.py) - 2.5小时
5. **政策分析页面** (analysis_page.py) - 2.5小时

### 第4阶段（2-3小时）：UI组件完整实现
- voice_ui.py
- policy_card.py
- 增强search_ui.py和graph_ui.py

### 第5阶段（1-2小时）：测试验证
- 手工测试所有页面
- 验证外部服务集成

### 第6阶段（1-2小时）：文档完善
- 更新README.md
- 创建API文档
- 创建开发指南

---

## 💡 重要概念速览

### 新的配置系统
```python
# 使用方式
from src.config import get_config
config = get_config()

# 访问各种配置
app_name = config.app_name
ragflow_host = config.ragflow_host
db_path = config.sqlite_path
```

**特点：**
- INI文件 + 环境变量覆盖
- 自动目录创建
- 类型转换（int, float, bool, list）
- 单例模式，全局访问

### 文件结构新变化
```
config/
├── config.ini.template    ✅ 配置模板（推荐复制为config.ini）
└── config.ini            （忽略，不上传git）

src/config/
├── config_loader.py      ✅ 配置加载器（Python代码）
└── __init__.py          ✅ 导出get_config()
```

---

## 🔧 开发环境快速检查

运行以下命令验证环境正常：

```bash
# 1. 进入项目目录
cd /Users/laurant/Documents/github/Investopedia

# 2. 验证虚拟环境（如果还没创建）
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建配置文件
cp config/config.ini.template config/config.ini

# 5. 启动应用（修复TASK-0.1后）
streamlit run app.py
```

---

## 📋 实现代码的标准格式

**文件头注释：**
```python
"""
模块名称 - 简要说明
====================
详细说明这个模块的作用...

功能清单：
- 功能A
- 功能B

使用示例：
    from src.xxx import xxx_func
    result = xxx_func()
"""
```

**函数注释：**
```python
def my_function(param1: str, param2: int) -> dict:
    """函数简要说明

    详细说明函数的作用和实现逻辑...

    Args:
        param1 (str): 参数1的说明
        param2 (int): 参数2的说明

    Returns:
        dict: 返回值的说明

    Example:
        >>> result = my_function("test", 10)
        >>> print(result)
    """
    # 关键逻辑的中文注释
    pass
```

---

## ⚠️ 常见问题

### Q: 为什么app.py会报ModuleNotFoundError？
**A:** 配置文件已从`config/`目录移到`src/config/`，需要更新导入。
参考：IMPLEMENTATION_PLAN.md 第一部分 - TASK-0.1

### Q: config.ini文件在哪里？
**A:**
- 模板：`config/config.ini.template`
- 实际配置：复制template为`config/config.ini`（会被git忽略）

```bash
cp config/config.ini.template config/config.ini
# 然后编辑config.ini，填入实际的RAGFlow/Whisper地址
```

### Q: 为什么Streamlit页面显示"正在开发中"？
**A:** 页面实现还未完成。所有5个页面都需要实现（TASK-2.1～2.5）

### Q: 如何运行单个页面进行开发？
**A:** 不用，Streamlit会自动重新加载。修改page代码后，保存文件，Streamlit会自动刷新。

### Q: 需要单元测试吗？
**A:** 目前不需要。先完成功能实现和手工测试，之后再考虑单元测试。

---

## 🎓 学习资源

- **Streamlit官方文档：** https://docs.streamlit.io/
- **NetworkX官方文档：** https://networkx.org/
- **Pyvis文档：** https://pyvis.readthedocs.io/
- **SQLAlchemy文档：** https://docs.sqlalchemy.org/
- **RAGFlow文档：** （根据实际部署地址）

---

## 📞 快速帮助

**遇到问题时：**
1. 先查看相关的文档（PROGRESS.md, IMPLEMENTATION_PLAN.md, README.md）
2. 检查TODO.md中的任务描述和验收标准
3. 查看代码注释（已完成的模块有详细注释）
4. 尝试运行代码，看错误消息提示

---

## ✅ 下一步行动

**现在就可以做：**
1. 阅读PROGRESS.md了解整体进度 (5分钟)
2. 阅读IMPLEMENTATION_PLAN.md第一部分 (10分钟)
3. 执行TASK-0.1和TASK-0.2修复 (1小时)
4. 测试应用是否能启动 (10分钟)

**完成上述后：**
5. 按照TASK-1.1～1.8添加代码注释 (3-4小时)
6. 按照TASK-2.1～2.5实现5个页面 (8-10小时)
7. 完成剩余任务

---

**祝开发顺利！** 🎉

有任何问题可以参考详细文档或查看代码中的注释。
