from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_serializer import SerializerMixin
from db_session import SqlAlchemyBase


class History(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer)
    body = Column(String, nullable=False)
    date = Column(DateTime)

    def __repr__(self):
        return f"<id {self.id}>"

    def get_dict(self):
        return {"body": self.body}
