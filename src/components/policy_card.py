"""
政策卡片组件
==========
提供政策展示的各种UI组件，包括卡片、详情页、列表、编辑表单等。

核心组件：
- render_policy_card：政策卡片（简洁展示）- 标题、文号、机关、日期、摘要、标签、状态、操作按钮
- render_policy_detail：政策详情页面 - 完整展示所有政策信息，包括时效性分析、相关政策等
- render_policy_list：政策列表 - 多个卡片的列表展示
- render_policy_form：政策编辑表单 - 用于创建或编辑政策

功能特性：
- 实时状态显示（有效、失效、即将失效、已更新）
- 时效性分析（集成ValidityChecker）
- 相关政策链接（集成PolicyDAO）
- 支持回调函数（详情、编辑、删除）
- 支持编辑表单提交

使用示例：
    from src.components.policy_card import render_policy_card, render_policy_detail

    # 显示卡片
    render_policy_card(policy_data, on_click_details=show_details)

    # 显示详情
    render_policy_detail(policy_data)
"""
import streamlit as st
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from src.database.policy_dao import get_policy_dao
from src.business.validity_checker import get_validity_checker


def render_policy_card(policy: Dict[str, Any], on_click_details: Optional[Callable] = None,
                      on_click_edit: Optional[Callable] = None,
                      on_click_delete: Optional[Callable] = None) -> None:
    """
    渲染政策卡片

    Args:
        policy: 政策数据字典
        on_click_details: 查看详情的回调函数
        on_click_edit: 编辑的回调函数
        on_click_delete: 删除的回调函数
    """
    with st.container():
        # 使用列布局
        col1, col2 = st.columns([3, 1])

        with col1:
            # 标题
            st.subheader(policy.get('title', '未知标题'))

            # 基本信息
            info_cols = st.columns(3)

            with info_cols[0]:
                st.caption("📄 文号")
                st.write(policy.get('document_number', 'N/A'))

            with info_cols[1]:
                st.caption("🏛️ 发文机关")
                st.write(policy.get('issuing_authority', 'N/A'))

            with info_cols[2]:
                st.caption("📅 发布日期")
                st.write(policy.get('publish_date', 'N/A'))

            # 摘要
            st.caption("📝 摘要")
            summary = policy.get('summary') or policy.get('content', '')
            if isinstance(summary, str):
                summary = summary[:200] + '...' if len(summary) > 200 else summary
            st.write(summary)

            # 标签
            if policy.get('tags'):
                st.caption("🏷️ 标签")
                tag_cols = st.columns(min(4, len(policy['tags'])))
                for idx, tag in enumerate(policy['tags'][:4]):
                    with tag_cols[idx % len(tag_cols)]:
                        st.write(f"🔹 {tag.get('name', 'Tag')}")

        with col2:
            # 状态标识
            status = policy.get('status', 'active')
            status_map = {
                'active': ('✅ 有效', 'info'),
                'expired': ('❌ 失效', 'error'),
                'expiring_soon': ('⚠️ 即将失效', 'warning'),
                'updated': ('🔄 已更新', 'info')
            }

            status_label, status_type = status_map.get(status, ('❓ 未知', 'info'))
            st.write(status_label)

            # 政策类型
            st.caption("分类")
            policy_type = policy.get('policy_type', 'unknown')
            type_map = {
                'special_bonds': '专项债',
                'franchise': '特许经营',
                'data_assets': '数据资产'
            }
            st.write(type_map.get(policy_type, policy_type))

            # 适用地区
            st.caption("地区")
            st.write(policy.get('region', '全国'))

        # 操作按钮
        st.divider()
        btn_cols = st.columns(3)

        with btn_cols[0]:
            if st.button("📖 详情", key=f"details_{policy['id']}", use_container_width=True):
                if on_click_details:
                    on_click_details(policy['id'])
                else:
                    st.session_state.selected_policy = policy['id']

        with btn_cols[1]:
            if st.button("✏️ 编辑", key=f"edit_{policy['id']}", use_container_width=True):
                if on_click_edit:
                    on_click_edit(policy['id'])

        with btn_cols[2]:
            if st.button("🗑️ 删除", key=f"delete_{policy['id']}", use_container_width=True):
                if on_click_delete:
                    on_click_delete(policy['id'])


def render_policy_detail(policy: Dict[str, Any]) -> None:
    """
    渲染政策详情页面

    Args:
        policy: 政策数据字典
    """
    st.title(policy.get('title', '政策详情'))

    # 基本信息
    with st.expander("📋 基本信息", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**文号：** {policy.get('document_number', 'N/A')}")
            st.write(f"**发文机关：** {policy.get('issuing_authority', 'N/A')}")
            st.write(f"**发布日期：** {policy.get('publish_date', 'N/A')}")

        with col2:
            st.write(f"**生效日期：** {policy.get('effective_date', 'N/A')}")
            st.write(f"**失效日期：** {policy.get('expiration_date', 'N/A')}")
            st.write(f"**适用地区：** {policy.get('region', '全国')}")

    # 时效性分析
    with st.expander("⏱️ 时效性分析"):
        try:
            checker = get_validity_checker()
            result = checker.check_policy(policy['id'])

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**状态：** {result.get('status', 'unknown')}")
            with col2:
                days = result.get('days_to_expiration', -1)
                if days >= 0:
                    st.write(f"**天数：** 还有 {days} 天")
                else:
                    st.write(f"**天数：** 长期有效")

            st.info(result.get('message', '无法获取时效信息'))

        except Exception as e:
            st.warning(f"时效性分析失败: {str(e)}")

    # 政策内容
    with st.expander("📄 完整内容", expanded=False):
        content = policy.get('content', '')
        if content:
            st.write(content)
        else:
            st.info("暂无完整内容")

    # 标签
    with st.expander("🏷️ 标签"):
        tags = policy.get('tags', [])
        if tags:
            tag_cols = st.columns(4)
            for idx, tag in enumerate(tags):
                with tag_cols[idx % 4]:
                    st.write(f"🔹 {tag.get('name', 'Tag')}")
                    if tag.get('confidence'):
                        st.caption(f"置信度: {tag['confidence']:.1%}")
        else:
            st.info("暂无标签")

    # 相关政策
    with st.expander("🔗 相关政策"):
        try:
            dao = get_policy_dao()
            relations = dao.get_policy_relations(policy['id'], as_source=True)

            if relations:
                for relation in relations:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"➡️ {relation.get('target_title', 'N/A')}")
                        st.caption(f"关系: {relation.get('relation_type', 'N/A')}")
                    with col2:
                        if st.button("查看", key=f"related_{relation['target_policy_id']}"):
                            st.session_state.selected_policy = relation['target_policy_id']
                            st.rerun()
            else:
                st.info("暂无相关政策")

        except Exception as e:
            st.warning(f"获取相关政策失败: {str(e)}")


def render_policy_list(policies: list, columns: int = 1) -> None:
    """
    渲染政策列表

    Args:
        policies: 政策列表
        columns: 列数
    """
    if not policies:
        st.info("暂无政策数据")
        return

    for idx, policy in enumerate(policies):
        with st.container():
            render_policy_card(policy)
            if idx < len(policies) - 1:
                st.divider()


def render_policy_form(policy: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    渲染政策编辑表单

    Args:
        policy: 已有的政策数据（用于编辑）

    Returns:
        表单数据
    """
    with st.form("policy_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("标题", value=policy.get('title', '') if policy else '')
            document_number = st.text_input("文号", value=policy.get('document_number', '') if policy else '')
            issuing_authority = st.text_input("发文机关", value=policy.get('issuing_authority', '') if policy else '')

        with col2:
            publish_date = st.date_input("发布日期")
            effective_date = st.date_input("生效日期")
            expiration_date = st.date_input("失效日期")

        policy_type = st.selectbox(
            "政策类型",
            ["special_bonds", "franchise", "data_assets"],
            index=0
        )

        region = st.text_input("适用地区", value=policy.get('region', '全国') if policy else '全国')

        content = st.text_area("政策内容", value=policy.get('content', '') if policy else '', height=200)

        submitted = st.form_submit_button("保存", use_container_width=True)

        if submitted:
            if not title or not content:
                st.error("标题和内容不能为空")
                return None

            return {
                'title': title,
                'document_number': document_number,
                'issuing_authority': issuing_authority,
                'publish_date': publish_date,
                'effective_date': effective_date,
                'expiration_date': expiration_date,
                'policy_type': policy_type,
                'region': region,
                'content': content
            }

        return None
