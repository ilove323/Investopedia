"""
政策分析页面
==========
提供单个政策分析、多个政策对比分析等功能。

核心功能：
- 影响力分析：分析政策的地域范围、影响强度、目标对象
- 相关政策推荐：基于政策类型推荐相关政策
- 政策对比：对比两个或多个政策的异同点
- 时间分析：展示政策的生效期、失效期
- 时效性管理：显示政策当前状态和风险提示

使用示例：
    import streamlit as st
    from src.pages import analysis_page
    analysis_page.show()
"""
import streamlit as st
import pandas as pd
from src.database.policy_dao import PolicyDAO
from src.business.impact_analyzer import ImpactAnalyzer
from src.business.validity_checker import ValidityChecker
from src.components.policy_card import render_policy_detail


def show():
    st.title("📈 政策分析")

    # 初始化session state
    if "selected_policies_for_compare" not in st.session_state:
        st.session_state.selected_policies_for_compare = []

    # 标签页
    tab_single, tab_compare, tab_trends = st.tabs(["📋 单个分析", "⚖️ 政策对比", "📊 趋势分析"])

    with tab_single:
        render_single_analysis()

    with tab_compare:
        render_policy_comparison()

    with tab_trends:
        render_trends_analysis()


def render_single_analysis():
    """单个政策分析"""
    st.subheader("政策影响分析")

    try:
        dao = PolicyDAO()
        policies = dao.get_policies()

        if not policies:
            st.info("暂无政策数据")
            return

        # 选择政策
        selected_policy = st.selectbox(
            "选择要分析的政策",
            options=policies,
            format_func=lambda p: f"{p.metadata.title} ({p.policy_type})"
        )

        if selected_policy:
            col_analysis, col_detail = st.columns([2, 1])

            with col_analysis:
                # 显示政策详情
                st.subheader("政策详情")
                render_policy_detail(selected_policy)

            with col_detail:
                # 显示时效性状态
                st.subheader("时效性状态")
                validity_checker = ValidityChecker()
                validity_result = validity_checker.check_policy(selected_policy)

                status_color = {
                    "ACTIVE": "🟢",
                    "EXPIRED": "🔴",
                    "EXPIRING_SOON": "🟡",
                    "UPDATED": "🔵"
                }

                st.write(f"**状态**：{status_color.get(validity_result.get('status', ''), '❓')} {validity_result.get('status', 'UNKNOWN')}")
                if validity_result.get('days_remaining'):
                    st.write(f"**剩余天数**：{validity_result.get('days_remaining')} 天")
                if validity_result.get('message'):
                    st.info(validity_result.get('message'))

            st.divider()

            # 影响分析
            st.subheader("影响分析")
            impact_analyzer = ImpactAnalyzer()
            impact_result = impact_analyzer.analyze_policy(selected_policy)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "影响范围",
                    impact_result.get("scope", "未知"),
                    delta=f"目标：{', '.join(impact_result.get('targets', []))[:30]}"
                )

            with col2:
                st.metric(
                    "影响强度",
                    impact_result.get("intensity", "未知"),
                    delta=impact_result.get("intensity_description", "")
                )

            with col3:
                st.metric(
                    "关键影响",
                    len(impact_result.get("key_impacts", [])),
                    delta="提取的要点数"
                )

            # 影响详情
            with st.expander("📍 影响详情", expanded=True):
                col_impact_left, col_impact_right = st.columns(2)

                with col_impact_left:
                    st.write("**影响范围详情**")
                    scope_details = {
                        "scope": impact_result.get("scope"),
                        "regions_affected": impact_result.get("regions_affected", []),
                        "target_groups": impact_result.get("target_groups", [])
                    }
                    for key, value in scope_details.items():
                        st.write(f"- {key}: {value}")

                with col_impact_right:
                    st.write("**关键影响点**")
                    for impact in impact_result.get("key_impacts", [])[:5]:
                        st.write(f"- {impact}")

            # 相关建议
            st.subheader("相关建议")
            suggestions = impact_result.get("suggestions", [])
            if suggestions:
                for i, suggestion in enumerate(suggestions[:5], 1):
                    st.info(f"{i}. {suggestion}")
            else:
                st.info("暂无相关建议")

    except Exception as e:
        st.error(f"分析失败：{str(e)}")


def render_policy_comparison():
    """政策对比"""
    st.subheader("政策对比分析")

    try:
        dao = PolicyDAO()
        policies = dao.get_policies()

        if len(policies) < 2:
            st.warning("需要至少2条政策才能进行对比")
            return

        # 选择要对比的政策
        col1, col2 = st.columns(2)

        with col1:
            policy1 = st.selectbox(
                "政策 1",
                options=policies,
                format_func=lambda p: p.metadata.title,
                key="compare_policy1"
            )

        with col2:
            policy2 = st.selectbox(
                "政策 2",
                options=policies,
                format_func=lambda p: p.metadata.title,
                key="compare_policy2"
            )

        if policy1 and policy2 and policy1.id != policy2.id:
            st.divider()

            # 基本信息对比
            st.subheader("基本信息对比")

            compare_data = {
                "属性": [
                    "名称",
                    "文号",
                    "发布机关",
                    "发布日期",
                    "生效日期",
                    "失效日期",
                    "政策类型",
                    "适用地区",
                    "状态"
                ],
                "政策 1": [
                    policy1.metadata.title,
                    policy1.metadata.document_number,
                    policy1.metadata.issuing_authority,
                    policy1.metadata.publish_date,
                    policy1.metadata.effective_date,
                    policy1.metadata.expiration_date,
                    policy1.policy_type,
                    policy1.metadata.region,
                    policy1.status
                ],
                "政策 2": [
                    policy2.metadata.title,
                    policy2.metadata.document_number,
                    policy2.metadata.issuing_authority,
                    policy2.metadata.publish_date,
                    policy2.metadata.effective_date,
                    policy2.metadata.expiration_date,
                    policy2.policy_type,
                    policy2.metadata.region,
                    policy2.status
                ]
            }

            df = pd.DataFrame(compare_data)
            st.dataframe(df, use_container_width=True)

            st.divider()

            # 影响分析对比
            st.subheader("影响分析对比")

            impact_analyzer = ImpactAnalyzer()
            impact1 = impact_analyzer.analyze_policy(policy1)
            impact2 = impact_analyzer.analyze_policy(policy2)

            col_impact1, col_impact2 = st.columns(2)

            with col_impact1:
                st.write(f"### {policy1.metadata.title}")
                st.metric("影响范围", impact1.get("scope", "未知"))
                st.metric("影响强度", impact1.get("intensity", "未知"))
                st.write("**关键影响**")
                for impact in impact1.get("key_impacts", [])[:3]:
                    st.write(f"- {impact}")

            with col_impact2:
                st.write(f"### {policy2.metadata.title}")
                st.metric("影响范围", impact2.get("scope", "未知"))
                st.metric("影响强度", impact2.get("intensity", "未知"))
                st.write("**关键影响**")
                for impact in impact2.get("key_impacts", [])[:3]:
                    st.write(f"- {impact}")

            st.divider()

            # 相似度分析
            st.subheader("相似度分析")

            similarity = calculate_policy_similarity(policy1, policy2, impact1, impact2)
            st.metric("相似度", f"{similarity:.1%}")

            # 相似点和差异点
            col_similar, col_diff = st.columns(2)

            with col_similar:
                st.write("**相似点**")
                st.write("- 都属于政策文件")
                if policy1.policy_type == policy2.policy_type:
                    st.write(f"- 政策类型相同：{policy1.policy_type}")
                if policy1.metadata.region == policy2.metadata.region:
                    st.write(f"- 适用地区相同：{policy1.metadata.region}")

            with col_diff:
                st.write("**差异点**")
                if policy1.policy_type != policy2.policy_type:
                    st.write(f"- 政策类型不同：{policy1.policy_type} vs {policy2.policy_type}")
                if policy1.metadata.region != policy2.metadata.region:
                    st.write(f"- 适用地区不同：{policy1.metadata.region} vs {policy2.metadata.region}")
                if impact1.get("scope") != impact2.get("scope"):
                    st.write(f"- 影响范围不同：{impact1.get('scope')} vs {impact2.get('scope')}")

    except Exception as e:
        st.error(f"对比失败：{str(e)}")


def render_trends_analysis():
    """政策趋势分析"""
    st.subheader("政策趋势分析")

    try:
        dao = PolicyDAO()
        stats = dao.get_stats()

        if not stats:
            st.info("暂无统计数据")
            return

        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总政策数", stats.get("total_count", 0))
        col2.metric("有效政策", stats.get("active_count", 0))
        col3.metric("失效政策", stats.get("expired_count", 0))
        col4.metric("平均有效期(天)", stats.get("avg_duration_days", 0))

        st.divider()

        # 政策类型分布
        st.subheader("政策类型分布")
        type_stats = stats.get("by_type", {})
        if type_stats:
            df_type = pd.DataFrame(
                list(type_stats.items()),
                columns=["政策类型", "数量"]
            )
            st.bar_chart(df_type.set_index("政策类型"))

        st.divider()

        # 政策状态分布
        st.subheader("政策状态分布")
        status_stats = stats.get("by_status", {})
        if status_stats:
            df_status = pd.DataFrame(
                list(status_stats.items()),
                columns=["状态", "数量"]
            )
            st.pie_chart(df_status.set_index("状态"))

        st.divider()

        # 地区分布
        st.subheader("地区分布")
        policies = dao.get_policies()
        region_data = {}
        for policy in policies:
            region = policy.metadata.region or "未指定"
            region_data[region] = region_data.get(region, 0) + 1

        if region_data:
            df_region = pd.DataFrame(
                list(region_data.items()),
                columns=["地区", "数量"]
            )
            st.bar_chart(df_region.set_index("地区"))

    except Exception as e:
        st.error(f"趋势分析失败：{str(e)}")


def calculate_policy_similarity(policy1, policy2, impact1, impact2):
    """计算两个政策的相似度"""
    similarity_score = 0.0

    # 政策类型相同 +20%
    if policy1.policy_type == policy2.policy_type:
        similarity_score += 0.20

    # 适用地区相同 +20%
    if policy1.metadata.region == policy2.metadata.region:
        similarity_score += 0.20

    # 影响范围相同 +15%
    if impact1.get("scope") == impact2.get("scope"):
        similarity_score += 0.15

    # 影响强度相同 +15%
    if impact1.get("intensity") == impact2.get("intensity"):
        similarity_score += 0.15

    # 目标对象有重叠 +15%
    targets1 = set(impact1.get("targets", []))
    targets2 = set(impact2.get("targets", []))
    if targets1 & targets2:
        similarity_score += 0.15

    # 发布机关相同 +15%
    if policy1.metadata.issuing_authority == policy2.metadata.issuing_authority:
        similarity_score += 0.15

    return min(similarity_score, 1.0)  # 确保不超过100%
