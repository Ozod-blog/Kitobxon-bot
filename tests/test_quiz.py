import pytest
from app.database.models import User, Book, ReadingSession, Quiz, QuizQuestion
from app.services.quiz_service import submit_answers
@pytest.mark.asyncio
async def test_quiz_score_once(session):
    u=User(telegram_id=123,first_name="Ali",last_name="Valiyev",phone="+998901234567",region="Farg‘ona",district="Farg‘ona")
    b=Book(title="Kitob",author="Muallif",description="",total_pages=10)
    session.add_all([u,b]); await session.flush()
    r=ReadingSession(user_id=u.id,book_id=b.id,start_page=1,page_count=5,minimum_seconds=0,status="active")
    session.add(r); await session.flush()
    q=Quiz(user_id=u.id,reading_session_id=r.id,book_id=b.id); session.add(q); await session.flush()
    qs=[]
    for i in range(5):
        x=QuizQuestion(quiz_id=q.id,position=i,question=f"Savol {i}?",options_json='["a","b","c","d"]',correct_index=0); session.add(x); qs.append(x)
    await session.flush()
    result=await submit_answers(session,q.id,u.id,{x.id:0 for x in qs})
    assert result[0]==5 and result[1] is True
    with pytest.raises(ValueError): await submit_answers(session,q.id,u.id,{x.id:0 for x in qs})
