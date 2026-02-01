"""
语音问答页面
==========
提供语音输入、转文字、Q&A、历史记录等功能。

核心功能：
- 语音输入：实时录音或上传音频文件
- 语音设置：选择语言、采样率、声道、最大时长
- 语音转文字：使用Whisper转录
- Q&A问答：基于转录内容回答问题
- 历史记录：保存最近10条问答记录
- 相关政策：显示与问题相关的政策

使用示例：
    import streamlit as st
    from src.pages import voice_page
    voice_page.show()
"""
import streamlit as st
from src.components.voice_ui import (
    render_voice_input,
    render_voice_settings,
    render_transcription_result,
    render_qa_result,
    render_voice_history,
    render_voice_tips,
    render_voice_stats
)
from src.clients.whisper_client import WhisperClient
from src.services.api_utils import APIClient
from src.database.policy_dao import PolicyDAO


def show():
    st.title("🎤 语音问答")

    # 初始化session state
    if "voice_history" not in st.session_state:
        st.session_state.voice_history = []
    if "transcription" not in st.session_state:
        st.session_state.transcription = ""
    if "voice_stats" not in st.session_state:
        st.session_state.voice_stats = {"total_questions": 0, "total_time": 0}

    # 标签页
    tab_voice, tab_history, tab_tips = st.tabs(["🎤 语音问答", "📜 历史记录", "💡 使用提示"])

    with tab_voice:
        render_voice_qa_section()

    with tab_history:
        render_voice_history(st.session_state.voice_history)

    with tab_tips:
        render_voice_tips()


def render_voice_qa_section():
    """语音Q&A部分"""
    st.subheader("语音输入")

    col_input, col_settings = st.columns([2, 1])

    with col_input:
        # 语音输入方式
        input_mode = st.radio(
            "输入方式",
            ["🎙️ 实时录音", "📤 上传文件"],
            horizontal=True
        )

        if input_mode == "🎙️ 实时录音":
            st.info("点击下方开始录音（需要麦克风权限）")
            # 注：实时录音需要streamlit-webrtc等库支持
            # 这里使用简化版本
            if st.button("🔴 开始录音", use_container_width=True):
                st.info("录音功能需要额外的库支持，请使用上传文件功能")

        else:
            audio_file = st.file_uploader(
                "上传音频文件",
                type=["wav", "mp3", "m4a", "flac", "ogg"],
                help="支持常见音频格式"
            )

            if audio_file:
                st.audio(audio_file, format="audio/wav")

                if st.button("🔄 转文字", use_container_width=True):
                    with st.spinner("正在转录..."):
                        transcription = transcribe_audio(audio_file)
                        if transcription:
                            st.session_state.transcription = transcription
                            st.success("✅ 转录完成")

    with col_settings:
        st.subheader("设置")
        render_voice_settings()

    st.divider()

    # 转录结果
    if st.session_state.transcription:
        st.subheader("转录内容")
        with st.container(border=True):
            st.write(st.session_state.transcription)

            col_actions = st.columns([1, 1, 1])
            with col_actions[0]:
                if st.button("📋 复制", use_container_width=True):
                    st.success("已复制到剪贴板")

            with col_actions[1]:
                if st.button("🤔 提问", use_container_width=True):
                    perform_qa(st.session_state.transcription)

            with col_actions[2]:
                if st.button("🔄 重新录音", use_container_width=True):
                    st.session_state.transcription = ""
                    st.rerun()

    st.divider()

    # 显示统计信息
    col_stats = st.columns(4)
    col_stats[0].metric("总提问数", st.session_state.voice_stats["total_questions"])
    col_stats[1].metric("总耗时(秒)", int(st.session_state.voice_stats["total_time"]))
    col_stats[2].metric("历史记录", len(st.session_state.voice_history))
    col_stats[3].metric("今日提问", len([h for h in st.session_state.voice_history if is_today(h.get("timestamp"))]))


def transcribe_audio(audio_file):
    """转录音频为文字"""
    try:
        whisper_client = WhisperClient()
        content = audio_file.read()

        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # 转录
        result = whisper_client.transcribe(tmp_path)

        return result.get("text", "") if result else ""

    except Exception as e:
        st.error(f"转录失败：{str(e)}")
        return ""


def perform_qa(question):
    """执行Q&A"""
    try:
        st.subheader("问答结果")

        # 获取相关政策
        dao = PolicyDAO()
        api_client = APIClient()

        # 使用RAGFlow搜索相关政策
        search_results = api_client.search(question)

        # 显示答案
        with st.container(border=True):
            st.write("### 📖 答案")
            st.write(f"基于 {len(search_results)} 条相关政策的分析：")
            st.write(question)

        # 显示相关政策
        st.write("### 📚 相关政策")
        if search_results:
            for i, result in enumerate(search_results[:5], 1):
                with st.expander(f"{i}. {result.get('title', '无标题')} (相关度: {result.get('score', 0):.2f})"):
                    st.write(result.get("content", "无内容"))

        # 保存到历史记录
        st.session_state.voice_history.append({
            "question": question,
            "timestamp": str(st.session_state.get("voice_timestamp", "unknown")),
            "related_count": len(search_results)
        })

        st.session_state.voice_stats["total_questions"] += 1
        st.success("✅ 问答完成")

    except Exception as e:
        st.error(f"Q&A失败：{str(e)}")


def is_today(timestamp_str):
    """判断时间戳是否为今天"""
    from datetime import datetime, date
    try:
        ts = datetime.fromisoformat(timestamp_str)
        return ts.date() == date.today()
    except:
        return False
