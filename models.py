import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys 
from app import db

# Venue model
class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
  website = db.Column(db.String(500))
  seeking_talent = db.Column(db.Boolean, default=False)
  seeking_description = db.Column(db.String(120))
  shows = db.relationship('Show', backref='venue', lazy=True)

  def __repr__(self):
      return f'<Venue {self.id} {self.name}>'


# Artist model
class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120))
  genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(500))
  album = db.Column(db.String(500))
  seeking_venue = db.Column(db.Boolean, default=False)
  seeking_description = db.Column(db.String(120))
  shows = db.relationship('Show', backref='artist', lazy=True)

  def __repr__(self):
      return f'<Artist {self.id} {self.name}>'


# Show model
class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey(
      'Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False,
                        default=datetime.utcnow)

  def __repr__(self):
    return f'<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>'