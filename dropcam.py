#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2012-2014, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# - Neither the name of the software nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import time
import logging
import urllib2
import cookielib
import json
from urllib import urlencode
import datetime
from pytz import timezone
import glob

__doc__ = """
Unofficial Dropcam Python API.
"""

__author__ = "Ryan Galloway <ryan@rsgalloway.com>"

logging.basicConfig()
log = logging.getLogger("dropcam")

class ConnectionError(IOError):
    """
    Exception used to indicate issues with connectivity or HTTP
    requests/responses
    """

def _request(path, params, cookie=None):
    """
    Dropcam http request function.
    """
    request_url = "?".join([path, urlencode(params)])
    request = urllib2.Request(request_url)
    if cookie:
        request.add_header('cookie', cookie)
    try:
        return urllib2.urlopen(request)
    except urllib2.HTTPError:
        log.error("Bad URL: %s" % request_url)
        raise

class Dropcam(object):

    NEXUS_BASE = "https://nexusapi.dropcam.com"
    API_BASE = "https://www.dropcam.com"
    API_PATH = "api/v1"

    LOGIN_PATH =  "/".join([API_BASE, API_PATH, "login.login"])
    CAMERAS_GET =  "/".join([API_BASE, API_PATH, "cameras.get"])
    CAMERAS_UPDATE =  "/".join([API_BASE, API_PATH, "cameras.update"])
    CAMERAS_GET_VISIBLE =  "/".join([API_BASE, API_PATH, "cameras.get_visible"])
    CAMERAS_GET_IMAGE_PATH = "/".join([API_BASE, API_PATH, "cameras.get_image"])
    CAMERAS_CREATE_CLIP_PATH = "/".join([API_BASE, API_PATH, "videos.request"])
    CAMERAS_DELETE_CLIP_PATH = "/".join([API_BASE, API_PATH, "videos.delete"])
    CAMERAS_GET_ALL_CLIPS_PATH = "/".join([API_BASE, API_PATH, "videos.get_owned"])
    def __init__(self, username, password):
        """
        Creates a new dropcam API instance.

        :param username: Dropcam account username.
        :param password: Dropcam account password.
        """
        self.__username = username
        self.__password = password
        self.cookie = None
        self._login()

    def _login(self):
        params = dict(username=self.__username, password=self.__password)
        response = _request(self.LOGIN_PATH, params)
        self.cookie = response.headers.get('Set-Cookie')

    def cameras(self):
        """
        :returns: list of Camera class objects
        """
        if not self.cookie:
            self._login()
        cameras = []
        params = dict(group_cameras=True)
        response = _request(self.CAMERAS_GET_VISIBLE, params, self.cookie)
        data = json.load(response)
        items = data.get('items')
        for item in items:
            for params in item.get('owned'):
                cameras.append(Camera(self, params))
        return cameras

class Camera(object):
    def __init__(self, dropcam, params):
        """
        :param params: Dictionary of dropcam camera attributes.
        :returns: addinfourl file-like object
        :raises: urllib2.HTTPError, urllib2.URLError
        """
        self.dropcam = dropcam
        self.__dict__.update(params)
    
    def create_clip(self, width=720, start=None, length=None, title=None):
        """
        Requests a camera video, returns response object.
        
        :param width: image width or X resolution
        :param start: time of image capture (in seconds from epoch)
        :param length: length of image capture (in seconds)
        :param title: title of clip
        :returns: response object
        :raises: ConnectionError
        """
        params = dict(uuid=self.uuid, width=width, start_date=start, length=length, title=title)
        if start:
            params.update()
        response = _request(Dropcam.CAMERAS_CREATE_CLIP_PATH, params, self.dropcam.cookie)

        if (
            response.code != 200
            or not int(response.headers.getheader('content-length', 0))
        ):
            # Either a connection error or empty image sent with code 200
            raise ConnectionError(
                'Camera image is not available or camera is turned off',
            )

        return response

    def save_all_clips(self, path):
        """
        Saves all saved video clips.
        
        :param path: base path to save clips to
        """
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1'
        headers = { 'User-Agent' : user_agent }

        items = self.get_all_clips()
        for item in items:
            link = 'http://%s/%s'%(item.get('server'),item.get('filename'))
            #link = 'http://lauren-mccarthy.com'
            clip_id = item.get('id')
            title = item.get('title')
            # print '%d:%s %s' % (clip_id, title, link)
            print link

            # download clip
            # f = open(path+title+'.mp4', 'wb')
            # req = urllib2.Request(link, None, headers)
            # data = urllib2.urlopen(req)
            # f.write(data.read())
            # f.close()

    def get_all_clips(self):
        """
        Requests a camera video, returns response object.
        
        :param start: time of image capture (in seconds from epoch)
        :param length: length of image capture (in seconds)
        :returns: array of clip items
        :raises: ConnectionError
        """
        params = dict(uuid=self.uuid)
        response = _request(Dropcam.CAMERAS_GET_ALL_CLIPS_PATH, params, self.dropcam.cookie)

        data = json.load(response)
        items = data.get('items')
        return items
    
    def delete_all_clips(self):
        """
        Deletes all saved clips.
        """
        items = self.get_all_clips()
        for item in items:
            clip_id = item.get('id')
            self.delete_clip(clip_id)
    

    def delete_clip(self, id):
        """
        Deletes a camera video, returns response object.
        
        :param id: id of video to delete
        :returns: response object
        :raises: ConnectionError
        """
        params = dict(uuid=self.uuid, id=id)
        response = _request(Dropcam.CAMERAS_DELETE_CLIP_PATH, params, self.dropcam.cookie)

        return response


    def get_image(self, width=720, seconds=None):
        """
        Requests a camera image, returns response object.
        
        :param width: image width or X resolution
        :param seconds: time of image capture (in seconds from epoch)
        :returns: response object
        :raises: ConnectionError
        """
        params = dict(uuid=self.uuid, width=width)
        if seconds:
            params.update(time=seconds)
        response = _request(Dropcam.CAMERAS_GET_IMAGE_PATH, params, self.dropcam.cookie)

        if (
            response.code != 200
            or not int(response.headers.getheader('content-length', 0))
        ):
            # Either a connection error or empty image sent with code 200
            raise ConnectionError(
                'Camera image is not available or camera is turned off',
            )

        return response

    def save_image(self, path, width=720, seconds=None):
        """
        Saves a camera image to disc. 

        :param path: file path to save image
        :param width: image width or X resolution
        :param seconds: time of image capture (in seconds from epoch)
        :raises: ConnectionError
        """
        f = open(path, "wb")
        response = self.get_image(width, seconds)
        f.write(response.read())
        f.close()

if __name__ == "__main__":
    d = Dropcam(os.getenv("DROPCAM_USERNAME"), 
                os.getenv("DROPCAM_PASSWORD"))
    try:
        if len(d.cameras()) > 0:
            cam = d.cameras()[0]
            print "saving images for", cam.title

            for f in glob.glob(os.path.join('watching/', '*.mov')):
                f = f[9:-4]
                ind = f.index('+')
                dur = f[ind+1:]
                dt = f[:ind-1]
                dt = datetime.datetime.strptime(dt, '%Y-%B-%d %H %M %S') #convert string
                dt = dt.replace(tzinfo=timezone('US/Eastern')) # add tz
                print dt

                fname = f.replace(' ', '_')
                #os.mkdir('imgs/%s' % fname)

                epoch = datetime.datetime(1970, 1, 1, tzinfo=timezone('UTC'))
                delta = dt - epoch
                secs = float(delta.total_seconds())
                
                cam.create_clip(720, secs, dur, fname)
                cam.save_all_clips('imgs/')
                #cam.delete_all_clips()

    except Exception, err:
        print err
