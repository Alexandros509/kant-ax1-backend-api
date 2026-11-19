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
├── docker-compose.prod.yml   서버 배포용 (앱 + DB, DB 포트 비공개)
├── Dockerfile, .dockerignore 앱 이미지 빌드
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

## 배포 (AWS EC2 + Docker Compose)

EC2 한 대에 앱과 DB를 함께 띄우는 최소 구성입니다.

1. EC2 생성: Ubuntu 24.04, 보안그룹 인바운드는 22(내 IP만)와 8000만 엽니다. 5432는 열지 않습니다.
2. 서버 준비 후 코드 받기:

```
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker ubuntu   # 로그아웃 후 다시 접속
git clone https://github.com/Alexandros509/kant-ax1-backend-api.git
cd kant-ax1-backend-api
```

3. 서버용 `.env` 작성 (로컬 값을 복사하지 말고 새 무작위 값 사용):

```
POSTGRES_PASSWORD=<무작위 값>
DATABASE_URL=postgresql+asyncpg://postgres:<같은 값>@db:5432/postgres
SECRET_KEY=<무작위 값>
```

4. 실행과 확인:

```
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs app
```

`http://<퍼블릭IP>:8000/docs`가 열리면 로컬 PC에서 서버 대상으로 동작 확인을 합니다.

```
$env:BASE_URL = "http://<퍼블릭IP>:8000"; uv run python scripts/smoke_test.py
```

주의: HTTP만 쓰므로 비밀번호와 토큰이 평문으로 전송됩니다. 시연 후에는 인스턴스를 종료(Terminate)해 요금이 나가지 않게 합니다.

## 인증 흐름

1. `/register`로 가입 → 비밀번호는 bcrypt 해시로 저장
2. `/login`(폼: username, password) → 30분짜리 액세스 토큰 발급
3. 요청 헤더 `Authorization: Bearer <토큰>` → `get_current_user`가 토큰을 풀어 회원을 찾음
4. 수정·삭제는 게시글의 `owner_id`가 현재 회원 id와 같을 때만 허용, 다르면 403
