from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="로그인용 사용자 ID")
    password: str = Field(..., min_length=4, description="사용자 비밀번호 (평문)")
    nickname: str = Field(..., min_length=2, max_length=20, description="화면에 표시될 닉네임")


class UserResponse(BaseModel):
    id: int = Field(..., description="사용자 고유 식별자 (ID)")
    username: str = Field(..., description="사용자 ID")
    nickname: str = Field(..., description="사용자 닉네임")

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str = Field(..., description="발급된 JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
