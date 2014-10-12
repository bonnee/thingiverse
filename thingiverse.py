import sys
from rauth import OAuth2Service
import webbrowser
import urllib2
from time import sleep
import json
import requests
import logging



class Thingiverse:

    # appinfo = {'client_id': 'your client id',
    #            'client_secret': 'your client secret',
    #            'redirect_uri': 'your redirect url'}

    def __init__(self, appinfo):
        self.DEBUG = True
        self.EXIT = True

        if self.DEBUG: print 'Thingiverse!'

        self._appinfo = appinfo
        self._service = 0
        self._access_code = ''
        self._session = 0

        self._r2 = 0
        self._retry_request = False
        self._retry_count = 0

        self._parse_result = True
        self._initialize_list = True

        self.things = [ [], [], [], [] ] # thing id, user id, thing name, creator name
        self._new_count = 0

        self.seen_things_count = 0

        self.txt_url_mode = False



    # ##############
    # HTTP Request Helpers
    # ###############

    def _get_it(self, endpoint, data):
        try:
            r = self._session.get(self._service.base_url+endpoint, params=data)
            return r.json()
        except Exception as e:
            print 'error! (get)'
            print e
            if self.EXIT: sys.exit()

    def _post_it(self, endpoint, data):
        try:
            r = self._session.post(self._service.base_url+endpoint, data=data)
            return r.json()
        except Exception as e:
            print 'error! (post)'
            print e
            if self.EXIT: sys.exit()

    def _delete_it(self, endpoint, data):
        try:
            r = self._session.delete(self._service.base_url+endpoint, data=data)
            return r.json()
        except Exception as e:
            print 'error! (delete)'
            print e
            if self.EXIT: sys.exit()        

    def _patch_it(self, endpoint, data):

        # headers = {'Authorization: Bearer': self._access_code,
        #             'Host': 'api.thingiverse.com',
        #             'Content-Type': 'application/json'}

        try:
            r = self._session.patch(self._service.base_url+endpoint, data=json.dumps(data))
            return r.json()
        except Exception as e:
            print 'error! (patch)'
            print e
            if self.EXIT: sys.exit()    




    # ##############
    # Authentication Related
    # ###############

    def _fetch_access_code(self):
        if self.DEBUG: print 'fetch_access_code'

        sleep(1.0)

        for line in urllib2.urlopen(''):
            print line
            self._access_code = line

        if(self._access_code == ''):
            self._fetch_access_code()

        #self._access_code = raw_input("access token: >")



    def _get_access_code(self):
        if self.DEBUG: print 'get_access_code'

        # self._service = OAuth2Service(
        #     name='thingiverse',
        #     client_id='719ce807b9ceac053033',
        #     client_secret='45d1bb0958c45b7716e671ebe5723ace',
        #     access_token_url='https://www.thingiverse.com/login/oauth/access_token',
        #     authorize_url='https://www.thingiverse.com/login/oauth/authorize',
        #     base_url='https://api.thingiverse.com')

        #perplexedphoenix
        self._service = OAuth2Service(
            name='thingiverse',
            client_id=self._appinfo['client_id'],
            client_secret=self._appinfo['client_secret'],
            access_token_url='https://www.thingiverse.com/login/oauth/access_token',
            authorize_url='https://www.thingiverse.com/login/oauth/authorize',
            base_url='https://api.thingiverse.com')

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

        print '\n\n'+url+'\n\n';

        if self.txt_url_mode == False:
            webbrowser.open_new(url)
            
        else:
            f = open('url.txt', 'w')
            f.write(url)
            f.close()
            sleep(30.0)

        self._fetch_access_code()
    



    def _get_access_token(self):
        if self.DEBUG: print 'get_access_token'
        # now we can ask for an access token
        # it's given to us after we retrieve it from the above url

        data = {'client_id': self._service.client_id,
                'client_secret': self._service.client_secret,
                'code': self._access_code}

        print(data)

        try:
            self._session = self._service.get_auth_session(data=data)
        except KeyError as e:
            print e
            print 'key error, going to try to get it again'
            self._fetch_access_code()
            self._get_access_token()


    def connect(self):
        self._get_access_code()
        self._get_access_token()



    # ##############
    # Misc
    # ###############


    def send_request(self):
        if self.DEBUG: print 'send_request'

        try:
            #print('hi1')
            self._r2 = self._session.get(self._service.base_url+'/newest/', params={'format': 'json'})
            #print r2.json()

            if self._retry_request == True:
                print 'saved ourselves from the error!'

            self._retry_count = 0
            self._retry_request = False
            self._parse_result = True

        except requests.exceptions.ConnectionError as e:
            print e
            print 'connection error %d: %s' % (self._r2.status_code, self._r2.reason)
            if self._retry_count == 0:
                self._retry_request = True
                self._retry_count += 1
            elif self._retry_count == 1:
                self._retry_request = False
                sys.exit('connection error after a retry')
        
        except requests.exceptions.HTTPError as e:
            print e
            print 'http error %d: %s' % (self._r2.status_code, self._r2.reason)
            if self._retry_count == 0:
                self._retry_request = True
                self._retry_count += 1
            elif self._retry_count == 1:
                self._retry_request = False
                sys.exit('connection error after a retry')
        
        except requests.exceptions.URLRequired as e:
            print e
            print 'url required error %d: %s' % (self._r2.status_code, self._r2.reason)
            sys.exit()

        except requests.exceptions.TooManyRedirects as e:
            print e
            print 'too many redirects error %d: %s' % (self._r2.status_code, self._r2.reason)
            sys.exit()

        except requests.exceptions.RequestException as e:
            print e
            print 'some other error %d: %s' % (self._r2.status_code, self._r2.reason)
            sys.exit()

        except AttributeError as e:
            print 'AAARRRGGGHHH'
            print e
            self._fetch_access_code()
            #print e
            #print 'attribute error %d: %s' % (r2.status_code, r2.reason)
            #sys.exit()



    def _check_request(self):
        if self.DEBUG: print 'check_request'

        if self._retry_request == True:
            self.send_request()




    def _go_initialize_list(self):
        if self.DEBUG: print '_go_initialize_list'

        thing_id = ''
        user_id = ''
        thing_name = ''
        user_name = ''

        #print 'initialize_list'
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

        #print things

        self._initialize_list = False



    def _find_new(self):
        if self.DEBUG: print '_find_new'

        thing_id = ''
        user_id = ''
        thing_name = ''
        user_name = ''

        #print 'new count: %d' % (new_count)

        try:
            new = self._r2.json()[self._new_count]
        except ValueError as e:
            print e
            print 'well aw crap'
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

        #print 'new: %s vs old: %s' % (thing_id, things[0][new_count])

        if self._new_count > len(self.things[0])-1:
            print 'bizarre- new_count (%d) is > len(things[0]) (%d)' % (self._new_count, len(self.things[0])-1)
            #let's try to reset it?
            self._new_count=0
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

            self._new_count+=1
            self._find_new()




    def refresh_new(self):
        if self.DEBUG: print 'refresh_new'

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
                #print '.'
                twiddleloo = 1
            else:
                for i in range(0, self._new_count):
                    #print "this is new: %s" % (things[0][i])
                    print "%d: new thing: %s (%s) by %s" % (self.seen_things_count, self.things[2][i], self.things[0][i], self.things[3][i])
                    self.seen_things_count+=1
                self._new_count = 0

            #print('.')
            #sleep(2.0)




    # ##############
    # Users
    # ###############

    # get a user's profile
    # returns the user
    def get_profile(self, user):
        if self.DEBUG: print 'get_profile'
        s = "/users/%s"
        return self._get_it(s, None)


    # update a user's profile
    # data = {'first_name': 'the first name',
    #        'last_name': 'the last name',
    #        'bio': 'the amazing biography',
    #        'location': 'your location',
    #        'default_license': 'cc or cc-sa, etc'}
    # (all of the data parameters are optional)
    # returns the updated user
    def update_profile(self, user, data):
        if self.DEBUG: print 'update_profile'
        s = "/users/%s" % (user)
        return self._patch_it(s, data)


    # get list of user's own things
    # returns thing objects
    # 404 not found if user doesn't exist
    def get_things_user(self, user):
        if self.DEBUG: print 'get_things_user'
        s = "/users/%s/things" % (user)
        return self._get_it(s, None)


    # get things liked by a user
    # returns thing objects
    # 404 not found if user doesn't exist
    def get_likes_user(self, user):
        if self.DEBUG: print 'get_likes_user'
        s = "/users/%s/likes" % (user)
        return self._get_it(s, None)


    # get latest copies ('makes') by a user
    # returns copy objects
    # 404 not found if user doesn't exist
    def get_copies_user(self, user):
        if self.DEBUG: print 'get_copies_user'
        s = "/users/%s/copies" % (user)
        return self._get_it(s, None)


    # get latest collections by a user
    # returns collection objects
    # 404 not found if user doesn't exist
    def get_collections_user(self, user):
        if self.DEBUG: print 'get_collections_user'
        s = "/users/%s/collections" % (user)
        return self._get_it(s, None)


    # get latest downloads by a user
    # returns thing objects
    # 404 not found if user doesn't exist
    def get_downloads_user(self, user):
        if self.DEBUG: print 'get_downloads_user'
        s = "/users/%s/downloads" % (user)
        return self._get_it(s, None)


    # add a push notification device
    # data = {'type': 'apn',
    #            'id': 'apple device UUID'}
    # returns the "ok" object
    def add_apn(self, user, data):
        if self.DEBUG: print 'add_apn'
        s = "/users/%s/notifier" % (user)
        return self._post_it(s, data)


    # mystery?
    # returns none
    def get_tokens_user(self, user):
        if self.DEBUG: print 'get_tokens_user'
        s = "/users/%s/downloads" % (user)
        return self._get_it(s, None)


    # remove a push notification device
    # data = {'type': 'apn',
    #            'id': 'apple device UUID'}
    # returns the "ok" object
    def remove_apn(self, user, data):
        if self.DEBUG: print 'remove_apn'
        s = "/users/%s/notifier" % (s)
        return self._delete_it(s, data)


    # follow a user
    # returns the "ok" object
    # 404 not found if user doesn't exist
    # 400 bad request if user tries to follow themselves
    def follow_user(self, user):
        if self.DEBUG: print 'follow_user'
        s = "/users/%s/followers" % (s)
        return self._post_it(s, None)


    # unfollow a user
    # returns the "ok" object
    # 404 not found if user doesn't exist
    def unfollow_user(self, user):
        if self.DEBUG: print 'unfollow_user'
        s = "/users/%s/followers" % (user)
        return self._delete_it(s, None)


    # update user's avatar image
    # data = {'filename': 'photo.png'}
    # returns the data needed to upload a file via an HTTP POST,
    # with multipart/form-data encoding
    def update_avatar(self, user, data):
        if self.DEBUG: print 'update_avatar'
        s = "/users/%s/avatarimage" % (user)
        return self._post_it(s, data)


    # update user's cover image
    # data = {'filename': 'photo.png'}
    # returns the data needed to upload a file via an HTTP POST,
    # with multipart/form-data encoding
    def update_cover(self, user, data):
        if self.DEBUG: print 'update_cover'
        s = "/users/%s/coverimage" % (user)
        return self._post_it(s, data)


    # ##############
    # Things
    # ###############


    # gets a thing by its id
    # returns a thing object
    # 401 unauthourized if unpublished thing
    # 403 forbidden if unpublished thing you do not own
    # 404 not found if invalid or deleted thing
    def get_thing(self, thing):
        if self.DEBUG: print 'get_thing'
        s = "/things/%d/" % (thing)
        return self._get_it(s, None)


    # get summary info for all the images of a thing,
    # or more detailed info about a specific image
    # returns an array of imagess or detailed info
    def get_thing_image(self, thing, img):
        if self.DEBUG: print 'get_thing_image'
        s = "/things/%d/images/%d" % (thing, img)
        return self._get_it(s, None)


    # update an existing image on a thing
    # data = {'rank': 1,
    #            'featured': True}
    # returns the "ok" object
    def update_thing_image(self, thing, img, data):
        if self.DEBUG: print 'update_thing_image'
        s = "/things/%d/images/%d" % (thing, img)
        return self._patch_it(s, data)


    # delete an image from a thing
    # returns the "ok" object
    def delete_thing_image(self, thing, img):
        if self.DEBUG: print 'delete_thing_image'
        s = "/things/%d/images/%d" % (thing, img)
        return self._delete_it(s, None)


    # get list of files on a thing,
    # or with the numeric id, get more detailed info about a specific file
    # returns an array of files, or detail about a specific file
    def get_thing_file(self, thing, file_id):
        if self.DEBUG: print 'get_thing_file'

        if file_id == None:
            s = "/things/%d/files/" % (thing,)
        else:
            s = "/things/%d/files/%d" % (thing, file_id)

        return self._get_it(s, None)


    # delete a file from a thing
    # returns the "ok" object
    def delete_thing_file(self, thing, file_id):
        if self.DEBUG: print 'delete_thing_file'
        s = "/things/%d/files/%d" % (thing, file_id)
        return self._delete_it(s, None)


    # get users who liked this thing
    # returns array of users
    def get_thing_likes(self, thing):
        if self.DEBUG: print 'get_thing_likes'
        s = "/things/%d/likes" % (thing)
        return self._get_it(s, None)


    # get ancestors of this thing
    # returns array of things
    def get_thing_ancestors(self, thing):
        if self.DEBUG: print 'get_thing_ancestors'
        s = "/things/%d/ancestors" % (thing)
        return self._get_it(s, None)


    # get derivatives of this thing
    # returns array of things
    def get_thing_derivatives(self, thing):
        if self.DEBUG: print 'get_thing_derivatives'
        s = "/things/%d/derivatives" % (thing)
        return self._get_it(s, None)


    # get tags on this thing
    # returns array of tags
    def get_thing_tags(self, thing):
        if self.DEBUG: print 'get_thing_tags'
        s = "/things/%d/tags" % (thing)
        return self._get_it(s, None)


    # get categories of this thing
    # returns array of categories
    def get_thing_category(self, thing):
        if self.DEBUG: print 'get_thing_category'
        s = "/things/%d/categories" % (thing)
        return self._get_it(s, None)


    # update an existing thing
    # data = {'name': 'new name',
    #            'license': 'cc or cc-sa or ... etc.',
    #            'category': 'something eg 3D Printer Parts',
    #            'description': 'the best thing!',
    #            'instructions': 'just print it!',
    #            'is_wip': True,
    #            'tags': ['one', 'two']}
    # returns the updated thing
    def update_thing(self, thing, data):
        if self.DEBUG: print 'update_thing'
        s = "/things/%d/" % (thing)
        return self._patch_it(s, data)


    # create a new thing
    # data = {'name': 'new name',
    #            'license': 'cc or cc-sa or ... etc.',
    #            'category': 'something eg 3D Printer Parts',
    #            'description': 'the best thing!',
    #            'instructions': 'just print it!',
    #            'is_wip': True,
    #            'tags': ['one', 'two'],
    #            'ancestors': [123, 345]}
    # returns ???
    def create_thing(self, data):
        if self.DEBUG: print 'create_thing'
        s = "/things/"
        return self._post_it(s, data)


    # deletes a thing
    # returns the "ok" object
    def delete_thing(self, thing):
        if self.DEBUG: print 'delete_thing'
        s = "/things/%d/" % (thing)
        return self._delete_it(s, None)


    # upload a file to a thing
    # data = {'filename': 'name of the file to upload'}
    # returns the data needed to upload a file via an HTTP POST
    #   with multipart/form-data encoding
    def upload_thing_file(self, thing, data):
        if self.DEBUG: print 'upload_thing_file'
        s = "/things/%d/files" % (thing)
        return self._post_it(s, data)


    # publishes a thing
    # returns the published thing,
    # or an array of errors (status 400)
    def publish_thing(self, thing):
        if self.DEBUG: print 'publish_thing'
        s = "/things/%d/publish" % (thing)
        return self._post_it(s, None)


    # gets the copies ('makes') of a thing
    # returns array of copies
    def get_thing_copies(self, thing):
        if self.DEBUG: print 'get_thing_copies'
        s = "/things/%d/copies" % (thing)
        return self._get_it(s, None)


    # upload a image for new copy
    # data = {'filename': 'name of the file to upload'}
    # returns the data needed to upload a file via an HTTP POST
    #   with multipart/form-data encoding
    def upload_thing_copy_image(self, thing, data):
        if self.DEBUG: print 'upload_thing_copy_image'
        s = "/things/%d/copies" % (thing)
        return self._post_it(s, data)


    # like a thing
    # returns the "ok" object
    # 404 not found if thing doesn't exist
    # 400 bad request if trying to like their own thing
    def like_thing(self, thing):
        if self.DEBUG: print 'like_thing'
        s = "/things/%d/likes" % (thing)
        return self._post_it(s, None)

    # unlike a thing
    # returns the "ok" object
    # 404 not found if thing doesn't exist
    # 400 bad request if trying to like their own thing
    def unlike_thing(self, thing):
        if self.DEBUG: print 'unlike_thing'
        s = "/things/%d/likes" % (thing)
        return self._delete_it(s, None)


    # get the url of zip of thing files
    # returns the url
    def get_thing_zip(self, thing):
        if self.DEBUG: print 'get_thing_zip'
        s = "/things/%d/packageurl" % (thing)
        return self._get_it(s, None)


    # get list of prints associated with a thing (???)
    # returns array of prints
    def get_thing_prints(self, thing):
        if self.DEBUG: print 'get_thing_prints'
        s = "/things/%d/printjobs" % (thing)
        return self._get_it(s, None)


    # get layouts by a thing (???)
    # returns array of layouts
    def get_thing_layouts(self, thing, layout_id):
        if self.DEBUG: print 'get_thing_layouts'
        s = "/things/%d/layouts/%d" % (thing, layout_id)
        return self._get_it(s, None)


    # ##############
    # Files
    # ###############

    # get info about file
    # returns object with urls of the file
    def get_file_info(self, file_id):
        if self.DEBUG: print 'get_file_info'
        s = "/files/%d/" % (file_id)
        return self._get_it(s, None)

    # finalize an uploaded file
    # returns summary of objectfile or image,
    # or returns an error
    def finalize_file(self, file_id):
        if self.DEBUG: print 'finalize_file'
        s = "/files/%d/finalize" % (file_id)
        return self._post_it(s)


    # ##############
    # Copies
    # ###############

    # get a copy
    # if no copy id specified, will return latest copies
    # returns object with the copy, or an array of copy objects 
    def get_copy(self, copy_id):
        if self.DEBUG: print 'get_copy'
        s = "/copies/%d/" % (copy_id)
        return self._get_it(s, None)


    # get images for a copy
    # returns an array of images associated with the copy
    def get_copy_images(self, copy_id):
        if self.DEBUG: print 'get_copy_images'
        s = "/copies/%d/images" % (copy_id)
        return self._get_it(s, None)


    # upload an image to a copy
    # data = {'filename': 'name of the file you want to upload'}
    # returns the data needed to upload a file via an HTTP POST
    #   with multipart/form-data encoding
    def upload_copy_image(self, copy_id, data):
        if self.DEBUG: print 'upload_copy_image'
        s = "/copies/%d/images" % (copy_id)
        return self._post_it(s, data)


    # updates an existing image on a copy
    # data = {'rank': 1,
    #            'featured': True}
    # returns the "ok" object
    def update_copy_image(self, copy_id, image_id, data):
        if self.DEBUG: print 'update_copy_image'
        s = "/copies/%d/images/%d" % (copy_id, image_id)
        return self._patch_it(s, data)


    # delete an image from a copy
    # returns the "ok" object
    def delete_copy_image(self, copy_id, image_id):
        if self.DEBUG: print 'delete_copy_image'
        s = "/copies/%d/images/%d" % (copy_id, image_id)
        return self._delete_it(s, None)


    # update an existing copy
    # data = {'description': 'the new description'}
    # returns the updated thing
    def update_copy(self, copy_id, data):
        if self.DEBUG: print 'update_copy'
        s = "/copies/%d/" % (copy_id)
        return self._patch_it(s, data)


    # deletes a copy
    # returns NONE
    def delete_copy(self, copy_id):
        if self.DEBUG: print 'delete_copy'
        s = "/copies/%d/" % (copy_id)
        return self._delete_it(s, None)

    # like a copy
    # returns the "ok" object
    # or 404 if copy doesn't exist
    # or 400 if user is trying to like their own copy
    def like_copy(self, copy_id):
        if self.DEBUG: print 'like_copy'
        s = "/copies/%d/likes" % (copy_id)
        return self._post_it(s, None)


    # unlike a copy
    # returns the "ok" object
    # or 404 if copy doesn't exist
    # or 400 if user is trying to like their own copy
    def unlike_copy(self, copy_id):
        if self.DEBUG: print 'unlike_copy'
        s = "/copies/%d/likes" % (copy_id)
        return self._delete_it(s, None)



    # ##############
    # Collections
    # ###############

    # get a collection
    # if no id is given, gets the latest collections
    # returns a single collection, or an array of them
    def get_collection(self, collection_id):
        if self.DEBUG: print 'get_collection'
        s = "/collections/%d/" % (collection_id)
        return self._get_it(s, None)


    # get the things in a collection
    # returns an array of things
    def get_things_collection(self, collection_id):
        if self.DEBUG: print 'get_things_collection'
        s = "/collections/%d/things" % (collection_id)
        return self._get_it(s, None)


    # create a new collection
    # data = {'name': 'name of your collection',
    #            'description': 'your description'}
    # returns ???
    def create_collection(self, data):
        if self.DEBUG: print 'create_collection'
        s = "/collections/"
        return self._post_it(s, data)


    # add a thing to a collection
    # data = {'description': 'reason for adding'}
    # returns the "ok" object
    def add_thing_collection(self, collection_id, thing_id, data):
        if self.DEBUG: print 'add_thing_collection'
        s = "/collections/%d/thing/%d" % (collection_id, thing_id)
        return self._post_it(s, data)


    # remove a thing from the collection
    # returns the "ok" object
    def remove_thing_collection(self, collection_id, thing_id):
        if self.DEBUG: print 'remove_thing_collection'
        s = "/collections/%d/thing/%d" % (collection_id, thing_id)
        return self._delete_it(s, None)


    # update a collection
    # data = {'name': 'name of collection',
    #            'description': 'description of collection'}
    # returns the newly created collection
    # * apps can only update collections they've created
    def update_collection(self, collection_id, data):
        if self.DEBUG: print 'update_collection'
        s = "/collections/%d/" % (collection_id)
        return self._patch_it(s, data)


    # delete a collection
    # returns NONE
    # * apps can only delete collections they've created
    def delete_collection(self, collection_id):
        if self.DEBUG: print 'delete_collection'
        s = "/collections/%d/" % (collection_id)
        return self._delete_it(s, None)



    # ##############
    # Newest
    # ###############

    # get the latest things published
    def get_newest_things(self):
        if self.DEBUG: print 'get_newest_things'
        s = "/newest/"
        return self._get_it(s, None)



    # ##############
    # Popular
    # ###############

    # get the latest popular things
    def get_popular_things(self):
        if self.DEBUG: print 'get_popular_things'
        s = "/popular/"
        return self._get_it(s, None)



    # ##############
    # Featured
    # ###############

    # get the latest featured things
    def get_featured_things(self):
        if self.DEBUG: print 'get_featured_things'
        s = "/featured/"
        return self._get_it(s, None)



    # ##############
    # Search
    # ###############

    # get a search by keyword
    # returns array of things matching the search
    # or 404 if no things match the search
    def keyword_search(self, term):
        if self.DEBUG: print 'keyword_search'
        s = "/search/%s/" % (term)
        return self._get_it(s, None)



    # ##############
    # Categories
    # ###############

    # gets details about one category,
    # or a list of all categories
    # returns category object, or an array of categories
    def get_categories(self, category_slug):
        if self.DEBUG: print 'get_categories'

        if category_slug == None:
            s = "/categories"
        else:
            s = "/categories/%s" % (category_slug)
        
        return self._get_it(s, None)


    # get latest things in a category
    # returns array of thing objects
    # or 404 if category doesn't exist
    def get_latest_category(self, category_slug):
        if self.DEBUG: print 'get_latest_category'
        s = "/categories/%s/things" % (category_slug)
        return self._get_it(s, None)


    # ##############
    # Tags
    # ###############

    # get latest things with specified tag
    # returns array of thing objects
    # or 404 not found
    def get_latest_tag(self, tag):
        if self.DEBUG: print 'get_latest_tag'
        s = "/tags/%s/things" % (tag)
        return self._get_it(s, None)


    # if no tag is specified, returns a list of all tags
    def get_representation_tag(self, tag):
        if self.DEBUG: print 'get_representation_tag'
        s = "/tags/%s/" % (tag)
        return self._get_it(s, None)
