from application import db
from datetime import datetime
# from marshmallow_sqlalchemy import ModelSchema
# from marshmallow import fields



# declare a class as Users which will hold the schema for the users table:
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    hash = db.Column(db.String(100))
    cash = db.Column(db.Numeric)
    # shares = db.relationship('Share', backref='user')
    # history = db.relationship('History', backref='user')

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self
      
    def __init__(self,username,hash,cash):
        self.username = username
        self.hash = hash
        self.cash = cash

    # def __repr__(self):
    #     return '' % self.id\
# instructs the application to create all the tables and database specified in the application.
db.create_all()

# class UserSchema(ModelSchema):
#     class Meta(ModelSchema.Meta):
#         model = User
#         sqla_session = db.session
#     id = fields.Number(dump_only=True)
#     username = fields.String(required=True)


# declare a class as Share which will hold the schema for the shares table:
class Share(db.Model):
    __tablename__ = "shares"
    id = db.Column(db.Integer, primary_key=True)
    shares_name = db.Column(db.String(100))
    shares_no = db.Column(db.Numeric)
    total_price = db.Column(db.Numeric)
    created_at = db.Column(db.DateTime,default=datetime.utcnow)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self
    def __init__(self,shares_name,shares_no,total_price,user_id):
        self.shares_name = shares_name
        self.shares_no = shares_no
        self.total_price = total_price
        self.user_id = user_id
    # def __repr__(self):
    #     return '' % self.id\
# instructs the application to create all the tables and database specified in the application.
db.create_all()


# class ShareSchema(ModelSchema):
#     class Meta(ModelSchema.Meta):
#         model = Share
#         sqla_session = db.session
#     id = fields.Number(dump_only=True)
#     shares_name = fields.String(required=True)


# declare a class as History which will hold the schema for the history table:
class History(db.Model):
    __tablename__ = "history"
    id = db.Column(db.Integer, primary_key=True)
    shares_name = db.Column(db.String(100))
    shares_no = db.Column(db.Numeric)
    price = db.Column(db.Numeric)
    status = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime,default=datetime.utcnow)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self
    def __init__(self,shares_name,shares_no,price,status,user_id):
        self.shares_name = shares_name
        self.shares_no = shares_no
        self.price = price
        self.status = status
        self.user_id = user_id
    # def __repr__(self):
    #     return '' % self.id\
# instructs the application to create all the tables and database specified in the application.
db.create_all()

# class HistorySchema(ModelSchema):
#     class Meta(ModelSchema.Meta):
#         model = History
#         sqla_session = db.session
#     id = fields.Number(dump_only=True)
#     shares_name = fields.String(required=True)
