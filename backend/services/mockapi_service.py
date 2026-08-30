import httpx
from typing import Dict, Any, List, Optional
from backend.config import USERS_MOCKAPI_URL, HISTORY_MOCKAPI_URL, ADMIN_MOCKAPI_URL

class MockAPIService:
    def __init__(self):
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    # USER MOCKAPI METHODS
    async def get_users(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(USERS_MOCKAPI_URL)
            res.raise_for_status()
            return res.json()

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        users = await self.get_users()
        email_clean = email.strip().lower()
        for u in users:
            if u.get("EMAIL", "").strip().lower() == email_clean:
                return u
        return None

    async def create_user(self, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "NAME": name,
                "EMAIL": email.strip().lower(),
                "PASSWORD": password,
                "ROLE": role
            }
            res = await client.post(USERS_MOCKAPI_URL, json=payload)
            res.raise_for_status()
            return res.json()

    # HISTORY MOCKAPI METHODS
    async def get_history_by_user(self, user_id: Any) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(HISTORY_MOCKAPI_URL)
            res.raise_for_status()
            all_history = res.json()
            user_str = str(user_id)
            return [h for h in all_history if str(h.get("USER_ID")) == user_str]

    async def get_history_by_assessment_id(self, user_id: Any, assessment_id: str) -> Optional[Dict[str, Any]]:
        user_history = await self.get_history_by_user(user_id)
        for h in user_history:
            if str(h.get("ASSESSMENT_ID")) == str(assessment_id):
                return h
        return None

    async def create_history(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.post(HISTORY_MOCKAPI_URL, json=history_data)
            res.raise_for_status()
            return res.json()

    # ADMIN REVIEW MOCKAPI METHODS
    async def get_all_reviews(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(ADMIN_MOCKAPI_URL)
            res.raise_for_status()
            return res.json()

    async def get_reviews_by_user(self, user_id: Any) -> List[Dict[str, Any]]:
        all_reviews = await self.get_all_reviews()
        user_str = str(user_id)
        return [r for r in all_reviews if str(r.get("USER_ID")) == user_str]

    async def get_pending_reviews(self) -> List[Dict[str, Any]]:
        all_reviews = await self.get_all_reviews()
        return [
            r for r in all_reviews
            if r.get("APPROVED") is False or str(r.get("ADMIN_DECISION", "")).lower() == "pending"
        ]

    async def create_review_request(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Check for existing duplicate request
            all_reviews = await self.get_all_reviews()
            for r in all_reviews:
                if (str(r.get("USER_ID")) == str(review_data.get("USER_ID")) and
                    str(r.get("ASSESSMENT_ID")) == str(review_data.get("ASSESSMENT_ID")) and
                    str(r.get("BUILDING_ID")) == str(review_data.get("BUILDING_ID"))):
                    return r # return existing request without duplicating
            
            res = await client.post(ADMIN_MOCKAPI_URL, json=review_data)
            res.raise_for_status()
            return res.json()

    async def update_review(self, review_id: Any, update_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{ADMIN_MOCKAPI_URL}/{review_id}"
            res = await client.put(url, json=update_data)
            res.raise_for_status()
            return res.json()

mockapi_service = MockAPIService()
