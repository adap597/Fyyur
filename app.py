
# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, \
    redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from sqlalchemy import func
import re

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

# connect to a local postgresql database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'any secret string'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://[username]:[password]@localhost:5432/fyyurapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

from models import *


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = 'EE MM, dd, y h:mma'
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

# home page route handler

@app.route('/')
def index():
    return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------

# Venues homepage route handler
# See https://hackersandslackers.com/database-queries-sqlalchemy-orm/

@app.route('/venues')
def venues():
    data = []

  # select query to return all venues

    venues = Venue.query.all()

  # See https://stackoverflow.com/questions/22275412/sqlalchemy-return-all-distinct-column-values
  # See https://stackoverflow.com/questions/47192428/what-is-the-difference-between-with-entities-and-load-only-in-sqlalchemy/49141439
  # query to find disctinct city, state values

    for area in Venue.query.with_entities(Venue.city,
            Venue.state).distinct().all():
        data.append({'city': area.city, 'state': area.state,
                    'venues': [{'id': venue.id, 'name': venue.name}
                    for venue in venues if venue.city == area.city
                    and venue.state == area.state]})
    return render_template('pages/venues.html', areas=data)


#  ----------------------------------------------------------------
#  Venues Search
#  ----------------------------------------------------------------

# search venues route handler

@app.route('/venues/search', methods=['POST'])
def search_venues():

  # search on artists with partial string search. It is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')

  # venue select query based on search term
  # See https://kb.objectrocket.com/postgresql/how-to-use-ilike-in-postgres-1258
  # ilike operator allows case insensitive pattern matching.
  # This allows us to search with partial strings and return applicable results

    venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%'
                                )).all()

    venue_data = []

  # loop through venue results

    for venue in venues:
        venue_data.append({'id': venue.id, 'name': venue.name,
                          'num_upcoming_shows': 0})

  # provide number of items in result and venue information for each result
  # (i.e. Number of search results for "search term": 1 )

    response = {'count': len(venues), 'data': venue_data}

  # return search page (from Udacity starter code)

    return render_template('pages/search_venues.html',
                           results=response,
                           search_term=request.form.get('search_term',
                           ''))


#  ----------------------------------------------------------------
#  Show Venues
#  ----------------------------------------------------------------

# Show venue route handler

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  # shows the venue page with the given venue_id
  # select query to get venues by their id
  # select query to get shows filtered by venue id

    venue = Venue.query.get(venue_id)
    #shows = Show.query.filter_by(venue_id=venue_id).all()
    #upcoming_shows_venue = []

    past_shows_venue_query = Show.query.filter_by(venue_id=venue_id).join(Artist).filter(Show.start_time>datetime.now()).all()
    past_shows_venue = []

    upcoming_shows_venue_query = Show.query.filter_by(venue_id=venue_id).join(Venue).filter(Show.start_time<datetime.now()).all()
    upcoming_shows_venue = []

    for show in past_shows_venue_query:
        past_shows_venue.append({
            'artist_id': show.artist_id,
            'artist_name':show.artist.name,
            'artist_image_link':show.artist.image_link,
            'start_time': str(show.start_time)

        })

    for show in upcoming_shows_venue_query:
        upcoming_shows_venue.append({
            'artist_id': show.artist_id,
            'artist_name':show.artist.name,
            'artist_image_link':show.artist.image_link,
            'start_time': str(show.start_time)

        })
    

  # See https://hackersandslackers.com/database-queries-sqlalchemy-orm/

    #for show in shows:
        #show_data = {
            #'artist_id': show.artist_id,
            #'artist_name': Artist.query.filter_by(id=show.artist_id).first().name,
            #'artist_image_link': Artist.query.filter_by(id=show.artist_id).first().image_link,
            #'start_time': str(show.start_time),
            #}
        #if show.start_time > datetime.now():
            #upcoming_shows_venue.append(show_data)
        #else:
            #past_shows_venue.append(show_data)

  # venue data

    venue_data = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_shows_venue,
        'upcoming_shows': upcoming_shows_venue,
        'past_shows_count': len(past_shows_venue),
        'upcoming_shows_count': len(upcoming_shows_venue),
        }

  # return show venue page

    return render_template('pages/show_venue.html', venue=venue_data)


#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------

# create venue route handler

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()

    return render_template('forms/new_venue.html', form=form)


# See https://www.askpython.com/python-modules/flask/flask-crud-application

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    if form.validate_on_submit():
        form = form
    else:
        for error in form.errors:
            flash(error)

        return render_template('forms/new_venue.html', form=form)

    if request.method == 'POST':
        try:

    # get all data from the create venue form

            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            address = request.form['address']
            phone = request.form['phone']
            genres = request.form['genres']
            facebook_link = request.form['facebook_link']
            website = request.form['website_link']
            image_link = request.form['image_link']
            seeking_talent = (True if 'seeking_talent'
                              in request.form else False)
            seeking_description = request.form['seeking_description']

    # create new venue and add record to database

            venue = Venue(
                name=name,
                city=city,
                state=state,
                address=address,
                phone=phone,
                genres=genres,
                facebook_link=facebook_link,
                website=website,
                image_link=image_link,
                seeking_talent=seeking_talent,
                seeking_description=seeking_description,
                )
            db.session.add(venue)
            db.session.commit()

      # flash message if add is successful

            flash('Venue ' + request.form['name']
                  + ' was successfully listed!')
        except:

      # flash message if add was not successful

            flash('An error occurred. Venue ' + request.form['name']
                  + ' could not be listed.')
            db.session.rollback()
            #print sys.exc_info()
        finally:

      # close session

            db.session.close()

  # return to homepage

    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Edit Venue
#  ----------------------------------------------------------------

# edit venue route handler

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

# query to retrieve venue by id
# using .first() returns the first result essentially setting LIMIT to 1

    venue = Venue.query.filter_by(id=venue_id).first()

# set attributes

    venue = {
        'id': venue_id,
        'name': venue.name,
        'genres': venue.genres,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        }

  # use process_data to fill form with existing data
  # May make it easier for user to update the record if some fields like venue name are prefilled
  # See https://wtforms.readthedocs.io/en/2.3.x/fields/

    form.name.process_data(venue['name'])
    form.state.process_data(venue['state'])
    form.city.process_data(venue['city'])

  # return edit venue form

    return render_template('forms/edit_venue.html', form=form,
                           venue=venue)


# See https://www.askpython.com/python-modules/flask/flask-crud-application
# See https://www.blog.pythonlibrary.org/2017/12/14/flask-101-adding-editing-and-displaying-data/

@app.route('/venues/<int:venue_id>/edit', methods=['GET', 'POST'])
def edit_venue_submission(venue_id):
    try:
        form = VenueForm()

    # query to retrieve venue by id
    # using .first() returns the first result essentially setting LIMIT to 1

        venue = Venue.query.filter_by(id=venue_id).first()

    # get data from the form and assign to attributes

        venue.name = form.name.data
        venue.genres = form.genres.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.image_link = form.image_link.data
        venue.seeking_talent = (True if form.seeking_talent.data
                                == 'Yes' else False)
        venue.seeking_description = form.seeking_description.data

    # commit changes, flash message if successful

        db.session.commit()
        flash('Venue ' + request.form['name']
              + ' was successfully updated!')
    except:

    # catch errors, flash message if not successful

        db.session.rollback()
        flash('There was an error. Venue ' + request.form['name']
              + ' could not be updated.')
    finally:

    # close the session

        db.session.close()

  # return redirect to venue page

    return redirect(url_for('show_venue', venue_id=venue_id))


#  ----------------------------------------------------------------
#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>/edit/delete', methods=['POST'])
def delete_venue(venue_id):

  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # clicking delete button deletes it from the db then redirect the user to the homepage
  # flash messages for success or failure

    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + request.form.name
              + ' was successfully deleted!')
    except:
        flash('An error occurred. Venue ' + request.form.name
              + ' could not be deleted.')
        db.session.rollback()
        #print sys.exc_info()
    finally:
        db.session.close()
    return redirect(url_for('venues'))


#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html', artists=artists)


#  ----------------------------------------------------------------
#  Artist Search
#  ----------------------------------------------------------------

@app.route('/artists/search', methods=['POST'])
def search_artists():

  # search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term', '')

  # See https://kb.objectrocket.com/postgresql/how-to-use-ilike-in-postgres-1258
  # ilike operator allows case insensitive pattern matching.
  # This allows us to search with partial strings and return applicable results

    artists = Artist.query.filter(Artist.name.ilike('%' + search_term
                                  + '%')).all()

    artist_data = []

  # loop through results

    for artist in artists:
        artist_data.append({'id': artist.id, 'name': artist.name,
                           'num_upcoming_shows': 0})

  # provide number of items in result and venue information for each result
  # (i.e. Number of search results for "search term": 1 )

    response = {'count': len(artists), 'data': artist_data}

    return render_template('pages/search_artists.html',
                           results=response,
                           search_term=request.form.get('search_term',
                           ''))


#  ----------------------------------------------------------------
#  Show Artist
#  ----------------------------------------------------------------

# show artist route handler

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  # shows the artist page with the given artist_id
  # select query to get artist by their id
  # select query to get shows filtered by artist id

    #alternate implementation
    artist = Artist.query.get(artist_id)
    #shows = Show.query.filter_by(artist_id=artist_id).all()
    #upcoming_shows_artist = []
    #past_shows_artist = []

    past_shows_artist_query = Show.query.filter_by(artist_id=artist_id).join(Venue).filter(Show.start_time>datetime.now()).all()
    past_shows_artist = []

    upcoming_shows_artist_query = Show.query.filter_by(artist_id=artist_id).join(Venue).filter(Show.start_time<datetime.now()).all()
    upcoming_shows_artist = []

    for show in past_shows_artist_query:
        past_shows_artist.append({
            'venue_id': show.venue_id,
            'venue_name':show.venue.name,
            'venue_image_link':show.venue.image_link,
            'start_time': str(show.start_time)

        })

    for show in upcoming_shows_artist_query:
        upcoming_shows_artist.append({
            'venue_id': show.venue_id,
            'venue_name':show.venue.name,
            'venue_image_link':show.venue.image_link,
            'start_time': str(show.start_time)

        })

  # See https://hackersandslackers.com/database-queries-sqlalchemy-orm/
    #alternate implementation
    #for show in shows:
        #show_data = {
            #'venue_id': show.venue_id,
            #'venue_name': Venue.query.filter_by(id=show.venue_id).first().name,
            #'venue_image_link': Venue.query.filter_by(id=show.venue_id).first().image_link,
            #'start_time': str(show.start_time),
            #}
        #if show.start_time > datetime.now():
            #upcoming_shows_artist.append(show_data)
        #else:
            #past_shows_artist.append(show_data)

  # artist data

    artist_data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'album': artist.album,
        'single': artist.single,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows_artist,
        'upcoming_shows': upcoming_shows_artist,
        'past_shows_count': len(past_shows_artist),
        'upcoming_shows_count': len(upcoming_shows_artist),
        }
    return render_template('pages/show_artist.html', artist=artist_data)


#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

# creat artist route handler

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()


    return render_template('forms/new_artist.html', form=form)


# See https://www.askpython.com/python-modules/flask/flask-crud-application
# See https://www.blog.pythonlibrary.org/2017/12/14/flask-101-adding-editing-and-displaying-data/

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    if form.validate_on_submit():
        form = form
    else:
        for error in form.errors:
            flash(error)

        return render_template('forms/new_artist.html', form=form)
    if request.method == 'POST':
        try:

    # get all data from the create artist form

        
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            phone = request.form['phone']
            genres = request.form['genres']
            facebook_link = request.form['facebook_link']
            website = request.form['website_link']
            album = request.form['album']
            single = request.form['single']
            image_link = request.form['image_link']
            seeking_venue = (True if 'seeking_venue'
                         in request.form else False)
            seeking_description = request.form['seeking_description']

     # create new artist and add it to the database

            artist = Artist(
                name=name,
                city=city,
                state=state,
                phone=phone,
                genres=genres,
                facebook_link=facebook_link,
                website=website,
                album=album,
                single=single,
                image_link=image_link,
                seeking_venue=seeking_venue,
                seeking_description=seeking_description,
                )
            db.session.add(artist)
            db.session.commit()

    # flash message if successful

            flash('Artist ' + request.form['name']
              + ' was successfully listed!')
        except:

    # flash message if not succesful

            flash('An error occurred. Artist ' + request.form['name']
              + ' could not be listed.')
            db.session.rollback()
        #print sys.exc_info()
        finally:
            db.session.close()

  # return to homepage

    return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Edit Artist
#  ----------------------------------------------------------------

# edit artist route handler

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

  # select query to get artist by it
  # using .first() returns the first result essentially setting LIMIT to 1

    artist = Artist.query.filter_by(id=artist_id).first()

  # set attributes

    artist = {
        'id': artist_id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'album': artist.album,
        'single':artist.single,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        }

  # use process_data to fill form with existing data
  # May make it easier for user to update the record if some fields like venue name are prefilled
  # See https://wtforms.readthedocs.io/en/2.3.x/fields/

    form.name.process_data(artist['name'])
    form.state.process_data(artist['state'])
    form.city.process_data(artist['city'])

    return render_template('forms/edit_artist.html', form=form,
                           artist=artist)


# See https://www.blog.pythonlibrary.org/2017/12/14/flask-101-adding-editing-and-displaying-data/

@app.route('/artists/<int:artist_id>/edit', methods=['GET', 'POST'])
def edit_artist_submission(artist_id):

  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

    try:
        form = ArtistForm()

    # get artist by id
    # using .first() returns the first result essentially setting LIMIT to 1

        artist = Artist.query.filter_by(id=artist_id).first()

    # get data from the form and assign to attributes

        artist.name = form.name.data
        artist.genres = form.genres.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.website = form.website.data
        artist.album = form.album.data
        artist.single = form.single.data
        artist.image_link = form.image_link.data
        artist.seeking_venue = (True if 'seeking_venue'
                                in request.form else False)
        artist.seeking_description = form.seeking_description.dat

        db.session.commit()

    # flash message if edit successful

        flash('Artist ' + request.form['name']
              + ' was successfully updated!')
    except:

    # flash message if edit was not successful

        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name']
              + ' could not be updated.')
    finally:

    # close session

        db.session.close()

  # redirect to artist page

    return redirect(url_for('show_artist', artist_id=artist_id))


#  ----------------------------------------------------------------
#  Delete Artist
#  ----------------------------------------------------------------

# delete artists route handler

@app.route('/artists/<artist_id>/edit/delete', methods=['POST'])
def delete_artist(artist_id):

  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # clicking delete button deletes it from the db then redirects the user to the homepage

    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash('Artist was successfully deleted.')
    except:
        flash('An error occurred. Artist could not be deleted.')
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('artists'))


#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

# shows homepage route handler

@app.route('/shows')
def shows():

    show_data = []

  # query to get all shows

    shows = Show.query.all()

  # loop through results

    for show in shows:
        show_data.append({
            'venue_id': show.venue_id,
            'venue_name': Venue.query.filter_by(id=show.venue_id).first().name,
            'artist_id': show.artist_id,
            'artist_name': Artist.query.filter_by(id=show.artist_id).first().name,
            'artist_image_link': Artist.query.filter_by(id=show.artist_id).first().image_link,
            'start_time': str(show.start_time),
            })

    return render_template('pages/shows.html', shows=show_data)


#  ----------------------------------------------------------------
#  Create Shows
#  ----------------------------------------------------------------

# create show route handler

@app.route('/shows/create')
def create_shows():

  # renders form. do not touch.

    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:

    # get form data

        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']

    # create a new show and add to the database

        show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time)

        db.session.add(show)
        db.session.commit()

    # flash message if successful

        flash('Show was successfully posted!')
    except:
        db.session.rollback()

    # flash message if not successful

        flash('An error occurred. Show could not be posted.')
        #print sys.exc_info()
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Error handlers
#  ----------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return (render_template('errors/404.html'), 404)


@app.errorhandler(500)
def server_error(error):
    return (render_template('errors/500.html'), 500)

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                              ))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:

if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
