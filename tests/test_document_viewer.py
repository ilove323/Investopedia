"""
文档查看器测试
=============
测试PDF解析功能和文档查看器界面

测试内容：
- PDF文件检测和内容提取
- 文档切片显示功能
- 文档预览界面测试
"""
import sys
import os
import pytest

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.ragflow_client import RAGFlowClient
from src.config import get_config


class TestDocumentViewer:
    """文档查看器功能测试"""
    
    @pytest.fixture
    def ragflow_client(self):
        """RAGFlow客户端fixture"""
        from src.services.ragflow_client import get_ragflow_client
        return get_ragflow_client()
    
    def test_pdf_content_extraction(self, ragflow_client):
        """测试PDF内容提取功能"""
        print("🔍 测试PDF内容提取...")
        
        try:
            # 获取文档列表
            documents = ragflow_client.get_documents()
            print(f"📚 找到 {len(documents)} 个文档")
            
            # 查找PDF文档
            pdf_docs = [doc for doc in documents if doc.get('name', '').lower().endswith('.pdf')]
            print(f"📄 找到 {len(pdf_docs)} 个PDF文档")
            
            if pdf_docs:
                for doc in pdf_docs:
                    doc_id = doc.get('id')
                    doc_name = doc.get('name')
                    print(f"\n📖 测试文档: {doc_name}")
                    
                    # 获取文档内容
                    content = ragflow_client.get_document_content(doc_id)
                    
                    if content:
                        print(f"✅ 成功提取内容，长度: {len(content)} 字符")
                        print(f"📝 内容预览: {content[:200]}...")
                        
                        # 检查内容质量
                        if len(content) < 50:
                            print("⚠️  内容可能过短")
                        elif content.count('�') > len(content) * 0.1:
                            print("⚠️  可能存在编码问题")
                        else:
                            print("✅ 内容质量良好")
                    else:
                        print("❌ 内容提取失败")
            else:
                print("⚠️  没有找到PDF文档用于测试")
                
        except Exception as e:
            print(f"❌ PDF内容提取测试失败: {e}")
            raise
    
    def test_document_chunks(self, ragflow_client):
        """测试文档切片功能"""
        print("\n🔍 测试文档切片...")
        
        try:
            # 获取文档列表
            documents = ragflow_client.get_documents()
            
            if documents:
                doc = documents[0]  # 测试第一个文档
                doc_id = doc.get('id')
                doc_name = doc.get('name')
                print(f"📖 测试文档: {doc_name}")
                
                # 获取文档切片
                chunks = ragflow_client.get_document_chunks(doc_id)
                print(f"🧩 找到 {len(chunks)} 个切片")
                
                if chunks:
                    for i, chunk in enumerate(chunks[:3]):  # 只测试前3个切片
                        content = chunk.get('content', '')
                        keywords = chunk.get('important_keywords', [])
                        
                        print(f"\n切片 {i+1}:")
                        print(f"  📏 长度: {len(content)} 字符")
                        print(f"  🔑 关键词: {', '.join(keywords) if keywords else '无'}")
                        print(f"  📝 内容: {content[:100]}...")
                        
                    print("✅ 切片功能正常")
                else:
                    print("⚠️  文档没有切片数据")
            else:
                print("❌ 没有找到文档用于测试")
                
        except Exception as e:
            print(f"❌ 文档切片测试失败: {e}")
            raise
    
    def test_file_type_detection(self, ragflow_client):
        """测试文件类型检测"""
        print("\n🔍 测试文件类型检测...")
        
        try:
            # 获取文档列表
            documents = ragflow_client.get_documents()
            
            file_types = {}
            for doc in documents:
                doc_name = doc.get('name', '')
                if '.' in doc_name:
                    ext = doc_name.split('.')[-1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            print("📊 文件类型统计:")
            for ext, count in file_types.items():
                print(f"  .{ext}: {count} 个")
            
            # 测试不同类型的处理
            for doc in documents:
                doc_name = doc.get('name', '')
                doc_id = doc.get('id')
                
                if doc_name.lower().endswith('.pdf'):
                    print(f"\n📄 PDF文档: {doc_name}")
                    content = ragflow_client.get_document_content(doc_id)
                    if content:
                        print("  ✅ PDF解析成功")
                    else:
                        print("  ❌ PDF解析失败")
                        
                elif doc_name.lower().endswith(('.txt', '.md')):
                    print(f"\n📝 文本文档: {doc_name}")
                    content = ragflow_client.get_document_content(doc_id)
                    if content:
                        print("  ✅ 文本读取成功")
                    else:
                        print("  ❌ 文本读取失败")
            
            print("✅ 文件类型检测测试完成")
            
        except Exception as e:
            print(f"❌ 文件类型检测测试失败: {e}")
            raise


def run_tests():
    """运行所有测试"""
    print("🧪 开始文档查看器功能测试")
    print("=" * 50)
    
    try:
        # 获取RAGFlow客户端
        from src.services.ragflow_client import get_ragflow_client
        ragflow_client = get_ragflow_client()
        
        # 检查RAGFlow连接
        if not ragflow_client.check_health():
            print("❌ RAGFlow服务不可用，请检查服务状态")
            return
        
        print("✅ RAGFlow服务连接正常")
        
        # 初始化测试类并运行测试
        test_viewer = TestDocumentViewer()
        test_viewer.test_pdf_content_extraction(ragflow_client)
        test_viewer.test_document_chunks(ragflow_client) 
        test_viewer.test_file_type_detection(ragflow_client)
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        raise


if __name__ == "__main__":
    run_tests()