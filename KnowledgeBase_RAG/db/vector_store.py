"""向量库封装：文档加载、切分、Embedding、Chroma 持久化。"""
from __future__ import annotations # 与python的类型注解有关

import hashlib # hashlib 是 Python 自带的加密/哈希工具
import json
import os
from pathlib import Path # Path 是 Python 处理文件路径的工具
from typing import List, Optional, Tuple

from langchain_core.documents import Document # 导入Langchain文档对象
from langchain_text_splitters import ( # 导入两个文本切分器
    MarkdownHeaderTextSplitter,  # 按照MarkDown标题结构进行切分
    RecursiveCharacterTextSplitter,  # 用于普通文本进行切分
)
from langchain_community.embeddings import DashScopeEmbeddings # 负责把文本转换成向量
from langchain_chroma import Chroma # 导入向量数据库
# 向量库的核心作用是：
# 把文档向量化并存储（原文 + 向量）
# 根据用户 Query 的向量，高效检索出最相关的原始文档

# 导入项目配置 配置与业务实现逻辑分离
from common.config import (
    DASHSCOPE_API_KEY,
    EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RESOURCES_DIR,
    UPLOADS_DIR,
)

# 元数据记录文件 主要记录：这个知识库有哪些文件 每个文件多少 chunk 文件路径是什么
META_PATH = Path(CHROMA_PERSIST_DIR) / "docs_meta.json"

# 文档加载 + 文档切分 + Embedding + VectorStore + Retrieval

# 创建一个知识库管理器
class KnowledgeBase:
    """个人知识库：支持 Markdown / 纯文本上传与检索。"""

    # 构造函数init，初始化这个对象
    def __init__(self):
        self._embeddings = None
        self._vectorstore: Optional[Chroma] = None
        self._meta: dict = self._load_meta()

    # ---------- 内部 ----------
    # 从JSON文件中加载元数据
    # 元数据是和向量（Embedding）配套存储的额外信息，它的核心作用是：
    # 1.把向量和原始内容关联起来 2.支持过滤和条件查询 3.记录索引结构信息
    def _load_meta(self) -> dict:
        if META_PATH.exists():
            try:
                return json.loads(META_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    # 把内存中的 self._meta 保存到 JSON 文件
    # 程序启动后，通过 _load_meta() 把元数据加载到内存变量 self._meta（通常是一个 dict）。
    # 之后所有增删改查操作，都直接操作内存中的 self._meta，速度很快。
    # 当需要持久化时（比如新增了文档、删除了文档、或者程序退出前），就调用 _save_meta()，把内存里的最新状态写回磁盘上的 JSON 文件。
    def _save_meta(self):
        META_PATH.parent.mkdir(parents=True, exist_ok=True)
        META_PATH.write_text(json.dumps(self._meta, ensure_ascii=False, indent=2), encoding="utf-8")

    @property # 注解的作用：是 Python 的装饰器，它的核心作用是：把一个方法变成“属性”访问方式 方法像属性一样访问，可以不需要加括号
    # 懒加载创建Embedding模型
    def embeddings(self):
        if self._embeddings is None: #检查实例内部的私有变量 _embeddings 是否还是 None。如果是 None，说明还没有创建过 Embedding 模型，需要初始化。这是懒加载（Lazy Loading）的核心判断。
            if not DASHSCOPE_API_KEY:
                raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY")
            self._embeddings = DashScopeEmbeddings(
                model=EMBEDDING_MODEL,
                dashscope_api_key=DASHSCOPE_API_KEY,
            )
        return self._embeddings

    @property
    # 懒加载创建Chroma向量库
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIR,
            )
        return self._vectorstore

    # ---------- 切分 ----------
    #定义了两个切分方法
    # _split_markdown —— 专门切分 Markdown 文档

    # text：原始 Markdown 字符串 source：文档来源标识（后面会用来生成唯一 id） 返回值：切分后的 Document 列表
    def _split_markdown(self, text: str, source: str) -> List[Document]:
        # 定义要按哪些标题级别进行切分
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        # 创建Langchain的Markdown标题切分器
        md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
        chunks = md_splitter.split_text(text)

        # 创建第二级切分器（递归字符切分器） separators 优先按段落、换行、中文句号等位置断开，对中文更友好
        recursive = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],
        )

        # 初始化最终要返回的 Document 列表
        docs: List[Document] = []
        # idx 用来给每个小块生成唯一编号（从 1 开始）
        idx = 1
        for c in chunks:
            content = c.page_content
            meta = dict(c.metadata)
            meta["source"] = source
            header = meta.get("Header 3") or meta.get("Header 2") or meta.get("Header 1") or ""
            if header:
                content = f"### {header}\n{content}"

            if len(content) > CHUNK_SIZE:
                for sub in recursive.split_text(content):
                    d = Document(page_content=sub, metadata={**meta, "id": f"{source}_{idx}"})
                    d.id = d.metadata["id"]
                    docs.append(d)
                    idx += 1
            else:
                d = Document(page_content=content, metadata={**meta, "id": f"{source}_{idx}"})
                d.id = d.metadata["id"]
                docs.append(d)
                idx += 1
        return docs
    # _split_plain —— 切分普通纯文本
    def _split_plain(self, text: str, source: str) -> List[Document]:
        recursive = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],
        )
        docs = []
        for i, chunk in enumerate(recursive.split_text(text), start=1):
            d = Document(
                page_content=chunk,
                metadata={"source": source, "id": f"{source}_{i}"},
            )
            d.id = d.metadata["id"]
            docs.append(d)
        return docs

    # ---------- 公开 API ----------
    
    # 加载本地文件并写入向量库
    def add_file(self, file_path: Path, filename: Optional[str] = None) -> Tuple[str, int]:
        """加载本地文件并写入向量库。返回 (doc_id, chunk_count)。"""
        filename = filename or file_path.name
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        file_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        doc_id = f"{filename}_{file_hash}"

        if file_path.suffix.lower() in {".md", ".markdown"}:
            docs = self._split_markdown(text, doc_id)
        else:
            docs = self._split_plain(text, doc_id)

        if not docs:
            return doc_id, 0

        # 先删同名旧数据再写入（简单实现：按 source 过滤较难，这里直接 add）
        self.vectorstore.add_documents(docs)
        self._meta[doc_id] = {
            "filename": filename,
            "chunks": len(docs),
            "path": str(file_path),
        }
        self._save_meta()
        return doc_id, len(docs)
    # 直接添加文本内容
    def add_text(self, text: str, filename: str = "pasted.txt") -> Tuple[str, int]:
        """直接添加文本内容。"""
        tmp = UPLOADS_DIR / filename
        tmp.write_text(text, encoding="utf-8")
        return self.add_file(tmp, filename)

    # 相似度搜索 根据用户问题，从向量库中找出最相关的 k 个文档块
    def search(self, query: str, k: int = 5) -> List[Document]:
        """相似度检索。"""
        return self.vectorstore.similarity_search(query, k=k)
    # 带相关度分数的检索 和 search 类似，但额外返回每个结果的相关度分数
    def search_with_scores(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        return self.vectorstore.similarity_search_with_relevance_scores(query, k=k)
    # 获取检索器对象 把向量库包装成 LangChain 标准的 Retriever 对象
    def as_retriever(self, k: int = 5):
        return self.vectorstore.as_retriever(search_kwargs={"k": k})
    # 列出已入库的文档 作用：返回当前知识库中所有文档的简要信息
    def list_documents(self) -> List[dict]:
        return [
            {"id": did, "filename": info["filename"], "chunks": info["chunks"], "status": "indexed"}
            for did, info in self._meta.items()
        ]
    # 获取知识库统计信息 返回知识库的整体统计数据
    def stats(self) -> dict:
        total_chunks = sum(v.get("chunks", 0) for v in self._meta.values())
        return {
            "total_documents": len(self._meta),
            "total_chunks": total_chunks,
            "collection_name": COLLECTION_NAME,
        }
    # 清空整个知识库 开发/调试时用来彻底清空知识库
    def clear(self):
        """清空知识库（开发用）。"""
        import shutil
        if Path(CHROMA_PERSIST_DIR).exists():
            shutil.rmtree(CHROMA_PERSIST_DIR, ignore_errors=True)
        self._vectorstore = None
        self._meta = {}
        self._save_meta()


# 单例 方便全局使用：其他模块只需要 from xxx import kb，就可以直接调用 kb.add_file(...)
kb = KnowledgeBase()

#函数                 阶段             作用简述
#add_text            入库             文本 → 临时文件 → 调用 add_file
#add_file            入库             文件 → 切分 → 写入向量库
#search              检索             相似度搜索（无分数）
#search_with_scores  检索             相似度搜索（带分数）
#as_retriever        检索             返回标准 Retriever 对象
#list_documents       管理            列出已有文档
#stats                管理            统计信息
#clear                管理           清空知识库