from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_serializer import SerializerMixin
from db_session import SqlAlchemyBase


class Items(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "items"
    id = Column(String, primary_key=True)
    url = Column(String)
    size = Column(Integer)
    type = Column(String, nullable=False)
    parentId = Column(String)
    date = Column(DateTime)

    def __repr__(self):
        return f"<id {self.id}>"

    def get_dict(self):
        return {"id": self.id, "url": self.url,
                "size": self.size, "type": self.type,
                "parentId": self.parentId, "date": self.date.strftime("%Y-%m-%dT%H:%M:%SZ")}
