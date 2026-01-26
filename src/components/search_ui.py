"""
搜索UI组件
==========
提供搜索页面的各种UI组件，包括搜索栏、高级搜索面板、结果展示、过滤器、统计等。

核心组件：
- render_search_bar：搜索栏（输入框 + 搜索按钮）
- render_advanced_search_panel：高级搜索面板（政策类型、地区、状态、日期、排序）
- render_search_results：搜索结果展示（分页、卡片列表）
- render_search_filters_sidebar：侧边栏过滤器（政策类型、地区、状态、日期）
- render_search_stats：搜索统计（总数、各类型政策数等）

使用示例：
    from src.components.search_ui import render_search_bar, render_search_results

    query = render_search_bar()
    if query:
        results = search_policies(query)
        total_pages, current_page = render_search_results(results, total=100)
"""
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple, Set
import networkx as nx
from pyvis.network import Network
import tempfile
from pathlib import Path


def render_search_bar(placeholder: str = "搜索政策关键词...") -> str:
    """
    渲染搜索栏

    Args:
        placeholder: 占位符文本

    Returns:
        搜索查询字符串
    """
    cols = st.columns([4, 1])

    with cols[0]:
        query = st.text_input("🔍", placeholder=placeholder, label_visibility="collapsed")

    with cols[1]:
        search_button = st.button("搜索", use_container_width=True)

    return query if search_button else ""


def render_advanced_search_panel() -> Dict[str, Any]:
    """
    渲染高级搜索面板

    Returns:
        搜索过滤条件字典
    """
    with st.expander("🔧 高级搜索", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            policy_type = st.multiselect(
                "政策类型",
                ["special_bonds", "franchise", "data_assets"],
                default=[]
            )

            region = st.multiselect(
                "适用地区",
                ["全国", "北京", "上海", "广东", "浙江", "江苏", "四川", "湖北"],
                default=[]
            )

        with col2:
            status = st.multiselect(
                "政策状态",
                ["active", "expired", "expiring_soon", "updated"],
                default=["active"]
            )

            use_date_range = st.checkbox("使用日期范围筛选", value=False)
            date_from = None
            date_to = None

            if use_date_range:
                try:
                    date_range = st.date_input(
                        "发布日期范围",
                        value=[],
                        label_visibility="visible"
                    )
                    if isinstance(date_range, (list, tuple)) and len(date_range) >= 2:
                        date_from = date_range[0]
                        date_to = date_range[1]
                except Exception:
                    pass

        # 排序选项
        sort_by = st.selectbox(
            "排序方式",
            ["最新发布", "标题（A-Z）", "相关度最高"],
            index=0
        )

        return {
            'policy_type': policy_type[0] if policy_type else None,
            'region': region[0] if region else None,
            'status': status[0] if status else None,
            'date_from': date_from,
            'date_to': date_to,
            'sort_by': sort_by
        }


def render_search_results(results: List[Dict[str, Any]], total: int,
                         page: int = 1, page_size: int = 10, full_graph=None) -> Tuple[int, int]:
    """
    渲染搜索结果

    Args:
        results: 搜索结果列表
        total: 总数
        page: 当前页码
        page_size: 每页数量
        full_graph: 完整的PolicyGraph对象（用于生成子图谱）

    Returns:
        (总页数, 当前页码)
    """
    if not results:
        st.info("未找到匹配的政策")
        return 1, 1

    # 显示结果统计
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(f"找到 **{total}** 个结果")
    with col2:
        st.write(f"第 **{page}** 页")
    with col3:
        total_pages = (total + page_size - 1) // page_size
        st.write(f"共 **{total_pages}** 页")

    st.divider()

    # 显示结果
    for idx, result in enumerate(results, start=1):
        # 确保result是字典
        if not isinstance(result, dict):
            continue
            
        with st.container():
            col1, col2 = st.columns([5, 1])

            with col1:
                st.subheader(f"{idx}. {result.get('title', '未知标题')}")

                # 摘要和元数据
                meta_info = []
                if result.get('document_number'):
                    meta_info.append(f"📄 {result['document_number']}")
                if result.get('issuing_authority'):
                    meta_info.append(f"🏛️ {result['issuing_authority']}")
                if result.get('publish_date'):
                    meta_info.append(f"📅 {result['publish_date']}")

                if meta_info:
                    st.caption(" | ".join(meta_info))

                # 摘要
                summary = result.get('summary', result.get('content', ''))
                if isinstance(summary, str):
                    summary = summary[:200] + '...' if len(summary) > 200 else summary
                    st.write(summary)

                # 标签
                if result.get('tags'):
                    tag_list = result['tags']
                    if isinstance(tag_list, list):
                        tag_str = " ".join([f"🔹 {tag.get('name', 'Tag') if isinstance(tag, dict) else tag}" for tag in tag_list[:3]])
                        st.caption(tag_str)

            with col2:
                # 相关度分数（如果有）
                if result.get('score'):
                    st.metric("相关度", f"{result['score']:.1%}")

                # 查看按钮
                if result.get('id'):
                    if st.button("查看", key=f"view_{result['id']}", use_container_width=True):
                        st.session_state.selected_policy = result['id']
            
            # 嵌入式知识图谱
            if full_graph and full_graph.get_node_count() > 0:
                with st.expander("🔗 知识图谱", expanded=False):
                    # 提取实体
                    entities = extract_entities_from_policy(result)
                    
                    if entities:
                        # 模糊匹配到节点
                        matched_node_ids = fuzzy_match_entities_to_nodes(entities, full_graph)
                        
                        if matched_node_ids:
                            st.caption(f"✅ 匹配到 {len(matched_node_ids)} 个实体节点")
                            
                            # 构建子图
                            subgraph = build_subgraph_for_entities(full_graph, matched_node_ids)
                            
                            if subgraph.get_node_count() > 0:
                                st.caption(f"📊 图谱包含 {subgraph.get_node_count()} 个节点，{len(subgraph.edges)} 条边")
                                
                                # 渲染高亮图谱
                                render_highlighted_graph(subgraph, matched_node_ids)
                            else:
                                st.warning("暂无图谱数据")
                        else:
                            st.info("暂无图谱数据")
                    else:
                        st.info("未提取到实体信息")

        st.divider()

    # 分页控制
    col1, col2, col3, col4, col5 = st.columns(5)
    total_pages = (total + page_size - 1) // page_size

    with col1:
        if st.button("⬅️ 首页"):
            return total_pages, 1

    with col2:
        if st.button("⬅️ 上一页"):
            return total_pages, max(1, page - 1)

    with col3:
        current_page = st.number_input("页码", min_value=1, max_value=total_pages, value=page)

    with col4:
        if st.button("下一页 ➡️"):
            return total_pages, min(total_pages, page + 1)

    with col5:
        if st.button("末页 ➡️"):
            return total_pages, total_pages

    return total_pages, current_page


def render_search_filters_sidebar() -> Dict[str, Any]:
    """
    在侧边栏渲染搜索过滤器

    Returns:
        过滤条件字典，包含policy_type, region, status, date_from, date_to
    """
    filters = {
        "policy_type": None,
        "region": None,
        "status": None,
        "date_from": None,
        "date_to": None
    }

    with st.sidebar:
        st.subheader("📊 搜索过滤")

        # 政策类型
        st.write("**政策类型**")
        selected_types = []
        if st.checkbox("特别国债", key="type_special_bonds"):
            selected_types.append('special_bonds')
        if st.checkbox("特许经营", key="type_franchise"):
            selected_types.append('franchise')
        if st.checkbox("数据资产", key="type_data_assets"):
            selected_types.append('data_assets')
        
        if selected_types:
            filters['policy_type'] = selected_types[0]  # 取第一个作为主要过滤

        st.divider()

        # 地区过滤
        st.write("**地区**")
        regions = st.multiselect(
            "选择地区",
            ["全国", "北京", "上海", "广东", "浙江"],
            key="region_filter",
            label_visibility="collapsed"
        )
        if regions:
            filters['region'] = regions[0]  # 取第一个作为主要过滤

        st.divider()

        # 状态过滤
        st.write("**状态**")
        statuses = []
        if st.checkbox("有效", value=True, key="status_active"):
            statuses.append('active')
        if st.checkbox("失效", key="status_expired"):
            statuses.append('expired')
        if st.checkbox("即将失效", key="status_expiring"):
            statuses.append('expiring_soon')

        if statuses:
            filters['status'] = statuses[0]  # 取第一个作为主要过滤

        st.divider()

        # 日期范围
        st.write("**发布日期**")
        try:
            date_range = st.date_input("选择日期范围", value=[], key="date_range")
            if isinstance(date_range, (list, tuple)) and len(date_range) >= 2:
                filters['date_from'] = date_range[0]
                filters['date_to'] = date_range[1]
        except Exception:
            pass

        return filters


def render_search_stats(results: List[Dict[str, Any]]) -> None:
    """
    渲染搜索统计

    Args:
        results: 搜索结果列表
    """
    if not results:
        return
    
    # 统计各政策类型的数量
    stats_by_type = {}
    for r in results:
        policy_type = r.get('policy_type', 'unknown')
        stats_by_type[policy_type] = stats_by_type.get(policy_type, 0) + 1
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("搜索结果", len(results))

    with col2:
        special_bonds = stats_by_type.get('special_bonds', 0)
        st.metric("特别国债", special_bonds)

    with col3:
        franchise = stats_by_type.get('franchise', 0)
        st.metric("特许经营", franchise)

    with col4:
        data_assets = stats_by_type.get('data_assets', 0)
        st.metric("数据资产", data_assets)

def extract_entities_from_policy(policy: Dict[str, Any]) -> List[str]:
    """
    从政策对象中提取关键实体
    
    Args:
        policy: 政策字典对象
    
    Returns:
        实体名称列表
    """
    entities = []
    
    # 提取政策标题
    if policy.get('title'):
        entities.append(policy['title'])
    
    # 提取发文机关
    if policy.get('issuing_authority'):
        entities.append(policy['issuing_authority'])
    
    # 提取地区
    if policy.get('region'):
        entities.append(policy['region'])
    
    # 提取标签中的关键词
    if policy.get('tags'):
        tags = policy['tags']
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get('name')
                    if tag_name:
                        entities.append(tag_name)
                elif isinstance(tag, str):
                    entities.append(tag)
    
    return entities


def fuzzy_match_entities_to_nodes(entities: List[str], graph) -> List[str]:
    """
    使用模糊匹配将实体映射到图谱节点ID
    
    三级匹配策略：
    1. 精确匹配
    2. 去前缀匹配
    3. 包含匹配
    
    Args:
        entities: 实体名称列表
        graph: PolicyGraph对象
    
    Returns:
        匹配到的节点ID列表
    """
    matched_node_ids = set()
    
    # 前缀清理列表
    prefixes_to_remove = ["中华人民共和国", "国家", "省", "市", "自治区"]
    
    def clean_prefix(text: str) -> str:
        """移除常见前缀"""
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):]
        return text
    
    # 遍历每个实体
    for entity in entities:
        if not entity:
            continue
        
        entity_lower = entity.lower()
        entity_cleaned = clean_prefix(entity).lower()
        
        # 遍历图谱中所有节点
        for node_id, node in graph.nodes.items():
            label = node.label
            label_lower = label.lower()
            label_cleaned = clean_prefix(label).lower()
            
            # 策略1：精确匹配
            if entity_lower == label_lower:
                matched_node_ids.add(node_id)
                continue
            
            # 策略2：去前缀匹配
            if entity_cleaned == label_cleaned:
                matched_node_ids.add(node_id)
                continue
            
            # 策略3：包含匹配
            if entity_lower in label_lower or label_lower in entity_lower:
                matched_node_ids.add(node_id)
                continue
    
    return list(matched_node_ids)


def build_subgraph_for_entities(graph, entity_node_ids: List[str], max_nodes: int = 50):
    """
    为实体节点构建子图谱（包含1跳邻居）
    
    节点选择优先级：
    1. 实体节点（全保留）
    2. 高度数邻居（度数降序）
    3. 随机邻居
    
    Args:
        graph: PolicyGraph对象
        entity_node_ids: 实体节点ID列表
        max_nodes: 最大节点数
    
    Returns:
        子图 PolicyGraph对象
    """
    from src.models.graph import PolicyGraph
    
    if not graph or not entity_node_ids:
        return PolicyGraph()
    
    subgraph = PolicyGraph()
    nx_graph = graph.get_nx_graph()
    
    # 1. 添加所有实体节点
    for node_id in entity_node_ids:
        node = graph.get_node(node_id)
        if node:
            subgraph.add_node(node)
    
    # 2. 收集1跳邻居
    neighbors = set()
    for entity_id in entity_node_ids:
        if entity_id in nx_graph:
            neighbors.update(nx_graph.neighbors(entity_id))
    
    # 移除已经在实体节点中的
    neighbors = neighbors - set(entity_node_ids)
    
    # 3. 如果邻居数量+实体数量 > max_nodes，需要筛选
    remaining_slots = max_nodes - len(entity_node_ids)
    
    if len(neighbors) > remaining_slots:
        # 按度数排序邻居（高度数优先）
        neighbor_degrees = [(n, nx_graph.degree(n)) for n in neighbors]
        neighbor_degrees.sort(key=lambda x: x[1], reverse=True)
        neighbors = [n for n, _ in neighbor_degrees[:remaining_slots]]
    
    # 4. 添加邻居节点
    for neighbor_id in neighbors:
        node = graph.get_node(neighbor_id)
        if node:
            subgraph.add_node(node)
    
    # 5. 添加边（只添加子图中存在的边）
    for edge in graph.edges:
        if edge.source_id in subgraph.nodes and edge.target_id in subgraph.nodes:
            subgraph.add_edge(edge)
    
    return subgraph


def render_highlighted_graph(subgraph, highlighted_node_ids: List[str]) -> None:
    """
    渲染高亮图谱
    
    高亮节点：橙色(#FF8C00)/大号(size=30)
    普通节点：蓝色(#4169E1)/小号(size=15)
    
    Args:
        subgraph: PolicyGraph对象
        highlighted_node_ids: 要高亮显示的节点ID列表
    """
    if not subgraph or subgraph.get_node_count() == 0:
        st.warning("暂无图谱数据")
        return
    
    # 显示图例
    st.info("""
    🔍 **图谱说明：**
    • 🟠 橙色节点 - 从搜索结果中识别的实体（政策、机构、地区等）
    • 🔵 蓝色节点 - 与实体相关的节点（1跳关系）
    • 图谱最多显示50个节点，优先展示实体节点及其直接关联
    """)
    
    # 创建Pyvis网络图
    net = Network(
        height="500px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        directed=False
    )
    
    # 添加节点
    highlighted_set = set(highlighted_node_ids)
    
    for node_id, node in subgraph.nodes.items():
        is_highlighted = node_id in highlighted_set
        
        # 设置节点样式
        color = "#FF8C00" if is_highlighted else "#4169E1"  # 橙色/蓝色
        size = 30 if is_highlighted else 15  # 大/小
        
        net.add_node(
            node_id,
            label=node.label,
            color=color,
            size=size,
            title=f"{node.node_type.value}: {node.label}"
        )
    
    # 添加边
    for edge in subgraph.edges:
        net.add_edge(
            edge.source_id,
            edge.target_id,
            title=edge.label or edge.relation_type.value,
            color="#888888"
        )
    
    # 设置物理引擎
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {
                "iterations": 100
            }
        }
    }
    """)
    
    # 保存并显示
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
            html_path = f.name
            net.save_graph(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        st.components.v1.html(html_content, height=520, scrolling=True)
        
        # 清理临时文件
        Path(html_path).unlink(missing_ok=True)
        
    except Exception as e:
        st.error(f"图谱渲染失败: {str(e)}")