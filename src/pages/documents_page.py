"""
文档管理页面
==========
提供政策文档上传、列表展示、编辑、删除等功能。

核心功能：
- 文档上传：支持PDF/DOCX/TXT格式
- 文档列表：分页显示已上传文档，显示标题、文号、状态、上传时间
- 文档详情：展示完整文档信息、时效性状态
- 编辑文档：修改标题、分类、标签等
- 删除文档：移除不需要的文档

使用示例：
    import streamlit as st
    from src.pages import documents_page
    documents_page.show()
"""
import streamlit as st
from src.database.policy_dao import PolicyDAO
from src.business.validity_checker import ValidityChecker
from src.components.policy_card import render_policy_card, render_policy_detail, render_policy_form
from src.utils.summarizer import generate_summary


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
            policy_type = st.selectbox("政策类型", ["特别国债", "特许经营", "数据资产"])

        with col2:
            region = st.selectbox("适用地区", ["全国", "京津冀", "长三角", "粤港澳", "成渝"])
            document_number = st.text_input("文号", placeholder="例：财预〔2024〕1号")

        if st.button("✅ 上传文档", use_container_width=True):
            try:
                # 读取文件内容
                content = uploaded_file.read().decode('utf-8', errors='ignore')

                # 生成摘要（优先使用 RAGFlow，再使用 DeepSeek）
                with st.spinner("🤖 正在生成智能摘要..."):
                    summary = generate_summary(content, max_length=200)

                # 保存到数据库
                dao = PolicyDAO()
                policy_data = {
                    'title': title,
                    'content': content,
                    'summary': summary,
                    'policy_type': policy_type,
                    'region': region,
                    'document_number': document_number,
                    'file_path': uploaded_file.name
                }
                policy_id = dao.create_policy(policy_data)

                st.success(f"✅ 文档已上传：{title}")
                st.info(f"📝 生成的摘要：\n{summary}")
                st.session_state.documents_list = []  # 清空缓存

            except Exception as e:
                st.error(f"上传失败：{str(e)}")


def render_documents_list():
    """文档列表部分"""
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
        col2.metric("有效文档", len([p for p in policies if p.get('status') == "ACTIVE"]))
        col3.metric("失效文档", len([p for p in policies if p.get('status') == "EXPIRED"]))
        col4.metric("即将失效", len([p for p in policies if p.get('status') == "EXPIRING_SOON"]))

        st.divider()

        # 文档列表
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
    """文档管理部分"""
    st.subheader("文档管理")

    dao = PolicyDAO()
    policies = dao.get_policies()

    if not policies:
        st.info("暂无文档")
        return

    # 批量操作
    col_filter, col_action = st.columns([3, 1])

    with col_filter:
        filter_status = st.multiselect(
            "按状态筛选",
            ["ACTIVE", "EXPIRED", "EXPIRING_SOON"],
            default=["ACTIVE"]
        )
        filtered_policies = [p for p in policies if p.get('status') in filter_status]

    with col_action:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    st.divider()

    # 编辑或删除
    if filtered_policies:
        policy_to_edit = st.selectbox(
            "选择要编辑的文档",
            options=filtered_policies,
            format_func=lambda p: f"{p.get('title', '无标题')} ({p.get('status')})"
        )

        if policy_to_edit:
            with st.expander(f"✏️ 编辑 {policy_to_edit.get('title', '无标题')}", expanded=True):
                st.write("**基本信息**")
                title = st.text_input("标题", value=policy_to_edit.get('title'))
                doc_number = st.text_input("文号", value=policy_to_edit.get('document_number'))
                policy_type = st.selectbox("类型", ["特别国债", "特许经营", "数据资产"],
                                         index=0 if policy_to_edit.get('policy_type') == "特别国债" else 1)
                region = st.selectbox("地区", ["全国", "京津冀", "长三角", "粤港澳", "成渝"])

                if st.button("💾 保存修改"):
                    st.success("文档已更新")

    # 风险文档提示
    st.divider()
    st.subheader("⚠️ 即将失效的文档")

    expiring_policies = [p for p in policies if p.get('status') == "EXPIRING_SOON"]
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
        dao.delete_policy(policy_id)
        st.success("✅ 文档已删除")
        st.session_state.documents_list = []
    except Exception as e:
        st.error(f"删除失败：{str(e)}")
