"""
政策搜索页面
==========
提供政策关键词搜索、高级筛选、结果展示等功能。

核心功能：
- 搜索栏：支持关键词输入
- 高级筛选：按政策类型、地区、状态、日期范围筛选
- 结果展示：分页显示搜索结果
- 过滤器：侧边栏快速筛选

使用示例：
    import streamlit as st
    from src.pages import search_page
    search_page.show()
"""
import streamlit as st
from src.components.search_ui import (
    render_search_bar,
    render_advanced_search_panel,
    render_search_results,
    render_search_filters_sidebar,
    render_search_stats
)
from src.database.policy_dao import PolicyDAO


def show():
    """显示搜索页面 - 聊天式布局"""
    
    # 初始化session state
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "search_filters" not in st.session_state:
        st.session_state.search_filters = {
            "policy_type": None,
            "region": None,
            "status": None,
            "date_from": None,
            "date_to": None
        }
    
    # 初始化完整图谱缓存
    if "full_graph" not in st.session_state:
        st.session_state.full_graph = None

    # 顶部标题栏 - 简洁设计
    col1, col2, col3 = st.columns([1, 8, 1])
    with col1:
        st.markdown("# 🔍")
    with col2:
        st.title("政策智能搜索")
    with col3:
        # 清空历史按钮（小图标）
        if st.session_state.search_history:
            if st.button("🗑️", help="清空搜索历史"):
                st.session_state.search_history = []
                st.rerun()
    
    st.divider()
    
    # 搜索历史显示区（聊天式）
    if st.session_state.search_history:
        st.markdown("### 💬 搜索对话")
        search_container = st.container()
        with search_container:
            for idx, history_item in enumerate(st.session_state.search_history):
                # 用户查询（右对齐）
                with st.chat_message("user"):
                    st.write(f"🔍 {history_item['query']}")
                    if history_item.get('filters'):
                        filter_text = []
                        if history_item['filters'].get('policy_type'):
                            filter_text.append(f"类型:{history_item['filters']['policy_type']}")
                        if history_item['filters'].get('region'):
                            filter_text.append(f"地区:{history_item['filters']['region']}")
                        if filter_text:
                            st.caption(" | ".join(filter_text))
                
                # 搜索结果（左对齐）
                with st.chat_message("assistant"):
                    result_count = history_item.get('result_count', 0)
                    st.write(f"📊 找到 **{result_count}** 条相关政策")
                    
                    # 显示前3条结果预览
                    if history_item.get('results'):
                        for i, result in enumerate(history_item['results'][:3]):
                            with st.expander(f"📄 {result.get('title', '未知标题')}", expanded=False):
                                # 基本信息
                                if result.get('issuing_authority'):
                                    st.caption(f"🏛️ {result['issuing_authority']}")
                                if result.get('publish_date'):
                                    st.caption(f"📅 {result['publish_date']}")
                                summary = result.get('summary', result.get('content', ''))
                                if summary:
                                    summary_text = summary[:200] + '...' if len(summary) > 200 else summary
                                    st.write(summary_text)
                                
                                # 嵌入式知识图谱
                                if st.session_state.full_graph and st.session_state.full_graph.get_node_count() > 0:
                                    from src.components.search_ui import (
                                        extract_entities_from_policy,
                                        fuzzy_match_entities_to_nodes,
                                        build_subgraph_for_entities,
                                        render_highlighted_graph
                                    )
                                    
                                    with st.expander("🔗 知识图谱", expanded=False):
                                        # 提取实体
                                        entities = extract_entities_from_policy(result)
                                        
                                        if entities:
                                            # 模糊匹配到节点
                                            matched_node_ids = fuzzy_match_entities_to_nodes(entities, st.session_state.full_graph)
                                            
                                            if matched_node_ids:
                                                st.caption(f"✅ 匹配到 {len(matched_node_ids)} 个实体节点")
                                                
                                                # 构建子图
                                                subgraph = build_subgraph_for_entities(st.session_state.full_graph, matched_node_ids)
                                                
                                                if subgraph.get_node_count() > 0:
                                                    st.caption(f"📊 图谱包含 {subgraph.get_node_count()} 个节点，{len(subgraph.edges)} 条边")
                                                    
                                                    # 渲染高亮图谱
                                                    render_highlighted_graph(subgraph, matched_node_ids)
                                                else:
                                                    st.warning("暂无图谱数据")
                                            else:
                                                st.info("暂无匹配的图谱节点")
                                        else:
                                            st.info("未提取到实体信息")
                        
                        if result_count > 3:
                            st.caption(f"... 还有 {result_count - 3} 条结果")
        
        st.divider()
    
    # 搜索输入区 - 居中大输入框
    st.markdown("### 🔎 开始搜索")
    st.write("")  # 添加间距
    
    # 使用更合理的比例
    col_left, col_input, col_button, col_right = st.columns([1, 6, 1.5, 1])
    
    with col_input:
        query_input = st.text_input(
            "搜索",
            value="",
            placeholder="例如：特别国债的发行条件是什么？专项债用途有哪些限制？",
            label_visibility="collapsed",
            key="search_input_box"
        )
    
    with col_button:
        st.write("")  # 对齐
        search_button = st.button("🔍 搜索", use_container_width=True, type="primary")
    
    # 高级筛选（收起状态）
    with st.expander("▶ 高级筛选", expanded=False):
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            # 政策类型映射
            policy_type_map = {
                "全部": None,
                "专项债券": "special_bonds",
                "特许经营": "franchise",
                "数据资产": "data_assets"
            }
            policy_type_display = st.selectbox(
                "政策类型",
                list(policy_type_map.keys()),
                index=0
            )
            policy_type = policy_type_map[policy_type_display]
        
        with filter_col2:
            region = st.selectbox(
                "适用地区",
                [
                    "全部", "全国",
                    # 直辖市
                    "北京", "上海", "天津", "重庆",
                    # 省份（按拼音排序）
                    "安徽", "福建", "甘肃", "广东", "贵州", "海南", "河北", "河南", 
                    "黑龙江", "湖北", "湖南", "吉林", "江苏", "江西", "辽宁", "青海", 
                    "山东", "山西", "陕西", "四川", "台湾", "云南", "浙江",
                    # 自治区
                    "广西", "内蒙古", "宁夏", "西藏", "新疆",
                    # 特别行政区
                    "香港", "澳门"
                ],
                index=0
            )
        
        with filter_col3:
            # 政策状态映射
            status_map = {
                "全部": None,
                "生效中": "active",
                "已失效": "expired",
                "即将到期": "expiring_soon"
            }
            status_display = st.selectbox(
                "政策状态",
                list(status_map.keys()),
                index=0
            )
            status = status_map[status_display]
        
        # 更新筛选条件
        st.session_state.search_filters = {
            'policy_type': policy_type,
            'region': None if region == "全部" else region,
            'status': status
        }
    
    # 执行搜索
    if search_button and query_input:
        with st.spinner("🔍 正在搜索相关政策..."):
            st.session_state.search_query = query_input
            perform_search()
            
            # 自动加载图谱（如果还未加载）
            if st.session_state.full_graph is None:
                with st.spinner("正在加载知识图谱..."):
                    # 从数据库加载图谱
                    from src.services.hybrid_retriever import get_hybrid_retriever
                    retriever = get_hybrid_retriever()
                    retriever.initialize_graph()
                    st.session_state.full_graph = retriever.graph
            
            # 添加到搜索历史
            st.session_state.search_history.append({
                'query': query_input,
                'filters': st.session_state.search_filters.copy(),
                'result_count': len(st.session_state.search_results),
                'results': st.session_state.search_results[:10]  # 只保存前10条
            })
            
            # 清空输入框
            st.rerun()


def perform_search():
    """执行搜索并更新结果"""
    try:
        dao = PolicyDAO()
        query = st.session_state.search_query
        filters = st.session_state.search_filters

        # 获取所有政策
        results = dao.get_policies()

        # 应用过滤条件
        if filters.get("policy_type"):
            results = [p for p in results if p.get('policy_type') == filters.get("policy_type")]

        if filters.get("status"):
            results = [p for p in results if p.get('status') == filters.get("status")]

        if filters.get("region"):
            results = [p for p in results if p.get('region') == filters.get("region")]

        # 关键词过滤
        if query:
            results = [
                p for p in results
                if query.lower() in p.get('title', '').lower()
                or query.lower() in p.get('summary', '').lower()
                or query.lower() in p.get('content', '').lower()
            ]

        st.session_state.search_results = results
        st.session_state.current_page = 0

    except Exception as e:
        st.error(f"搜索失败: {str(e)}")
        st.session_state.search_results = []
