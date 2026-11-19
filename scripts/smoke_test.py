"""게시판 API 동작 확인 스크립트

서버를 먼저 실행한 뒤 다른 터미널에서 실행합니다.
    uv run uvicorn main:app --app-dir src --reload
    uv run python scripts/smoke_test.py
"""
import os
import uuid
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
results = []


def check(name: str, ok: bool, detail: str = ""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    suffix = uuid.uuid4().hex[:6]
    user_a = {"username": f"usera{suffix}", "password": "pass1234", "nickname": "회원A"}
    user_b = {"username": f"userb{suffix}", "password": "pass1234", "nickname": "회원B"}

    with httpx.Client(base_url=BASE_URL) as client:
        # 1) 회원가입
        r = client.post("/register", json=user_a)
        check("A 회원가입 201", r.status_code == 201, f"-> {r.status_code}")
        r = client.post("/register", json=user_b)
        check("B 회원가입 201", r.status_code == 201, f"-> {r.status_code}")
        r = client.post("/register", json=user_a)
        check("중복 아이디 400", r.status_code == 400, f"-> {r.status_code}")

        # 2) 로그인
        r = client.post("/login", data={"username": user_a["username"], "password": user_a["password"]})
        token_a = r.json().get("access_token")
        check("A 로그인 토큰 발급", r.status_code == 200 and bool(token_a))
        r = client.post("/login", data={"username": user_b["username"], "password": user_b["password"]})
        token_b = r.json().get("access_token")
        r = client.post("/login", data={"username": user_a["username"], "password": "wrong"})
        check("틀린 비밀번호 401", r.status_code == 401, f"-> {r.status_code}")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        r = client.get("/me", headers=headers_a)
        check("내 정보 조회 200", r.status_code == 200 and r.json()["username"] == user_a["username"])

        # 3) 게시글 CRUD
        r = client.post("/posts", json={"title": "첫 글", "content": "내용"})
        check("비로그인 작성 401", r.status_code == 401, f"-> {r.status_code}")
        r = client.post("/posts", json={"title": "첫 글", "content": "내용"}, headers=headers_a)
        check("A 게시글 작성 201", r.status_code == 201, f"-> {r.status_code}")
        post_id = r.json()["id"]

        r = client.get("/posts")
        check("목록 조회 200", r.status_code == 200 and any(p["id"] == post_id for p in r.json()))
        r = client.get(f"/posts/{post_id}")
        check("상세 조회 200", r.status_code == 200 and r.json()["title"] == "첫 글")
        r = client.get("/posts/999999")
        check("없는 글 404", r.status_code == 404, f"-> {r.status_code}")
        r = client.post("/posts", json={"title": "", "content": "내용"}, headers=headers_a)
        check("빈 제목 422", r.status_code == 422, f"-> {r.status_code}")

        r = client.put(f"/posts/{post_id}", json={"title": "B가 수정", "content": "x"}, headers=headers_b)
        check("B가 A 글 수정 403", r.status_code == 403, f"-> {r.status_code}")
        r = client.put(f"/posts/{post_id}", json={"title": "수정한 글", "content": "수정 내용"}, headers=headers_a)
        check("A 글 수정 200", r.status_code == 200 and r.json()["title"] == "수정한 글")

        r = client.delete(f"/posts/{post_id}", headers=headers_b)
        check("B가 A 글 삭제 403", r.status_code == 403, f"-> {r.status_code}")
        r = client.delete(f"/posts/{post_id}", headers=headers_a)
        check("A 글 삭제 204", r.status_code == 204, f"-> {r.status_code}")
        r = client.get(f"/posts/{post_id}")
        check("삭제 후 404", r.status_code == 404, f"-> {r.status_code}")

        r = client.get("/docs")
        check("Swagger UI 200", r.status_code == 200)

    print(f"\n결과: {sum(results)}/{len(results)} 통과")


if __name__ == "__main__":
    main()
