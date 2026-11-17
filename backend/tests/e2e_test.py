"""端到端业务闭环测试：用户下单 -> 商家可见 -> 核销 -> 碳账本 -> 通知。

运行前需启动后端服务：uvicorn app.main:app --port 8000
用法：python tests/e2e_test.py
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0


def call(method, path, body=None, token=None, expected=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status, payload = resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw
        status = exc.code
    ok = (status == expected) if expected is not None else (200 <= status < 300)
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"{'PASS' if ok else 'FAIL':4} {method:4} {path:44} {status}")
    if not ok:
        print("      响应:", payload)
    return status, payload


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    section("端到端验收：惜食余量魔法袋业务闭环")

    # 0. 健康检查
    call("GET", "/health", expected=200)

    # 1. 用户登录
    _, user_login = call("POST", "/api/v1/auth/login",
                         {"username": "user", "password": "user123"}, expected=200)
    user_token = user_login["access_token"]
    _, user_me = call("GET", "/api/v1/auth/me", token=user_token, expected=200)
    assert user_me["role"] == 0, f"普通用户角色错误: {user_me}"
    print(f"  C 端用户: {user_me['username']} (id={user_me['id']})")

    # 2. 商家登录
    _, admin_login = call("POST", "/api/v1/auth/login",
                          {"username": "admin", "password": "admin123"}, expected=200)
    admin_token = admin_login["access_token"]
    _, admin_me = call("GET", "/api/v1/auth/me", token=admin_token, expected=200)
    assert admin_me["role"] == 1, f"管理员角色错误: {admin_me}"
    print(f"  B 端商家: {admin_me['username']} (store_id={admin_me.get('store_id')})")

    # 3. 浏览可预订魔法袋
    _, bags = call("GET", "/api/surplus-bags/", expected=200)
    assert bags, "没有可预订的魔法袋，请先执行 scripts/init_db.py"
    bag = bags[0]
    print(f"  选择魔法袋: {bag['bag_name']} (id={bag['id']}, ¥{bag['sale_price']})")

    # 4. C 端用户下单，拿到核销码
    _, order = call("POST", "/api/orders/",
                    {"bag_id": bag["id"], "customer_phone": "13900139000",
                     "customer_name": "验收测试", "pay_method": "online"},
                    token=user_token, expected=201)
    assert order["verify_code"], "核销码未生成"
    verify_code = order["verify_code"]
    order_id = order["id"]
    print(f"  下单成功: 订单号={order['order_no']}, 核销码={verify_code}, merchant_id={order.get('merchant_id')}")
    assert order.get("merchant_id") == admin_me["id"], "闭环错误：订单未关联到门店管理员"

    # 5. 下单通知已生成
    _, notes = call("GET", "/api/notifications/", token=user_token, expected=200)
    assert any(n["title"] == "预订成功" for n in notes), "缺少下单成功通知"
    print(f"  通知已生成: 当前用户共 {len(notes)} 条通知")

    # 6. 商家端订单列表能看到该订单（闭环关键断言）
    _, merchant_orders = call("GET", "/api/v1/merchant/orders?size=100",
                              token=admin_token, expected=200)
    ids = [o["id"] for o in merchant_orders["items"]]
    assert order_id in ids, f"闭环断裂：商家端看不到订单 {order_id}，可见ID={ids}"
    print(f"  商家端可见订单 {order_id}，共 {merchant_orders['total']} 条")

    # 7. 碳账本下单前快照
    _, before = call("GET", f"/api/carbon/user/summary?user_id={user_me['id']}", expected=200)
    before_count = before.get("total_order_count", 0)

    # 8. 商家核销（输入核销码）
    _, verified = call("POST", f"/api/v1/merchant/orders/{order_id}/verify",
                       {"verify_code": verify_code}, token=admin_token, expected=200)
    assert verified["status"] == 2, f"核销后状态错误: {verified['status']}"
    assert verified["pay_status"] == 1, f"核销后支付状态错误: {verified['pay_status']}"
    print(f"  核销成功: 状态={verified['status']}, 支付状态={verified['pay_status']}")

    # 9. 碳账本出现记录
    _, after = call("GET", f"/api/carbon/user/summary?user_id={user_me['id']}", expected=200)
    assert after["total_order_count"] == before_count + 1, "碳账本未新增记录"
    _, records = call("GET", f"/api/carbon/user/records?user_id={user_me['id']}", expected=200)
    assert any(r["order_id"] == order_id for r in records), "碳记录未关联到本订单"
    print(f"  碳账本已更新: 订单数 {before_count} -> {after['total_order_count']}, 减碳 {after['total_reduce_carbon']}kg")

    # 10. 核销通知已生成
    _, notes2 = call("GET", "/api/notifications/", token=user_token, expected=200)
    assert any(n["title"] == "核销成功" for n in notes2), "缺少核销成功通知"
    print("  核销通知已生成")

    # 11. 门店自提点列表
    _, stores = call("GET", "/api/stores/", expected=200)
    assert stores, "门店自提点列表为空"
    print(f"  门店自提点: {len(stores)} 家")

    section(f"验收结果：通过 {PASS} 项，失败 {FAIL} 项")
    if FAIL:
        sys.exit(1)
    print("完整业务闭环验收通过：下单 -> 商家可见 -> 核销 -> 碳账本 -> 通知")


if __name__ == "__main__":
    main()
