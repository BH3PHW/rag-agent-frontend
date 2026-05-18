# 练习05: 第一个API
# 运行: python practice_05_first_api.py
# 访问: http://localhost:8080

from fastapi import FastAPI

app = FastAPI(title="练习05 - 第一个API")

# 根路径
@app.get("/")
async def root():
    return {
        "message": "欢迎来到练习05！",
        "course": "Python入门教程"
    }

# 问候API
@app.get("/greet/{name}")
async def greet(name: str):
    return {
        "greeting": f"你好，{name}！",
        "message": "欢迎使用我们的API"
    }

# 简单计算器
@app.get("/calculate/{a}/{b}")
async def calculate(a: int, b: int):
    return {
        "a": a,
        "b": b,
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "除数不能为0"
    }

# 运行服务器
if __name__ == "__main__":
    import uvicorn
    print("=" * 40)
    print("🚀 API服务器启动在 http://localhost:8080")
    print("📚 API文档: http://localhost:8080/docs")
    print("=" * 40)
    uvicorn.run(app, host="0.0.0.0", port=8080)
