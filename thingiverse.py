# Copyright (c) 2014 Erin RobotGrrl <erin@robotgrrl.com>, MIT license
import sys
from rauth import OAuth2Service
import webbrowser
import urllib2
from time import sleep
import json
import requests
import logging


class Thingiverse:

    def __init__(self, appinfo, loglevel='info'):
        """
        appinfo = {'client_id': 'your client id',
                   'client_secret': 'your client secret',
                   'redirect_uri': 'your redirect url'}
        """
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)

        self.EXIT = True

        logging.debug('Thingiverse!')

        self._appinfo = appinfo
        self._service = 0
        self._access_code = ''
        self._session = 0

        self._r2 = 0
        self._retry_request = False
        self._retry_count = 0

        self._parse_result = True
        self._initialize_list = True

        # thing id, user id, thing name, creator name
        self.things = [[], [], [], []]
        self._new_count = 0

        self.seen_things_count = 0

        self.txt_url_mode = False

    # HTTP Request Helpers

    def _get_it(self, endpoint, data):
        r = self._session.get(self._service.base_url + endpoint, params=data)
        return r.json()

    def _post_it(self, endpoint, data):
        r = self._session.post(self._service.base_url + endpoint, data=data)
        return r.json()

    def _delete_it(self, endpoint, data):
        r = self._session.delete(self._service.base_url + endpoint, data=data)
        return r.json()

    def _patch_it(self, endpoint, data):

        # headers = {'Authorization: Bearer': self._access_code,
        #             'Host': 'api.thingiverse.com',
        #             'Content-Type': 'application/json'}

        r = self._session.patch(
            self._service.base_url + endpoint, data=json.dumps(data))
        return r.json()

    # Authentication Related

    def _fetch_access_code(self):
        logging.debug('fetch_access_code')
        self._access_code = raw_input("access token: >")

    def _get_access_code(self, token=''):
        logging.debug('get_access_code')

        # self._service = OAuth2Service(
        #     name='thingiverse',
        #     client_id='719ce807b9ceac053033',
        #     client_secret='45d1bb0958c45b7716e671ebe5723ace',
        #     access_token_url='https://www.thingiverse.com/login/oauth/access_token',
        #     authorize_url='https://www.thingiverse.com/login/oauth/authorize',
        #     base_url='https://api.thingiverse.com')

        # perplexedphoenix
        self._service = OAuth2Service(
            name='thingiverse',
            client_id=self._appinfo['client_id'],
            client_secret=self._appinfo['client_secret'],
            access_token_url='https://www.thingiverse.com/login/oauth/access_token',
            authorize_url='https://www.thingiverse.com/login/oauth/authorize',
            base_url='https://api.thingiverse.com')

        if not token:
            # let's get the url to go to
            params = {'redirect_uri': self._appinfo['redirect_uri'],
                      'response_type': 'code'}
            url = self._service.get_authorize_url(**params)

            # nope
            # req = urllib2.Request(url)
            # fd = urllib2.urlopen(req)
            # data = fd.readlines()
            # fd.close()
            # print data

            logging.info(url)
    
            if self.txt_url_mode == False:
                webbrowser.open_new(url)

            else:
                f = open('url.txt', 'w')
                f.write(url)
                f.close()
                sleep(30.0)

            self._fetch_access_code()

    def _get_session(self, token=''):
        logging.debug('get_session')
        if token:
            self._session = self._service.get_session(token=token)
        else:
            # now we can ask for an access token
            # it's given to us after we retrieve it from the above url

            data = {'client_id': self._service.client_id,
                    'client_secret': self._service.client_secret,
                    'code': self._access_code}

            logging.debug(data)

            try:
                self._session = self._service.get_auth_session(data=data)
                logging.debug(self._session.access_token)
            except KeyError as e:
                logging.debug(str(e))
                logging.debug('key error, going to try to get it again')
                self._fetch_access_code()
                self._get_session()

    def connect(self, token=''):
        self._get_access_code(token=token)
        self._get_session(token=token)

    # Misc

    def send_request(self):
        logging.debug('send_request')

        try:
            self._r2 = self._session.get(
                self._service.base_url + '/newest/', params={'format': 'json'})

            if self._retry_request == True:
                logging.debug('saved ourselves from the error!')

            self._retry_count = 0
            self._retry_request = False
            self._parse_result = True

        except requests.exceptions.RequestException as e:
            logging.debug(str(e))
            logging.debug('Error %d: %s' %
                          (self._r2.status_code, self._r2.reason))
            if self._retry_count == 0:
                self._retry_request = True
                self._retry_count += 1
            elif self._retry_count == 1:
                self._retry_request = False
                raise e

        except AttributeError as e:
            logging.debug(str(e))
            self._fetch_access_code()

    def _check_request(self):
        logging.debug('check_request')

        if self._retry_request == True:
            self.send_request()

    def _go_initialize_list(self):
        logging.debug('_go_initialize_list')

        thing_id = ''
        user_id = ''
        thing_name = ''
        user_name = ''

        for i in range(0, 10):
            new = self._r2.json()[i]

            for key, value in new.items():
                if key == 'id':
                    thing_id = value
                elif key == 'name':
                    thing_name = value
                elif key == 'creator':
                    for key2, value2 in value.items():
                        if key2 == 'id':
                            user_id = value2
                        elif key2 == 'name':
                            user_name = value2

            self.things[0].append(thing_id)
            self.things[1].append(user_id)
            self.things[2].append(thing_name)
            self.things[3].append(user_name)

        self._initialize_list = False

    def _find_new(self):
        logging.debug('_find_new')

        thing_id = ''
        user_id = ''
        thing_name = ''
        user_name = ''

        try:
            new = self._r2.json()[self._new_count]
        except ValueError as e:
            logging.debug(str(e))
            return

        for key, value in new.items():
                if key == 'id':
                    thing_id = value
                elif key == 'name':
                    thing_name = value
                elif key == 'creator':
                    for key2, value2 in value.items():
                        if key2 == 'id':
                            user_id = value2
                        elif key2 == 'name':
                            user_name = value2

        if self._new_count > len(self.things[0]) - 1:
            logging.debug('bizarre- new_count (%d) is > len(things[0]) (%d)' % (
                self._new_count, len(self.things[0]) - 1))
            # let's try to reset it?
            self._new_count = 0
            self._find_new()
            return

        if thing_id != self.things[0][self._new_count]:
            self.things[0].pop()
            self.things[1].pop()
            self.things[2].pop()
            self.things[3].pop()

            self.things[0].insert(self._new_count, thing_id)
            self.things[1].insert(self._new_count, user_id)
            self.things[2].insert(self._new_count, thing_name)
            self.things[3].insert(self._new_count, user_name)

            self._new_count += 1
            self._find_new()

    def refresh_new(self):
        logging.debug('refresh_new')

        thing_id = ''
        user_id = ''
        thing_name = ''
        user_name = ''

        self.send_request()
        self._check_request()

        if self._parse_result == True:

            if self._initialize_list == True:
                self._go_initialize_list()
            else:
                self._find_new()

            if self._new_count == 0:
                twiddleloo = 1
            else:
                for i in range(0, self._new_count):
                    logging.debug("%d: new thing: %s (%s) by %s" %
                                  (self.seen_things_count, self.things[2][i], self.things[0][i], self.things[3][i]))
                    self.seen_things_count += 1
                self._new_count = 0

    # Users

    def get_profile(self, user):
        """
        get a user's profile
        returns the user
        """
        logging.debug('get_profile')
        s = "/users/%s"
        return self._get_it(s, None)

    def update_profile(self, user, data):
        """
        update a user's profile
        data = {'first_name': 'the first name',
               'last_name': 'the last name',
               'bio': 'the amazing biography',
               'location': 'your location',
               'default_license': 'cc or cc-sa, etc'}
        (all of the data parameters are optional)
        returns the updated user
        """
        logging.debug('update_profile')
        s = "/users/%s" % (user)
        return self._patch_it(s, data)

    def get_things_user(self, user):
        """
        get list of user's own things
        returns thing objects
        404 not found if user doesn't exist
        """
        logging.debug('get_things_user')
        s = "/users/%s/things" % (user)
        return self._get_it(s, None)

    def get_likes_user(self, user):
        """
        get things liked by a user
        returns thing objects
        404 not found if user doesn't exist
        """
        logging.debug('get_likes_user')
        s = "/users/%s/likes" % (user)
        return self._get_it(s, None)

    def get_copies_user(self, user):
        """
        get latest copies ('makes') by a user
        returns copy objects
        404 not found if user doesn't exist
        """
        logging.debug('get_copies_user')
        s = "/users/%s/copies" % (user)
        return self._get_it(s, None)

    def get_collections_user(self, user):
        """
        get latest collections by a user
        returns collection objects
        404 not found if user doesn't exist
        """
        logging.debug('get_collections_user')
        s = "/users/%s/collections" % (user)
        return self._get_it(s, None)

    def get_downloads_user(self, user):
        """
        get latest downloads by a user
        returns thing objects
        404 not found if user doesn't exist
        """
        logging.debug('get_downloads_user')
        s = "/users/%s/downloads" % (user)
        return self._get_it(s, None)

    def add_apn(self, user, data):
        """
        add a push notification device
        data = {'type': 'apn',
                   'id': 'apple device UUID'}
        returns the "ok" object
        """
        logging.debug('add_apn')
        s = "/users/%s/notifier" % (user)
        return self._post_it(s, data)

    def get_tokens_user(self, user):
        """
        mystery?
        returns none
        """
        logging.debug('get_tokens_user')
        s = "/users/%s/downloads" % (user)
        return self._get_it(s, None)

    def remove_apn(self, user, data):
        """
        remove a push notification device
        data = {'type': 'apn',
                   'id': 'apple device UUID'}
        returns the "ok" object
        """
        logging.debug('remove_apn')
        s = "/users/%s/notifier" % (s)
        return self._delete_it(s, data)

    def follow_user(self, user):
        """
        follow a user
        returns the "ok" object
        404 not found if user doesn't exist
        400 bad request if user tries to follow themselves
        """
        logging.debug('follow_user')
        s = "/users/%s/followers" % (s)
        return self._post_it(s, None)

    def unfollow_user(self, user):
        """
        unfollow a user
        returns the "ok" object
        404 not found if user doesn't exist
        """
        logging.debug('unfollow_user')
        s = "/users/%s/followers" % (user)
        return self._delete_it(s, None)

    def update_avatar(self, user, data):
        """
        update user's avatar image
        data = {'filename': 'photo.png'}
        returns the data needed to upload a file via an HTTP POST,
        with multipart/form-data encoding
        """
        logging.debug('update_avatar')
        s = "/users/%s/avatarimage" % (user)
        return self._post_it(s, data)

    def update_cover(self, user, data):
        """
        update user's cover image
        data = {'filename': 'photo.png'}
        returns the data needed to upload a file via an HTTP POST,
        with multipart/form-data encoding
        """
        logging.debug('update_cover')
        s = "/users/%s/coverimage" % (user)
        return self._post_it(s, data)

    # Things

    def get_thing(self, thing):
        """
        gets a thing by its id
        returns a thing object
        401 unauthourized if unpublished thing
        403 forbidden if unpublished thing you do not own
        404 not found if invalid or deleted thing
        """
        logging.debug('get_thing')
        s = "/things/%d/" % (thing)
        return self._get_it(s, None)

    def get_thing_image(self, thing, img):
        """
        get summary info for all the images of a thing,
        or more detailed info about a specific image
        returns an array of imagess or detailed info
        """
        logging.debug('get_thing_image')
        s = "/things/%d/images/%d" % (thing, img)
        return self._get_it(s, None)

    def update_thing_image(self, thing, img, data):
        """
        update an existing image on a thing
        data = {'rank': 1,
                   'featured': True}
        returns the "ok" object
        """
        logging.debug('update_thing_image')
        s = "/things/%d/images/%d" % (thing, img)
        return self._patch_it(s, data)

    def delete_thing_image(self, thing, img):
        """
        delete an image from a thing
        returns the "ok" object
        """
        logging.debug('delete_thing_image')
        s = "/things/%d/images/%d" % (thing, img)
        return self._delete_it(s, None)

    def get_thing_file(self, thing, file_id):
        """
        get list of files on a thing,
        or with the numeric id, get more detailed info about a specific file
        returns an array of files, or detail about a specific file
        """
        logging.debug('get_thing_file')

        if file_id == None:
            s = "/things/%d/files/" % (thing,)
        else:
            s = "/things/%d/files/%d" % (thing, file_id)

        return self._get_it(s, None)

    def delete_thing_file(self, thing, file_id):
        """
        delete a file from a thing
        returns the "ok" object
        """
        logging.debug('delete_thing_file')
        s = "/things/%d/files/%d" % (thing, file_id)
        return self._delete_it(s, None)

    def get_thing_likes(self, thing):
        """
        get users who liked this thing
        returns array of users
        """
        logging.debug('get_thing_likes')
        s = "/things/%d/likes" % (thing)
        return self._get_it(s, None)

    def get_thing_ancestors(self, thing):
        """
        get ancestors of this thing
        returns array of things
        """
        logging.debug('get_thing_ancestors')
        s = "/things/%d/ancestors" % (thing)
        return self._get_it(s, None)

    def get_thing_derivatives(self, thing):
        """
        get derivatives of this thing
        returns array of things
        """
        logging.debug('get_thing_derivatives')
        s = "/things/%d/derivatives" % (thing)
        return self._get_it(s, None)

    def get_thing_tags(self, thing):
        """
        get tags on this thing
        returns array of tags
        """
        logging.debug('get_thing_tags')
        s = "/things/%d/tags" % (thing)
        return self._get_it(s, None)

    def get_thing_category(self, thing):
        """
        get categories of this thing
        returns array of categories
        """
        logging.debug('get_thing_category')
        s = "/things/%d/categories" % (thing)
        return self._get_it(s, None)

    def update_thing(self, thing, data):
        """
        update an existing thing
        data = {'name': 'new name',
                   'license': 'cc or cc-sa or ... etc.',
                   'category': 'something eg 3D Printer Parts',
                   'description': 'the best thing!',
                   'instructions': 'just print it!',
                   'is_wip': True,
                   'tags': ['one', 'two']}
        returns the updated thing
        """
        logging.debug('update_thing')
        s = "/things/%d/" % (thing)
        return self._patch_it(s, data)

    def create_thing(self, data):
        """
        create a new thing
        data = {'name': 'new name',
                   'license': 'cc or cc-sa or ... etc.',
                   'category': 'something eg 3D Printer Parts',
                   'description': 'the best thing!',
                   'instructions': 'just print it!',
                   'is_wip': True,
                   'tags': ['one', 'two'],
                   'ancestors': [123, 345]}
        returns ???
        """
        logging.debug('create_thing')
        s = "/things/"
        return self._post_it(s, data)

    def delete_thing(self, thing):
        """
        deletes a thing
        returns the "ok" object
        """
        logging.debug('delete_thing')
        s = "/things/%d/" % (thing)
        return self._delete_it(s, None)

    def upload_thing_file(self, thing, data):
        """
        upload a file to a thing
        data = {'filename': 'name of the file to upload'}
        returns the data needed to upload a file via an HTTP POST
          with multipart/form-data encoding
        """
        logging.debug('upload_thing_file')
        s = "/things/%d/files" % (thing)
        return self._post_it(s, data)

    def publish_thing(self, thing):
        """
        publishes a thing
        returns the published thing,
        or an array of errors (status 400)
        """
        logging.debug('publish_thing')
        s = "/things/%d/publish" % (thing)
        return self._post_it(s, None)

    def get_thing_copies(self, thing):
        """
        gets the copies ('makes') of a thing
        returns array of copies
        """
        logging.debug('get_thing_copies')
        s = "/things/%d/copies" % (thing)
        return self._get_it(s, None)

    def upload_thing_copy_image(self, thing, data):
        """
        upload a image for new copy
        data = {'filename': 'name of the file to upload'}
        returns the data needed to upload a file via an HTTP POST
          with multipart/form-data encoding
        """
        logging.debug('upload_thing_copy_image')
        s = "/things/%d/copies" % (thing)
        return self._post_it(s, data)

    def like_thing(self, thing):
        """
        like a thing
        returns the "ok" object
        404 not found if thing doesn't exist
        400 bad request if trying to like their own thing
        """
        logging.debug('like_thing')
        s = "/things/%d/likes" % (thing)
        return self._post_it(s, None)

    def unlike_thing(self, thing):
        """
        unlike a thing
        returns the "ok" object
        404 not found if thing doesn't exist
        400 bad request if trying to like their own thing
        """
        logging.debug('unlike_thing')
        s = "/things/%d/likes" % (thing)
        return self._delete_it(s, None)

    def get_thing_zip(self, thing):
        """
        get the url of zip of thing files
        returns the url
        """
        logging.debug('get_thing_zip')
        s = "/things/%d/packageurl" % (thing)
        return self._get_it(s, None)

    def get_thing_prints(self, thing):
        """
        get list of prints associated with a thing (???)
        returns array of prints
        """
        logging.debug('get_thing_prints')
        s = "/things/%d/printjobs" % (thing)
        return self._get_it(s, None)

    def get_thing_layouts(self, thing, layout_id):
        """
        get layouts by a thing (???)
        returns array of layouts
        """
        logging.debug('get_thing_layouts')
        s = "/things/%d/layouts/%d" % (thing, layout_id)
        return self._get_it(s, None)

    # Files

    def get_file_info(self, file_id):
        """
        get info about file
        returns object with urls of the file
        """
        logging.debug('get_file_info')
        s = "/files/%d/" % (file_id)
        return self._get_it(s, None)

    def finalize_file(self, file_id):
        """
        finalize an uploaded file
        returns summary of objectfile or image,
        or returns an error
        """
        logging.debug('finalize_file')
        s = "/files/%d/finalize" % (file_id)
        return self._post_it(s)

    # Copies

    def get_copy(self, copy_id):
        """
        get a copy
        if no copy id specified, will return latest copies
        returns object with the copy, or an array of copy objects 
        """
        logging.debug('get_copy')
        s = "/copies/%d/" % (copy_id)
        return self._get_it(s, None)

    def get_copy_images(self, copy_id):
        """
        get images for a copy
        returns an array of images associated with the copy
        """
        logging.debug('get_copy_images')
        s = "/copies/%d/images" % (copy_id)
        return self._get_it(s, None)

    def upload_copy_image(self, copy_id, data):
        """
        upload an image to a copy
        data = {'filename': 'name of the file you want to upload'}
        returns the data needed to upload a file via an HTTP POST
          with multipart/form-data encoding
        """
        logging.debug('upload_copy_image')
        s = "/copies/%d/images" % (copy_id)
        return self._post_it(s, data)

    def update_copy_image(self, copy_id, image_id, data):
        """
        updates an existing image on a copy
        data = {'rank': 1,
                   'featured': True}
        returns the "ok" object
        """
        logging.debug('update_copy_image')
        s = "/copies/%d/images/%d" % (copy_id, image_id)
        return self._patch_it(s, data)

    def delete_copy_image(self, copy_id, image_id):
        """
        delete an image from a copy
        returns the "ok" object
        """
        logging.debug('delete_copy_image')
        s = "/copies/%d/images/%d" % (copy_id, image_id)
        return self._delete_it(s, None)

    def update_copy(self, copy_id, data):
        """
        update an existing copy
        data = {'description': 'the new description'}
        returns the updated thing
        """
        logging.debug('update_copy')
        s = "/copies/%d/" % (copy_id)
        return self._patch_it(s, data)

    def delete_copy(self, copy_id):
        """
        deletes a copy
        returns NONE
        """
        logging.debug('delete_copy')
        s = "/copies/%d/" % (copy_id)
        return self._delete_it(s, None)

    def like_copy(self, copy_id):
        """
        like a copy
        returns the "ok" object
        or 404 if copy doesn't exist
        or 400 if user is trying to like their own copy
        """
        logging.debug('like_copy')
        s = "/copies/%d/likes" % (copy_id)
        return self._post_it(s, None)

    def unlike_copy(self, copy_id):
        """
        unlike a copy
        returns the "ok" object
        or 404 if copy doesn't exist
        or 400 if user is trying to like their own copy
        """
        logging.debug('unlike_copy')
        s = "/copies/%d/likes" % (copy_id)
        return self._delete_it(s, None)

    # Collections

    def get_collection(self, collection_id):
        """
        get a collection
        if no id is given, gets the latest collections
        returns a single collection, or an array of them
        """
        logging.debug('get_collection')
        s = "/collections/%d/" % (collection_id)
        return self._get_it(s, None)

    def get_things_collection(self, collection_id):
        """
        get the things in a collection
        returns an array of things
        """
        logging.debug('get_things_collection')
        s = "/collections/%d/things" % (collection_id)
        return self._get_it(s, None)

    def create_collection(self, data):
        """
        create a new collection
        data = {'name': 'name of your collection',
                   'description': 'your description'}
        returns ???
        """
        logging.debug('create_collection')
        s = "/collections/"
        return self._post_it(s, data)

    def add_thing_collection(self, collection_id, thing_id, data):
        """
        add a thing to a collection
        data = {'description': 'reason for adding'}
        returns the "ok" object
        """
        logging.debug('add_thing_collection')
        s = "/collections/%d/thing/%d" % (collection_id, thing_id)
        return self._post_it(s, data)

    def remove_thing_collection(self, collection_id, thing_id):
        """
        remove a thing from the collection
        returns the "ok" object
        """
        logging.debug('remove_thing_collection')
        s = "/collections/%d/thing/%d" % (collection_id, thing_id)
        return self._delete_it(s, None)

    def update_collection(self, collection_id, data):
        """
        update a collection
        data = {'name': 'name of collection',
                   'description': 'description of collection'}
        returns the newly created collection
        * apps can only update collections they've created
        """
        logging.debug('update_collection')
        s = "/collections/%d/" % (collection_id)
        return self._patch_it(s, data)

    def delete_collection(self, collection_id):
        """
        delete a collection
        returns NONE
        * apps can only delete collections they've created
        """
        logging.debug('delete_collection')
        s = "/collections/%d/" % (collection_id)
        return self._delete_it(s, None)

    # Newest

    def get_newest_things(self):
        """
        get the latest things published
        """
        logging.debug('get_newest_things')
        s = "/newest/"
        return self._get_it(s, None)

    # Popular

    def get_popular_things(self):
        """
        get the latest popular things
        """
        logging.debug('get_popular_things')
        s = "/popular/"
        return self._get_it(s, None)

    # Featured

    def get_featured_things(self):
        """
        get the latest featured things
        """
        logging.debug('get_featured_things')
        s = "/featured/"
        return self._get_it(s, None)

    # Search

    def keyword_search(self, term):
        """
        get a search by keyword
        returns array of things matching the search
        or 404 if no things match the search
        """
        logging.debug('keyword_search')
        s = "/search/%s/" % (term)
        return self._get_it(s, None)

    # Categories

    def get_categories(self, category_slug):
        """
        gets details about one category,
        or a list of all categories
        returns category object, or an array of categories
        """
        logging.debug('get_categories')

        if category_slug == None:
            s = "/categories"
        else:
            s = "/categories/%s" % (category_slug)

        return self._get_it(s, None)

    def get_latest_category(self, category_slug):
        """
        get latest things in a category
        returns array of thing objects
        or 404 if category doesn't exist
        """
        logging.debug('get_latest_category')
        s = "/categories/%s/things" % (category_slug)
        return self._get_it(s, None)

    # Tags

    def get_latest_tag(self, tag):
        """
        get latest things with specified tag
        returns array of thing objects
        or 404 not found
        """
        logging.debug('get_latest_tag')
        s = "/tags/%s/things" % (tag)
        return self._get_it(s, None)

    def get_representation_tag(self, tag):
        """
        if no tag is specified, returns a list of all tags
        """
        logging.debug('get_representation_tag')
        s = "/tags/%s/" % (tag)
        return self._get_it(s, None)
