#!/bin/bash

# ===========================================
# RAG 智能客服系统 - 一键部署脚本
# ===========================================

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要工具
check_requirements() {
    print_info "检查系统要求..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_info "系统要求检查通过 ✓"
}

# 初始化环境变量
init_env() {
    print_info "初始化环境变量..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "已创建 .env 文件，请编辑配置"
        fi
    fi
    
    print_info "环境变量初始化完成 ✓"
}

# 构建 Docker 镜像
build_images() {
    print_info "构建 Docker 镜像..."
    
    docker-compose build
    
    print_info "镜像构建完成 ✓"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    docker-compose up -d
    
    print_info "服务启动完成 ✓"
}

# 等待服务就绪
wait_for_services() {
    print_info "等待服务就绪..."
    
    # 等待 API Gateway
    print_info "等待 API Gateway..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_info "API Gateway 已就绪 ✓"
            break
        fi
        sleep 2
    done
    
    # 等待管理 API
    print_info "等待管理 API..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            print_info "管理 API 已就绪 ✓"
            break
        fi
        sleep 2
    done
    
    print_info "所有服务就绪 ✓"
}

# 验证部署
verify_deployment() {
    print_info "验证部署..."
    
    echo ""
    echo "=========================================="
    echo "         部署验证"
    echo "=========================================="
    echo ""
    
    # 检查 API Gateway
    echo -n "API Gateway: "
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}运行中 ✓${NC}"
    else
        echo -e "${RED}未运行 ✗${NC}"
    fi
    
    # 检查管理 API
    echo -n "管理 API: "
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}运行中 ✓${NC}"
    else
        echo -e "${RED}未运行 ✗${NC}"
    fi
    
    echo ""
    echo "=========================================="
    echo ""
}

# 打印使用说明
print_usage() {
    echo ""
    echo "=========================================="
    echo "       RAG 智能客服系统已成功部署！"
    echo "=========================================="
    echo ""
    echo "访问地址："
    echo "  • 消费者前端:    http://localhost:3000"
    echo "  • 企业管理前端:  http://localhost:8080"
    echo "  • 系统管理前端:  http://localhost:9090"
    echo "  • API Gateway:   http://localhost:8000"
    echo ""
    echo "常用命令："
    echo "  • 查看服务状态:  docker-compose ps"
    echo "  • 查看日志:      docker-compose logs -f"
    echo "  • 停止服务:      docker-compose down"
    echo "  • 重启服务:      docker-compose restart"
    echo ""
    echo "详细文档请查看: DEPLOYMENT_GUIDE.md"
    echo ""
}

# 主函数
main() {
    echo "=========================================="
    echo "  RAG 智能客服系统 - 一键部署脚本"
    echo "=========================================="
    echo ""
    
    check_requirements
    init_env
    build_images
    start_services
    wait_for_services
    verify_deployment
    print_usage
}

# 执行主函数
main
