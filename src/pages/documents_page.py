"""
文档管理页面
==========
提供政策文档上传、列表展示、编辑、删除等功能。

核心功能：
- 文档上传：支持PDF/DOCX/TXT格式，支持手动或自动生成文号
- 文档列表：分页显示已上传文档，显示标题、文号、状态、上传时间
- 文档详情：展示完整文档信息、时效性状态
- 文档管理：支持搜索、编辑、删除操作
- 自动生成：根据政策类型和日期自动生成文号

使用示例：
    import streamlit as st
    from src.pages import documents_page
    documents_page.show()
"""
import streamlit as st
import tempfile
import os
from datetime import datetime
from src.database.policy_dao import PolicyDAO
from src.business.validity_checker import ValidityChecker
from src.components.policy_card import render_policy_card, render_policy_detail, render_policy_form
from src.services.ragflow_client import get_ragflow_client
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


def generate_document_number(policy_type: str) -> str:
    """自动生成文号
    
    Args:
        policy_type: 政策类型 (special_bonds/franchise/data_assets)
        
    Returns:
        str: 生成的文号，格式如"财预〔2026〕001号"
        
    示例：
        >>> generate_document_number('special_bonds')
        '财预〔2026〕001号'
    """
    from src.database.policy_dao import get_policy_dao
    
    year = datetime.now().year
    dao = get_policy_dao()
    
    # 获取该类型今年已有的文档数量
    existing = dao.get_policies(filters={'policy_type': policy_type})
    count = len(existing) + 1
    
    # 根据政策类型生成相应的文号前缀
    prefix_map = {
        'special_bonds': f'财预〔{year}〕',      # 财政预算类
        'franchise': f'发改投资〔{year}〕',      # 发改投资类
        'data_assets': f'财会〔{year}〕'         # 财会类
    }
    
    prefix = prefix_map.get(policy_type, f'政策〔{year}〕')
    return f'{prefix}{count:03d}号'


def show():
    st.title("📄 文档管理")

    # 初始化session state
    if "documents_list" not in st.session_state:
        st.session_state.documents_list = []
    if "edit_policy_id" not in st.session_state:
        st.session_state.edit_policy_id = None

    # 标签页
    tab_upload, tab_list, tab_manage = st.tabs(["📤 上传文档", "📋 文档列表", "⚙️ 文档管理"])

    with tab_upload:
        render_upload_section()

    with tab_list:
        render_documents_list()

    with tab_manage:
        render_manage_section()


def render_upload_section():
    """文档上传部分"""
    st.subheader("上传政策文档")

    col_file, col_info = st.columns([2, 1])

    with col_file:
        uploaded_file = st.file_uploader(
            "选择PDF、Word或文本文件",
            type=["pdf", "docx", "txt"],
            help="支持常见文档格式"
        )

    with col_info:
        st.info("支持格式：PDF、DOCX、TXT")

    if uploaded_file:
        st.write(f"选中文件：{uploaded_file.name}")

        # 文档基本信息表单
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("政策名称", value=uploaded_file.name.split('.')[0])
            policy_type = st.selectbox("政策类型", ["special_bonds", "franchise", "data_assets"],
                                       format_func=lambda x: {"special_bonds": "特别国债", "franchise": "特许经营", "data_assets": "数据资产"}.get(x, x))

        with col2:
            region = st.selectbox("适用地区", ["全国", "京津冀", "长三角", "粤港澳", "成渝"])
            
            # 自动生成文号 - 预生成后可修改
            auto_docnum = generate_document_number(policy_type)
            document_number = st.text_input("文号", value=auto_docnum, 
                                           help="系统已预生成文号，可修改为其他文号")
            st.caption(f"💡 已预生成: {auto_docnum}（可修改）")

        if st.button("✅ 上传文档", use_container_width=True):
            try:
                # 表单验证
                if not title or title.strip() == '':
                    st.error("❌ 政策名称不能为空")
                    return

                # 检查文号的唯一性
                dao = PolicyDAO()
                if document_number and document_number.strip() != '':
                    existing_policy = dao.get_policy_by_document_number(document_number.strip())
                    if existing_policy:
                        st.error(f"❌ 文号 '{document_number}' 已存在，请修改后重试")
                        return
                    document_number = document_number.strip()
                else:
                    st.error("❌ 文号不能为空")
                    return

                # 上传文件到RAGFlow
                with st.spinner("📤 正在上传文档到RAGFlow..."):
                    ragflow_client = get_ragflow_client()
                    
                    # 检查RAGFlow连接
                    if not ragflow_client.check_health():
                        st.error("❌ RAGFlow服务不可用，请检查：\n1. RAGFlow是否已启动\n2. 配置中的host/port是否正确\n3. 网络连接是否正常")
                        return
                    
                    # 将Streamlit的文件对象保存为临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    
                    try:
                        # 从配置读取知识库名称
                        config = get_config()
                        kb_name = config.ragflow_kb_name
                        
                        # 上传到RAGFlow
                        st.info(f"📄 文件已保存为临时文件: {tmp_path}")
                        st.info(f"🔄 正在上传到RAGFlow知识库: {kb_name}")
                        
                        doc_id = ragflow_client.upload_document(
                            file_path=tmp_path,
                            file_name=uploaded_file.name,
                            knowledge_base_name=kb_name
                        )
                        
                        if not doc_id:
                            st.error(f"""
❌ 上传到RAGFlow失败！可能的原因：

1. **知识库不存在** - 需要在RAGFlow中先创建 '{kb_name}'
2. **文件格式不支持** - 检查RAGFlow是否支持此格式
3. **API端点配置错误** - 检查config.ini中的RAGFlow配置
4. **权限问题** - 检查RAGFlow API Key是否有效

💡 建议：
- 登录RAGFlow Web界面 (http://host:9380)
- 手动创建名为 '{kb_name}' 的知识库
- 检查 config/config.ini 中 [RAGFLOW] 的配置是否正确

📋 当前配置：
- Host: {ragflow_client.client.base_url}
- Knowledge Base: {kb_name}
                            """)
                            return
                        
                        # 保存到数据库（content存储RAGFlow文档ID）
                        policy_data = {
                            'title': title.strip(),
                            'content': doc_id,  # 存储RAGFlow文档ID
                            'summary': f"已上传到RAGFlow，文档ID: {doc_id}",
                            'policy_type': policy_type,
                            'region': region,
                            'document_number': document_number,
                            'file_path': uploaded_file.name
                        }
                        policy_id = dao.create_policy(policy_data)

                        st.success(f"✅ 文档已上传：{title}")
                        st.info(f"📚 RAGFlow文档ID: {doc_id}")
                        st.session_state.documents_list = []  # 清空缓存
                        
                    finally:
                        # 清理临时文件
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

            except ValueError as e:
                # 处理业务逻辑错误（如文号重复）
                st.error(f"❌ {str(e)}")
            except Exception as e:
                # 处理其他数据库或系统错误
                if "UNIQUE constraint failed" in str(e):
                    st.error("❌ 文号已存在，请修改后重试")
                else:
                    st.error(f"❌ 上传失败：{str(e)}")


def render_documents_list():
    """文档列表部分 - 查看已上传文档"""
    st.subheader("已上传文档")

    try:
        dao = PolicyDAO()
        policies = dao.get_policies()

        if not policies:
            st.info("暂无文档，请先上传")
            return

        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总文档数", len(policies))
        col2.metric("有效文档", len([p for p in policies if p.get('status') == "active"]))
        col3.metric("失效文档", len([p for p in policies if p.get('status') == "expired"]))
        col4.metric("即将失效", len([p for p in policies if p.get('status') == "expiring_soon"]))

        st.divider()

        # 文档列表 - 添加删除按钮
        for policy in policies:
            col_card, col_actions = st.columns([5, 1])

            policy_id = policy.get('id')
            policy_title = policy.get('title', '无标题')

            with col_card:
                # 显示政策卡片
                st.write(f"**{policy_title}**")
                st.caption(f"文号: {policy.get('document_number', 'N/A')} | 类型: {policy.get('policy_type', 'N/A')} | 状态: {policy.get('status', 'UNKNOWN')}")

                if st.button(f"📖 查看详情", key=f"detail_{policy_id}"):
                    st.session_state["show_detail"] = policy_id

            # 删除按钮
            with col_actions:
                if st.button("🗑️", key=f"list_delete_{policy_id}", help="删除文档"):
                    if st.session_state.get(f"confirm_delete_{policy_id}"):
                        delete_policy(policy_id)
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{policy_id}"] = True
                        st.warning(f"确认删除？再点一次确认")

            # 显示详情
            if st.session_state.get("show_detail") == policy_id:
                with st.expander(f"📖 {policy_title} - 详情", expanded=True):
                    st.write("**文档信息**")
                    st.write(f"标题: {policy_title}")
                    st.write(f"文号: {policy.get('document_number')}")
                    st.write(f"类型: {policy.get('policy_type')}")
                    st.write(f"地区: {policy.get('region')}")
                    st.write(f"状态: {policy.get('status')}")
                    st.write(f"摘要: {policy.get('summary')[:100]}...")

    except Exception as e:
        st.error(f"加载文档列表失败：{str(e)}")


def render_manage_section():
    """文档管理部分 - 支持搜索、编辑、删除"""
    st.subheader("文档管理")

    dao = PolicyDAO()
    policies = dao.get_policies()

    if not policies:
        st.info("暂无文档")
        return

    # 搜索和筛选
    col_search, col_filter, col_action = st.columns([2, 2, 1])

    with col_search:
        search_text = st.text_input("🔍 搜索文档", placeholder="输入标题或文号")
    
    with col_filter:
        filter_status = st.multiselect(
            "按状态筛选",
            ["active", "expired", "updated"],
            default=["active"]
        )

    with col_action:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    # 应用搜索和筛选
    filtered_policies = [
        p for p in policies 
        if (p.get('status') in filter_status and
            (search_text.lower() in str(p.get('title', '')).lower() or
             search_text.lower() in str(p.get('document_number', '')).lower()))
    ]

    st.divider()

    # 搜索结果统计
    st.caption(f"📊 搜索结果：{len(filtered_policies)}/{len(policies)} 个文档")

    if not filtered_policies:
        st.warning("⚠️ 没有找到匹配的文档")
        return

    # 文档列表 - 支持编辑和删除
    for idx, policy in enumerate(filtered_policies):
        col_info, col_actions = st.columns([4, 1])
        
        policy_id = policy.get('id')
        policy_title = policy.get('title', '无标题')
        policy_docnum = policy.get('document_number', 'N/A')

        with col_info:
            st.write(f"**{policy_title}**")
            st.caption(f"文号: {policy_docnum} | 类型: {policy.get('policy_type', 'N/A')} | 状态: {policy.get('status', 'UNKNOWN')}")

        with col_actions:
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("✏️", key=f"edit_{policy_id}", help="编辑文档"):
                    st.session_state[f"editing_{policy_id}"] = True
            
            with col_delete:
                if st.button("🗑️", key=f"delete_{policy_id}", help="删除文档"):
                    if st.session_state.get(f"confirm_delete_{policy_id}"):
                        delete_policy(policy_id)
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{policy_id}"] = True
                        st.warning(f"确认删除 '{policy_title}'？再点一次确认")

        # 编辑界面
        if st.session_state.get(f"editing_{policy_id}"):
            with st.expander(f"✏️ 编辑 - {policy_title}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_title = st.text_input("标题", value=policy_title, key=f"title_{policy_id}")
                    new_docnum = st.text_input("文号", value=policy_docnum, key=f"docnum_{policy_id}")
                
                with col2:
                    new_type = st.selectbox(
                        "类型",
                        ["special_bonds", "franchise", "data_assets"],
                        index=0 if policy.get('policy_type') == "special_bonds" else 1,
                        key=f"type_{policy_id}"
                    )
                    new_region = st.selectbox(
                        "地区",
                        ["全国", "京津冀", "长三角", "粤港澳", "成渝"],
                        key=f"region_{policy_id}"
                    )

                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    if st.button("💾 保存修改", key=f"save_{policy_id}"):
                        try:
                            update_data = {
                                'title': new_title,
                                'document_number': new_docnum if new_docnum else None,
                                'policy_type': new_type,
                                'region': new_region
                            }
                            dao.update_policy(policy_id, update_data)
                            st.success("✅ 文档已更新")
                            st.session_state[f"editing_{policy_id}"] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {str(e)}")
                
                with col_cancel:
                    if st.button("❌ 取消", key=f"cancel_{policy_id}"):
                        st.session_state[f"editing_{policy_id}"] = False
                        st.rerun()

    # 风险文档提示
    st.divider()
    st.subheader("⚠️ 即将失效的文档")

    expiring_policies = [p for p in policies if p.get('status') == "expiring_soon"]
    if expiring_policies:
        for policy in expiring_policies:
            with st.container(border=True):
                st.warning(f"📅 {policy.get('title', '无标题')} 即将于 {policy.get('expiration_date', 'N/A')} 失效")
    else:
        st.info("无即将失效的文档")


def delete_policy(policy_id):
    """删除政策"""
    try:
        dao = PolicyDAO()
        policy = dao.get_policy_by_id(policy_id)
        if policy:
            dao.delete_policy(policy_id)
            st.success(f"✅ 文档 '{policy.get('title')}' 已删除")
            st.session_state.documents_list = []
            return True
        else:
            st.error("❌ 文档不存在")
            return False
    except Exception as e:
        st.error(f"❌ 删除失败：{str(e)}")
        return False
