from . import db, ma
from sqlalchemy.dialects.postgresql import JSON
import datetime


class Scalar(db.Model):
    """Model for hyperslab scalars."""

    __tablename__ = 'scalars'
    id = db.Column(db.Integer,
                   primary_key=True)
    region = db.Column(db.String(64),
                       index=False,
                       unique=False,
                       nullable=False)
    metric = db.Column(db.String(80),
                       index=False,
                       unique=False,
                       nullable=False)
    scalar = db.Column(db.String(80),
                       index=False,
                       unique=False,
                       nullable=False)
    model = db.Column(db.String(80),
                      index=False,
                      unique=False,
                      nullable=False)
    value = db.Column(db.String(80),
                      index=False,
                      unique=False,
                      nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<region: {} metric: {} scalar: {} model: {}>'.format(self.region, self.metric, self.scalar, self.model)


class ScalarSchema(ma.ModelSchema):
    class Meta:
        model = Scalar
        exclude = ('id', 'created_date')
