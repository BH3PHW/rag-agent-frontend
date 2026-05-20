#!/usr/bin/env python3
"""
角色系统测试脚本
验证三类角色的权限是否正确实现
"""
import sys
sys.path.insert(0, '/workspace/backend')

from common.role_permissions import (
    RoleType,
    Permission,
    has_permission,
    get_role_permissions,
    ROLE_PERMISSIONS,
    get_role_info
)


def test_consumer_permissions():
    """测试消费者角色权限"""
    print("\n=== 测试消费者（Consumer）角色 ===")

    role = RoleType.CONSUMER
    permissions = get_role_permissions(role)

    print(f"角色：{role.value}")
    print(f"权限数量：{len(permissions)}")

    # 验证核心权限
    core_permissions = [
        Permission.SESSION_CREATE,
        Permission.SESSION_READ_OWN,
        Permission.SESSION_DELETE_OWN,
        Permission.MESSAGE_CREATE,
        Permission.MESSAGE_READ_OWN,
        Permission.FEEDBACK_CREATE,
        Permission.FEEDBACK_READ_OWN,
    ]

    print("\n核心权限检查：")
    all_passed = True
    for perm in core_permissions:
        has = has_permission(role, perm)
        status = "✅" if has else "❌"
        print(f"  {status} {perm.value}")
        if not has:
            all_passed = False

    # 验证不应该有的权限
    print("\n不应该有的权限检查：")
    forbidden_permissions = [
        Permission.SESSION_READ_ENTERPRISE,
        Permission.SESSION_READ_ALL,
        Permission.KNOWLEDGE_BASE_CREATE,
        Permission.ENTERPRISE_MANAGE_MEMBERS,
        Permission.SYSTEM_CONFIG,
    ]

    for perm in forbidden_permissions:
        has = has_permission(role, perm)
        status = "❌ (错误)" if has else "✅"
        print(f"  {status} {perm.value}")
        if has:
            all_passed = False

    return all_passed


def test_enterprise_admin_permissions():
    """测试企业管理员角色权限"""
    print("\n=== 测试企业管理员（Enterprise Admin）角色 ===")

    role = RoleType.ENTERPRISE_ADMIN
    permissions = get_role_permissions(role)

    print(f"角色：{role.value}")
    print(f"权限数量：{len(permissions)}")

    # 验证核心权限
    core_permissions = [
        Permission.SESSION_READ_ENTERPRISE,
        Permission.MESSAGE_READ_ENTERPRISE,
        Permission.KNOWLEDGE_BASE_CREATE,
        Permission.KNOWLEDGE_BASE_READ,
        Permission.KNOWLEDGE_BASE_UPDATE,
        Permission.KNOWLEDGE_BASE_DELETE,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_DELETE,
        Permission.ENTERPRISE_READ,
        Permission.ENTERPRISE_UPDATE,
        Permission.ENTERPRISE_MANAGE_MEMBERS,
        Permission.USER_READ_ENTERPRISE,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.ALERT_READ,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.ALERT_RESOLVE,
    ]

    print("\n核心权限检查：")
    all_passed = True
    for perm in core_permissions:
        has = has_permission(role, perm)
        status = "✅" if has else "❌"
        print(f"  {status} {perm.value}")
        if not has:
            all_passed = False

    # 验证不应该有的权限
    print("\n不应该有的权限检查：")
    forbidden_permissions = [
        Permission.SESSION_READ_ALL,
        Permission.SYSTEM_READ_ALL_ENTERPRISES,
        Permission.SYSTEM_MANAGE_ENTERPRISES,
        Permission.SYSTEM_CONFIG,
    ]

    for perm in forbidden_permissions:
        has = has_permission(role, perm)
        status = "❌ (错误)" if has else "✅"
        print(f"  {status} {perm.value}")
        if has:
            all_passed = False

    return all_passed


def test_system_admin_permissions():
    """测试系统管理员角色权限"""
    print("\n=== 测试系统管理员（System Admin）角色 ===")

    role = RoleType.SYSTEM_ADMIN
    permissions = get_role_permissions(role)

    print(f"角色：{role.value}")
    print(f"权限数量：{len(permissions)}")

    # 验证核心权限
    core_permissions = [
        Permission.SESSION_READ_ALL,
        Permission.SYSTEM_READ_ALL_ENTERPRISES,
        Permission.SYSTEM_MANAGE_ENTERPRISES,
        Permission.SYSTEM_VIEW_LOGS,
        Permission.SYSTEM_CONFIG,
    ]

    print("\n系统管理权限检查：")
    all_passed = True
    for perm in core_permissions:
        has = has_permission(role, perm)
        status = "✅" if has else "❌"
        print(f"  {status} {perm.value}")
        if not has:
            all_passed = False

    # 验证应该包含企业管理员的所有权限
    print("\n包含企业管理员权限检查：")
    enterprise_admin_role = RoleType.ENTERPRISE_ADMIN
    enterprise_permissions = get_role_permissions(enterprise_admin_role)

    for perm in enterprise_permissions:
        has = has_permission(role, perm)
        status = "✅" if has else "❌"
        print(f"  {status} {perm.value}")
        if not has:
            all_passed = False

    return all_passed


def test_role_hierarchy():
    """测试角色层级关系"""
    print("\n=== 测试角色层级关系 ===")

    # 系统管理员应该拥有所有权限
    system_admin_perms = get_role_permissions(RoleType.SYSTEM_ADMIN)
    enterprise_admin_perms = get_role_permissions(RoleType.ENTERPRISE_ADMIN)
    consumer_perms = get_role_permissions(RoleType.CONSUMER)

    print(f"系统管理员权限数量：{len(system_admin_perms)}")
    print(f"企业管理员权限数量：{len(enterprise_admin_perms)}")
    print(f"消费者权限数量：{len(consumer_perms)}")

    # 验证权限数量递增
    all_passed = True
    if len(system_admin_perms) < len(enterprise_admin_perms):
        print("❌ 系统管理员权限应该 >= 企业管理员权限")
        all_passed = False
    else:
        print("✅ 系统管理员权限 >= 企业管理员权限")

    if len(enterprise_admin_perms) < len(consumer_perms):
        print("❌ 企业管理员权限应该 >= 消费者权限")
        all_passed = False
    else:
        print("✅ 企业管理员权限 >= 消费者权限")

    return all_passed


def test_role_info():
    """测试角色信息获取"""
    print("\n=== 测试角色信息获取 ===")

    for role in RoleType:
        info = get_role_info(role)
        print(f"\n{role.value}:")
        print(f"  名称：{info.get('name')}")
        print(f"  英文名：{info.get('name_en')}")
        print(f"  描述：{info.get('description')}")
        print(f"  权限数量：{info.get('permissions_count')}")

    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("角色权限系统测试")
    print("=" * 60)

    results = []

    # 测试各类角色
    results.append(("消费者权限", test_consumer_permissions()))
    results.append(("企业管理员权限", test_enterprise_admin_permissions()))
    results.append(("系统管理员权限", test_system_admin_permissions()))
    results.append(("角色层级关系", test_role_hierarchy()))
    results.append(("角色信息获取", test_role_info()))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
