# RESTful 게시판 API (FastAPI)

회원가입·로그인(JWT)과 게시글 CRUD를 제공하는 게시판 API입니다.
교안 10장 5장 2강(비동기 SQLAlchemy, `models/`·`schemas/`), 4장 1강(`routers/`), 6장 1강(PyJWT·passlib·OAuth2PasswordBearer) 구조를 따릅니다.

## 기술 스택

FastAPI, Pydantic, SQLAlchemy(비동기, asyncpg), PostgreSQL 17(Docker), PyJWT, passlib + bcrypt 4.0.1, uv

## 폴더 구조

```
board-api/
├── pyproject.toml, uv.lock
├── docker-compose.yml        로컬 PostgreSQL 17 (호스트 포트 5434)
├── .env.example              DATABASE_URL, SECRET_KEY
├── scripts/smoke_test.py     동작 확인 스크립트
└── src/
    ├── main.py               앱 생성, 테이블 생성(lifespan), 라우터 등록
    ├── database.py           비동기 엔진, 세션, Base, get_async_db
    ├── security.py           비밀번호 해시, JWT 발급, get_current_user
    ├── models/
    │   ├── user.py           User (users 테이블)
    │   └── post.py           Post (posts 테이블)
    ├── schemas/
    │   ├── auth.py           UserRegister, UserResponse, Token
    │   └── post.py           PostCreate, PostUpdate, PostResponse
    └── routers/
        ├── auth.py           /register, /login, /me
        └── posts.py          /posts CRUD
```

## 테이블

| 테이블 | 컬럼                      | 제약                                        |
| ------ | ------------------------- | ------------------------------------------- |
| users  | id                        | PK                                          |
|        | username                  | UNIQUE, NOT NULL                            |
|        | hashed_password, nickname | NOT NULL                                    |
| posts  | id                        | PK                                          |
|        | title, content            | NOT NULL                                    |
|        | owner_id                  | FK → users.id (ON DELETE CASCADE), NOT NULL |

User 1 : N Post (`relationship`, `back_populates`)

## 엔드포인트

| 메서드 | 경로               | 인증   | 성공     | 실패                 |
| ------ | ------------------ | ------ | -------- | -------------------- |
| POST   | `/register`        | -      | 201      | 400 중복 아이디, 422 |
| POST   | `/login`           | -      | 200 토큰 | 401                  |
| GET    | `/me`              | 필요   | 200      | 401                  |
| POST   | `/posts`           | 필요   | 201      | 401, 422             |
| GET    | `/posts`           | -      | 200      |                      |
| GET    | `/posts/{post_id}` | -      | 200      | 404                  |
| PUT    | `/posts/{post_id}` | 작성자 | 200      | 401, 403, 404        |
| DELETE | `/posts/{post_id}` | 작성자 | 204      | 401, 403, 404        |

Swagger UI: http://127.0.0.1:8000/docs — 오른쪽 위 **Authorize**에 아이디·비밀번호를 넣으면 토큰이 붙어서 보호된 API를 바로 시험할 수 있습니다.

## 실행 방법

```
uv sync
docker-compose up -d
```

`.env.example`을 복사해 `.env`를 만들고 `SECRET_KEY`에 무작위 문자열을 넣습니다.

```
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
uv run uvicorn main:app --app-dir src --reload
```

다른 터미널에서 동작 확인:

```
uv run python scripts/smoke_test.py
```

## 인증 흐름

1. `/register`로 가입 → 비밀번호는 bcrypt 해시로 저장
2. `/login`(폼: username, password) → 30분짜리 액세스 토큰 발급
3. 요청 헤더 `Authorization: Bearer <토큰>` → `get_current_user`가 토큰을 풀어 회원을 찾음
4. 수정·삭제는 게시글의 `owner_id`가 현재 회원 id와 같을 때만 허용, 다르면 403
