"""
标签数据模型
"""
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from enum import Enum


class TagLevel(int, Enum):
    """标签级别"""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class PolicyTypeCategory(str, Enum):
    """政策类型分类"""
    SPECIAL_BONDS = "special_bonds"
    FRANCHISE = "franchise"
    DATA_ASSETS = "data_assets"


@dataclass
class Tag:
    """标签对象"""
    id: Optional[int] = None
    name: str = ""
    level: int = 1
    parent_id: Optional[int] = None
    policy_type: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0
    children: List['Tag'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'parent_id': self.parent_id,
            'policy_type': self.policy_type,
            'description': self.description,
            'display_order': self.display_order,
            'children': [child.to_dict() for child in self.children]
        }

    @staticmethod
    def from_db_dict(db_dict: Dict[str, Any]) -> 'Tag':
        """从数据库字典创建Tag"""
        return Tag(
            id=db_dict.get('id'),
            name=db_dict.get('name', ''),
            level=db_dict.get('level', 1),
            parent_id=db_dict.get('parent_id'),
            policy_type=db_dict.get('policy_type'),
            description=db_dict.get('description'),
            display_order=db_dict.get('display_order', 0)
        )

    def to_db_dict(self) -> Dict[str, Any]:
        """转换为数据库字典"""
        return {
            'name': self.name,
            'level': self.level,
            'parent_id': self.parent_id,
            'policy_type': self.policy_type,
            'description': self.description,
            'display_order': self.display_order
        }

    def is_valid(self) -> bool:
        """检查标签是否有效"""
        return bool(self.name and 1 <= self.level <= 3)

    def add_child(self, child: 'Tag'):
        """添加子标签"""
        if child not in self.children:
            self.children.append(child)
            child.parent_id = self.id

    def get_path(self) -> str:
        """获取标签路径（用于显示层级关系）"""
        return f"{self.policy_type or ''}/{self.name}".strip('/')


@dataclass
class TagHierarchy:
    """标签体系（用于管理三级标签树）"""
    root_tags: List[Tag] = field(default_factory=list)

    def add_tag(self, tag: Tag):
        """添加顶级标签"""
        if tag not in self.root_tags:
            self.root_tags.append(tag)

    def find_tag_by_name(self, name: str) -> Optional[Tag]:
        """按名称查找标签"""
        for tag in self.root_tags:
            result = self._search_tag(tag, name)
            if result:
                return result
        return None

    @staticmethod
    def _search_tag(tag: Tag, name: str) -> Optional[Tag]:
        """递归搜索标签"""
        if tag.name == name:
            return tag

        for child in tag.children:
            result = TagHierarchy._search_tag(child, name)
            if result:
                return result

        return None

    def find_tags_by_policy_type(self, policy_type: str) -> List[Tag]:
        """按政策类型获取所有标签"""
        tags = []

        for tag in self.root_tags:
            if tag.policy_type == policy_type:
                tags.append(tag)
                tags.extend(self._get_all_children(tag))

        return tags

    @staticmethod
    def _get_all_children(tag: Tag) -> List[Tag]:
        """获取标签的所有子标签"""
        children = []

        for child in tag.children:
            children.append(child)
            children.extend(TagHierarchy._get_all_children(child))

        return children

    def get_tags_by_level(self, level: int) -> List[Tag]:
        """按级别获取标签"""
        tags = []

        for tag in self.root_tags:
            if tag.level == level:
                tags.append(tag)

            tags.extend(self._search_tags_by_level(tag, level))

        return tags

    @staticmethod
    def _search_tags_by_level(tag: Tag, level: int) -> List[Tag]:
        """递归搜索指定级别的标签"""
        tags = []

        for child in tag.children:
            if child.level == level:
                tags.append(child)

            tags.extend(TagHierarchy._search_tags_by_level(child, level))

        return tags

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'root_tags': [tag.to_dict() for tag in self.root_tags]
        }

    def get_flattened_tags(self) -> List[Tag]:
        """获取扁平化的标签列表"""
        tags = []

        for root_tag in self.root_tags:
            tags.append(root_tag)
            tags.extend(self._get_all_children(root_tag))

        return tags


@dataclass
class TagAssociation:
    """标签关联（政策与标签的关联）"""
    policy_id: int
    tag_id: int
    confidence: float = 1.0  # 置信度（0-1）
    source: str = "auto"  # auto 或 manual

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @staticmethod
    def from_db_dict(db_dict: Dict[str, Any]) -> 'TagAssociation':
        """从数据库字典创建"""
        return TagAssociation(
            policy_id=db_dict.get('policy_id'),
            tag_id=db_dict.get('tag_id'),
            confidence=db_dict.get('confidence', 1.0),
            source=db_dict.get('source', 'auto')
        )

    def is_valid(self) -> bool:
        """检查关联是否有效"""
        return (self.policy_id and self.tag_id and
                0 <= self.confidence <= 1.0 and
                self.source in ['auto', 'manual'])
