import asyncio
from backend.db.session import AsyncSessionLocal
from backend.models.coding_challenge import CodingChallenge
from sqlalchemy import select

async def update_db():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CodingChallenge))
        challenges = result.scalars().all()
        for ch in challenges:
            if not ch.template_code: continue
            updated = False
            new_tc = dict(ch.template_code)
            for lang, code in new_tc.items():
                if isinstance(code, str) and '/dev/stdin' in code:
                    new_tc[lang] = code.replace('/dev/stdin', '0')
                    updated = True
            if updated:
                ch.template_code = new_tc
                db.add(ch)
        await db.commit()
        print("Updated successfully")

if __name__ == "__main__":
    asyncio.run(update_db())
