import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # 允许两个可能的前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# 包含API路由
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Air-Ground Coordination Backend"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)