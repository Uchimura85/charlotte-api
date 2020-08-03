from datetime import datetime
from pytz import timezone
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, ValidationError
from untitled.exceptions import InvalidUsage
from untitled.helpers import extract_title_from_url

# Initially, the database isn't bound to an app. This is so
# we can bind to one while our app is being created in our
# app factory.
db = SQLAlchemy()

# ORM Models:

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(512), nullable=False)
    links = db.relationship('Link', backref='user', lazy=True)

    def __repr__(self):
        return '<User: {} [{}]>'.format(self.name, self.id)

    def create_link(self, url=None, title=None, **kwargs):
        """Adds a link to the database for the given user.
        If the title attribute is None, will call a helper function to
        attempt to scrape the title from the HTML of the website passed in.
        Will also raise an exception if the URL ended up being invalid.

        Returns the ID of the link entry in the database if successful.
        """
        
        # Load into the Link schema to catch any errors. We'll catch ValidationErrors
        # at the blueprint level:
        data = LinkSchema().validate(dict(user_id=self.id, title=title, url=url))
        
        # Try and extract our title from the URL if it's not provided.
        # If the title can't be extracted, a value of None is still okay.
        if title is None:
            title = extract_title_from_url(url)

        # Add this link to the database:
        link = Link(user_id=self.id, title=title, url=url)
        db.session.add(link)
        db.session.commit()
        return link.id


class Link(db.Model):
    __tablename__ = 'link'

    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.now())
    url = db.Column(db.String(2048), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(512), nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<Link: {} [{}]>'.format(self.url, self.id)

    def to_dict(self):
        """Returns a dict representation of a saved link.
        """
        return {
            'id': self.id,
            'date_added': self.date_added.replace(tzinfo=timezone('America/Toronto')).strftime('%Y-%m-%d %I:%M %p %Z'),
            'url': self.url,
            'title': self.title,
            'read': self.read
        }


# Schema:

class UserSchema(Schema):
    id = fields.Int(strict=True, required=True)
    name = fields.Str(required=True)
    # Setting api_key as load_only ensures any dumps don't contain it:
    api_key = fields.Str(required=True, load_only=True)


class LinkSchema(Schema):
    id = fields.Int(strict=True, required=True, dump_only=True)
    date_added = fields.DateTime(format="%Y-%m-%d %I:%M %p %Z")
    url = fields.URL(required=True, relative=False)
    user_id = fields.Int(strict=True, required=True, load_only=True)
    title = fields.Str(allow_none=True)
    read = fields.Bool(default=False)
