"""
政策数据模型
==========
定义政策相关的数据结构，包括政策元数据、内容、类型、状态等。

核心类：
- PolicyType：政策类型枚举（专项债、特许经营、数据资产）
- PolicyStatus：政策状态枚举（活跃、过期、更新、即将过期）
- PolicyMetadata：政策元数据（标题、文号、机关、日期、地区等）
- PolicyContent：政策内容（全文和摘要）
- Policy：完整的政策对象

使用示例：
    from src.models.policy import Policy, PolicyMetadata, PolicyContent, PolicyType, PolicyStatus

    metadata = PolicyMetadata(title='某政策', document_number='财预〔2024〕1号')
    content = PolicyContent(content='政策全文...', summary='摘要...')
    policy = Policy(metadata=metadata, content=content, policy_type=PolicyType.SPECIAL_BONDS)
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import date
from enum import Enum


class PolicyType(str, Enum):
    """政策类型"""
    SPECIAL_BONDS = "special_bonds"
    FRANCHISE = "franchise"
    DATA_ASSETS = "data_assets"


class PolicyStatus(str, Enum):
    """政策状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    UPDATED = "updated"
    EXPIRING_SOON = "expiring_soon"


@dataclass
class PolicyMetadata:
    """政策元数据"""
    title: str
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    publish_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    region: str = "全国"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class PolicyContent:
    """政策内容"""
    content: str
    summary: Optional[str] = None

    def get_content_length(self) -> int:
        """获取内容长度"""
        return len(self.content) if self.content else 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Policy:
    """政策对象"""
    id: Optional[int] = None
    metadata: PolicyMetadata = None
    content: PolicyContent = None
    policy_type: PolicyType = PolicyType.SPECIAL_BONDS
    status: PolicyStatus = PolicyStatus.ACTIVE
    file_path: Optional[str] = None
    ragflow_doc_id: Optional[str] = None
    tags: List[Dict[str, Any]] = None
    relations: List[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.tags is None:
            self.tags = []
        if self.relations is None:
            self.relations = []
        if self.metadata is None:
            self.metadata = PolicyMetadata(title="")
        if self.content is None:
            self.content = PolicyContent(content="")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.metadata.title if self.metadata else '',
            'document_number': self.metadata.document_number if self.metadata else None,
            'issuing_authority': self.metadata.issuing_authority if self.metadata else None,
            'publish_date': self.metadata.publish_date if self.metadata else None,
            'effective_date': self.metadata.effective_date if self.metadata else None,
            'expiration_date': self.metadata.expiration_date if self.metadata else None,
            'region': self.metadata.region if self.metadata else '全国',
            'content': self.content.content if self.content else '',
            'summary': self.content.summary if self.content else None,
            'policy_type': self.policy_type.value,
            'status': self.status.value,
            'file_path': self.file_path,
            'ragflow_doc_id': self.ragflow_doc_id,
            'tags': self.tags,
            'relations': self.relations
        }

    def to_db_dict(self) -> Dict[str, Any]:
        """转换为数据库字典"""
        return {
            'title': self.metadata.title if self.metadata else '',
            'document_number': self.metadata.document_number if self.metadata else None,
            'issuing_authority': self.metadata.issuing_authority if self.metadata else None,
            'publish_date': self.metadata.publish_date if self.metadata else None,
            'effective_date': self.metadata.effective_date if self.metadata else None,
            'expiration_date': self.metadata.expiration_date if self.metadata else None,
            'region': self.metadata.region if self.metadata else '全国',
            'content': self.content.content if self.content else '',
            'summary': self.content.summary if self.content else None,
            'policy_type': self.policy_type.value,
            'status': self.status.value,
            'file_path': self.file_path,
            'ragflow_doc_id': self.ragflow_doc_id
        }

    @staticmethod
    def from_db_dict(db_dict: Dict[str, Any]) -> 'Policy':
        """从数据库字典创建Policy"""
        metadata = PolicyMetadata(
            title=db_dict.get('title', ''),
            document_number=db_dict.get('document_number'),
            issuing_authority=db_dict.get('issuing_authority'),
            publish_date=db_dict.get('publish_date'),
            effective_date=db_dict.get('effective_date'),
            expiration_date=db_dict.get('expiration_date'),
            region=db_dict.get('region', '全国')
        )

        content = PolicyContent(
            content=db_dict.get('content', ''),
            summary=db_dict.get('summary')
        )

        try:
            policy_type = PolicyType(db_dict.get('policy_type', 'special_bonds'))
        except ValueError:
            policy_type = PolicyType.SPECIAL_BONDS

        try:
            status = PolicyStatus(db_dict.get('status', 'active'))
        except ValueError:
            status = PolicyStatus.ACTIVE

        return Policy(
            id=db_dict.get('id'),
            metadata=metadata,
            content=content,
            policy_type=policy_type,
            status=status,
            file_path=db_dict.get('file_path'),
            ragflow_doc_id=db_dict.get('ragflow_doc_id')
        )

    def get_title(self) -> str:
        """获取标题"""
        return self.metadata.title if self.metadata else ''

    def get_summary(self) -> str:
        """获取摘要"""
        return self.content.summary or self.content.content[:200] + '...' if self.content else ''

    def add_tag(self, tag: Dict[str, Any]):
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)

    def add_relation(self, relation: Dict[str, Any]):
        """添加关系"""
        if relation not in self.relations:
            self.relations.append(relation)

    def is_valid(self) -> bool:
        """检查政策是否有效"""
        # 必需字段检查
        if not self.metadata or not self.metadata.title:
            return False
        if not self.content or not self.content.content:
            return False
        return True
