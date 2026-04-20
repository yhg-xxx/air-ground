"""迷宫数据API"""
from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(prefix="/maze", tags=["迷宫"])

@router.get("/blocks")
async def get_maze_blocks():
    """获取迷宫墙壁块数据"""
    blocks_path = Path("output/wall_blocks.json")
    
    if blocks_path.exists():
        with open(blocks_path, 'r') as f:
            data = json.load(f)
        return data
    
    # 默认返回空数据
    return {"width": 480, "height": 1200, "sample": 10, "blocks": []}
