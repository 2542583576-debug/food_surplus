"""接口冒烟测试：python tests/smoke_test.py（需先启动服务）。"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method, path, body=None, token=None, expected=200):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, payload = resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        status, payload = exc.code, json.loads(exc.read().decode())
    ok = status == expected
    print(f"{'PASS' if ok else 'FAIL'} {method:4} {path:38} {status}")
    if not ok:
        print("      ", payload)
    return payload


def main():
    call("GET", "/health")
    call("GET", "/ready")

    admin = call("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})
    admin_token = admin["access_token"]
    me = call("GET", "/api/v1/auth/me", token=admin_token)
    assert me["role"] == 1, f"管理员角色错误: {me}"

    user = call("POST", "/api/users/login", {"username": "user", "password": "user123"})
    user_token = user["access_token"]
    user_me = call("GET", "/api/users/me", token=user_token)
    assert user_me["role"] == 0, f"普通用户角色错误: {user_me}"

    bags = call("GET", "/api/surplus-bags/")
    if not bags:
        print("FAIL 没有可用魔法袋，请先执行 scripts/init_db.py")
        return
    bag_id = bags[0]["id"]

    order = call(
        "POST",
        "/api/orders/",
        {"bag_id": bag_id, "customer_phone": "13900139000"},
        token=user_token,
        expected=201,
    )
    assert order["verify_code"], "核销码未生成"
    call("GET", "/api/orders/", token=user_token)
    call("GET", f"/api/orders/{order['id']}", token=user_token)
    call("PUT", f"/api/orders/{order['id']}/verify", token=admin_token)
    call("GET", "/api/carbon/platform/summary")

    call("GET", "/api/v1/categories", token=admin_token)
    call("GET", "/api/v1/products", token=admin_token)
    call("GET", "/api/v1/blind-boxes", token=admin_token)
    call("GET", "/api/v1/merchant/orders", token=admin_token)
    print("冒烟测试结束")


if __name__ == "__main__":
    main()
