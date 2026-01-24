"""
语音UI组件
"""
import streamlit as st
from typing import Optional, Dict, Any
from pathlib import Path


def render_voice_input() -> Optional[Dict[str, Any]]:
    """
    渲染语音输入组件

    Returns:
        输入数据字典或None
    """
    st.subheader("🎤 语音输入")

    # 输入方式选择
    input_method = st.radio(
        "选择输入方式",
        ["实时录音", "上传音频文件"],
        horizontal=True
    )

    if input_method == "实时录音":
        st.info("实时录音功能需要浏览器支持")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎙️ 开始录音", use_container_width=True):
                st.session_state.recording = True
                st.write("录音中...")

        with col2:
            if st.button("⏹️ 停止录音", use_container_width=True):
                st.session_state.recording = False
                st.success("录音已保存")

    else:
        # 文件上传
        audio_file = st.file_uploader(
            "上传音频文件",
            type=["wav", "mp3", "m4a", "flac", "ogg"],
            help="支持格式: WAV, MP3, M4A, FLAC, OGG"
        )

        if audio_file:
            return {
                'type': 'file',
                'file': audio_file,
                'name': audio_file.name
            }

    return None


def render_voice_settings() -> Dict[str, Any]:
    """
    渲染语音设置

    Returns:
        设置字典
    """
    with st.expander("⚙️ 语音设置", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            language = st.selectbox(
                "语言",
                ["中文", "English", "日本語"],
                index=0
            )

            sample_rate = st.select_slider(
                "采样率",
                options=[8000, 16000, 22050, 44100],
                value=16000
            )

        with col2:
            channels = st.radio(
                "声道",
                [1, 2],
                index=0,
                horizontal=True
            )

            max_duration = st.slider(
                "最大时长 (秒)",
                min_value=30,
                max_value=600,
                value=300,
                step=30
            )

        return {
            'language': language,
            'sample_rate': sample_rate,
            'channels': channels,
            'max_duration': max_duration
        }


def render_transcription_result(result: Dict[str, Any]) -> None:
    """
    渲染转写结果

    Args:
        result: 转写结果
    """
    st.subheader("📝 转写结果")

    # 识别的文本
    with st.container():
        st.write("**识别的文本：**")
        text = result.get('text', result.get('transcript', ''))

        if text:
            # 在可编辑的文本框中显示
            recognized_text = st.text_area(
                "识别文本",
                value=text,
                height=100,
                label_visibility="collapsed"
            )

            # 复制按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📋 复制文本", use_container_width=True):
                    st.success("已复制到剪贴板")

            with col2:
                if st.button("🎙️ 重新录音", use_container_width=True):
                    st.session_state.transcription = None
                    st.rerun()

            with col3:
                if st.button("➡️ 继续", use_container_width=True):
                    st.session_state.proceed_with_text = recognized_text

        else:
            st.warning("未识别到任何文本")

    # 分段信息（如果有）
    segments = result.get('segments', [])
    if segments:
        with st.expander("⏱️ 分段信息", expanded=False):
            for segment in segments[:5]:  # 显示前5个分段
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(segment.get('text', ''))

                with col2:
                    start = segment.get('start', 0)
                    end = segment.get('end', 0)
                    st.caption(f"{start:.1f}s - {end:.1f}s")


def render_qa_result(result: Dict[str, Any]) -> None:
    """
    渲染问答结果

    Args:
        result: 问答结果
    """
    st.subheader("💡 答案")

    if 'answer' in result:
        st.success(result['answer'])
    elif 'response' in result:
        st.success(result['response'])
    else:
        st.info("暂无答案")

    # 相关政策推荐
    if result.get('policies'):
        st.subheader("📄 相关政策")

        for policy in result['policies'][:3]:
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"**{policy.get('title', 'N/A')}**")
                    if policy.get('summary'):
                        st.caption(policy['summary'][:100] + "...")

                with col2:
                    if st.button("查看", key=f"policy_{policy.get('id')}"):
                        st.session_state.selected_policy = policy.get('id')

                st.divider()


def render_voice_history() -> None:
    """渲染语音问答历史"""
    with st.expander("📜 历史记录", expanded=False):
        if 'voice_history' in st.session_state and st.session_state.voice_history:
            for idx, item in enumerate(st.session_state.voice_history[-10:], 1):
                with st.container():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"{idx}. {item.get('question', 'N/A')}")

                    with col2:
                        if st.button("重复", key=f"repeat_{idx}"):
                            st.session_state.selected_query = item.get('question')

                    st.divider()
        else:
            st.info("暂无历史记录")


def render_voice_tips() -> None:
    """显示语音使用提示"""
    with st.expander("💡 使用提示", expanded=False):
        tips = """
        ### 语音问答使用建议

        1. **清晰表达**：
           - 说话清晰缓慢，避免口音
           - 完整表达问题，如"查询专项债的发行管理政策"

        2. **语言选择**：
           - 中文识别准确度最高
           - 可以混合使用中英文

        3. **最佳实践**：
           - 在安静的环境下使用
           - 避免背景噪音
           - 使用标准普通话或方言清晰的表达

        4. **常见问题**：
           - 如果识别不准确，请尝试重新录音
           - 可以编辑识别的文本后继续提问
           - 长时间录音可能超时，建议分段提问
        """
        st.markdown(tips)


def render_voice_stats() -> None:
    """显示语音统计信息"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总提问数", 0)

    with col2:
        st.metric("成功率", "0%")

    with col3:
        st.metric("平均耗时", "0s")

    with col4:
        st.metric("上次使用", "从未")
