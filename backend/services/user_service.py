from typing import Optional

from backend.repositories import user_repository
from backend.schemas.user import CareerInfo, LanguageSkillInfo, UserResponseDTO


def get_user(user_id: int) -> Optional[UserResponseDTO]:
    """
    유저 ID로 프로필 전체를 조회
    careers, certifications, language_skills, document_skills, other_skills를 user_id로 조회해서 Dto로 LLM에게 전달함.
    """
    user = user_repository.find_user_by_id(user_id)

    # 없다면 LLM에게는 정보 전달 X
    if not user:
        return None

    careers = [CareerInfo(**row) for row in user_repository.find_careers_by_user_id(user_id)]
    certifications = user_repository.find_certifications_by_user_id(user_id)
    language_skills = [
        LanguageSkillInfo(**row) for row in user_repository.find_language_skills_by_user_id(user_id)
    ]
    document_skills = user_repository.find_document_skills_by_user_id(user_id)
    other_skills = user_repository.find_other_skills_by_user_id(user_id)

    return UserResponseDTO(
        id=user["id"],
        name=user["name"],
        age=user.get("age"),
        address=user.get("address"),
        careers=careers,
        certifications=certifications,
        language_skills=language_skills,
        document_skills=document_skills,
        other_skills=other_skills,
    )
