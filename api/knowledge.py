"""
知识库管理API
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


class KnowledgeItem(BaseModel):
    id: Optional[int] = None
    content: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    category: str = "general"
    keywords: List[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None


def _knowledge_content(item: KnowledgeItem) -> str:
    if item.content and item.content.strip():
        return item.content.strip()
    if item.question and item.answer:
        return f"问题: {item.question.strip()}\n答案: {item.answer.strip()}"
    raise HTTPException(status_code=422, detail="content 或 question/answer 必填")


@router.get("/")
async def get_all_knowledge():
    """获取所有知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        entries = knowledge_service.get_all_documents()
        
        # 安全获取categories，避免出错
        try:
            categories = knowledge_service.get_all_categories()
        except Exception as e:
            print(f"获取categories失败: {e}")
            categories = []
        
        return {
            "documents": entries or [],
            "categories": categories or [],
            "total_count": len(entries) if entries else 0,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库失败: {str(e)}")


@router.get("/{knowledge_id}")
async def get_knowledge(knowledge_id: int):
    """获取特定知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        entry = knowledge_service.get_document(knowledge_id)
        if not entry:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {
            "status": "success",
            "data": entry
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识条目失败: {str(e)}")


@router.post("/")
async def add_knowledge(item: KnowledgeItem):
    """添加新的知识条目"""
    try:
        from services.knowledge_service import KnowledgeService

        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()

        content = _knowledge_content(item)
        result = await knowledge_service.add_document(
            content=content,
            category=item.category,
            keywords=item.keywords,
        )
        return {
            "status": "success",
            "message": "知识条目添加成功",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加知识条目失败: {str(e)}")


@router.put("/{knowledge_id}")
async def update_knowledge(knowledge_id: int, item: KnowledgeItem):
    """更新知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        content = _knowledge_content(item)
        result = await knowledge_service.update_document(
            doc_id=knowledge_id,
            content=content,
            category=item.category,
            keywords=item.keywords,
        )
        if not result:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {
            "status": "success",
            "message": "知识条目更新成功",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新知识条目失败: {str(e)}")


@router.delete("/{knowledge_id}")
async def delete_knowledge(knowledge_id: int):
    """删除知识条目"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        result = await knowledge_service.delete_document(knowledge_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return {
            "status": "success",
            "message": "知识条目删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除知识条目失败: {str(e)}")


@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """搜索知识库"""
    try:
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService()
        if not knowledge_service.initialized:
            await knowledge_service.initialize()
        results = await knowledge_service.search(
            request.query,
            top_k=request.top_k,
            category=request.category,
        )
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "total_found": len(results),
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索知识库失败: {str(e)}")
