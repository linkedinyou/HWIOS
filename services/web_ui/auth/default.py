# -*- coding: utf-8 -*-
"""
    services.web_ui.auth.default
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Overriding of the default Django authentication model allowing us to customize things

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import os
import uuid, time, datetime, random
import hashlib
import smtplib

from django.db import models 
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.http import HttpResponseServerError
from django.core import mail
from django.template import Context, Template
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

import web_ui.settings as settings
from web_ui.models.settings import Settings
try:
    from core.application import HWIOS
except ImportError:
    print "POEP"
from web_ui.models.signal import Signal


class XAuth(ModelBackend):
    """
    Overriding ModelBackend so the authenticate function can be overriden as well.
    """

    @property
    def user_class(self):
        """Set the userclass

        :return: Profile - Return the profile class
        """
        if not hasattr(self, '_user_class'):
            self._user_class = get_model('no_fixture','profile')
            if not self._user_class:
                raise ImproperlyConfigured('Could not get custom user model')
        return self._user_class
        
        
    def authenticate(self, username=None, password=None, options = False):
        """Authenticated a user login request to django

        :param str username: The username that is trying to login (first_name and last_name)
        :param str password: The raw password that's used to login with
        :param dict options: Optional; Add some options to the login
        :return: Profile or None - Returns the profile when succesful, otherwise None
        """
        
        #'regular' sha1 django authentication
        #result = super(XAuth, self).authenticate(username='%s %s' % (username[0],username[1]), password=password)
        #if isinstance(result, User):
        #    return result.profile
        #else:
        #    return None
        #'opensim-compatible' authentication. Won't hurt to use it without opensim
        try:
            profile = self.user_class.objects.get(username=username)
            pwhash = hashlib.md5('%s:%s' % (hashlib.md5(password).hexdigest(),profile.salt)).hexdigest()
            if pwhash == profile.password:
                return profile
            else:
                return None
        except ObjectDoesNotExist:
            return None


class XAuthManager(models.Manager):
    """Profile manager object override, to handle things like creating new profiles and sending activation mails"""
    
    try:
        acp_settings = Settings.objects.all()
        if len(acp_settings) > 0: acp_settings = acp_settings[0]
    except DatabaseError:
        pass

    
    def __init__(self,*args,**kwargs):
        super(XAuthManager, self).__init__(*args,**kwargs)
        
    
    def create_profile(self, profile_data, acp = False, client = None):
        """Creates a new profile from data and optionally sends a signal within HWIOS for optional listeners

        :param dict profile_data: A collection of keys and values necessary to register a new account
        :param bool acp: Acp means that the account is registered from the backend, which takes a different path for registering (like no activation mail)
        :param Client client: If client is not None, send out a signal for optional further processing. Doesn't need client anyway probably.
        :return: Profile - Returns the new profile
        """
        write_profile = True
        self.acp_settings = Settings.objects.all()[0]
        required_keys = ['username','email','password','ip']
        if acp:
            required_keys.extend(['is_staff','is_active'])
        missing_keys = []
        proceed = True
        for key in required_keys:
            if not profile_data.has_key(key):
                missing_keys.append(key)
                proceed = False
        if not proceed: return missing_keys
        #valid parameters, proceeed...
        else:
            try:                
                profile = self.model.objects.get(username=profile_data['username'])
                write_profile = False
            #doesnt exist. create a hwios profile
            except ObjectDoesNotExist: 
                profile = self.model(**profile_data)
                profile.username = profile_data['username']
                profile.email = profile_data['email']
                profile.uuid = uuid.uuid4()
                profile.date_joined = datetime.datetime.now()
                profile.set_password(profile_data['password'])
                profile.raw_password = profile_data['password']
                profile.ip = profile_data['ip']
                #passed to the registration template later on                
                #used in the activation body
                #profile.raw_password = profile_data['first_name']
                #0: direct activation, 1: activation by user, 2:activation by moderator
                if (self.acp_settings.activation_type == 1 or self.acp_settings.activation_type == 2) and not acp:
                    profile.is_active = 0
                    self.activate_link = 'http://%s:%s/profiles/activate/%s/' % (settings.HWIOS_URI, settings.HWIOS_PORT, profile.uuid)
                    self._send_activation_mail(profile, acp)
                elif not acp:
                    profile.is_active = 1
                    self._send_activation_mail(profile, acp)
            if acp:
                profile.is_active = profile_data['is_active']
                profile.is_staff = profile_data['is_staff']
                profile.is_superuser = profile_data['is_superuser']
            if write_profile == True:
                profile.save()
                if client != None:
                    HWIOS.ws_realm.pool.signals.send('profile_created', client = client.transport, filters = None, profile = profile)
        return profile
        
    
    def delete_profile(self,profile_uuid, client = None):
        try: 
            profile = self.model.objects.get(uuid = profile_uuid)
            deleted = profile.username
            profile.delete()
            if client != None:
                HWIOS.ws_realm.pool.signals.send('profile_deleted', client = client.transport, filters = None, profile_uuid = profile_uuid)
        except ObjectDoesNotExist:
            return False
        return {'name':deleted,'status':"Succesfully deleted"}
        
    
    #limiting this to username,firstname,lastname,password
    def update_profile(self, profile_uuid, profile_data, client = None):
        """Updates a profile from data and optionally sends a signal within HWIOS for optional listeners

        :param str profile_uuid: The uuid of the profile to update
        :param dict profile_data: A collection of keys and values necessary to update the profile
        :param Client client: If client is not None, send out a signal for optional further processing. Doesn't need client anyway probably.
        :return: Profile - Returns the updated profile
        """
        profile = self.model.objects.get(uuid = profile_uuid)
        for key in profile_data:
            if key == 'password':               
                if profile_data[key] != '':
                    profile.set_password(profile_data['password'])
                    #we signal authentication listeners with raw password included, so they may change their pw-data as well
                    profile.raw_password = profile_data['password']
            elif key == 'avatar':
                import PIL
                import Image,ImageDraw,ImageFont,ImageChops
                from StringIO import StringIO
                import base64
                udata = profile_data['avatar'].split(',')[1].encode('utf-8')
                imagedata = base64.b64decode(udata)
                im = Image.open(StringIO(imagedata))
                resized_image = im.resize((120,120))
                #remove old avatar image
                _avatar_fp = os.path.join(settings.HWIOS_ROOT,'services','web_ui','media','files','avatars')
                old_avatar_file = os.path.join(_avatar_fp, profile.photo)
                try:
                    os.remove(old_avatar_file)
                except OSError:
                    pass
                new_avatar_file = '%s_%s.png' % (profile.uuid, int(time.time()))
                profile.photo = new_avatar_file
                _file = open(os.path.join(_avatar_fp, new_avatar_file),'w')
                resized_image.save(_file,'png')
                _file.close()
                os.chmod(os.path.join(_avatar_fp, new_avatar_file), 0755)
            else: setattr(profile,key,profile_data[key])
        profile.save()
        profile.is_authenticated = True
        if client != None:
            #update the ws-session's profile, if change is required
            if client.profile.uuid == profile.uuid:
                client.profile = profile
            HWIOS.ws_realm.pool.signals.send('profile_changed', client = client.transport, filters = None, profile = profile)
        return profile
        
        
    def _send_activation_mail(self, profile, acp):
        """Sends an activation mail to a registered profile

        :param Profile profile: The profile to send the activation mail to        
        :param bool acp: With acp, the moderator doesn't get an activation mail notification 
        :return: bool - Returns True on success, False otherwise
        """
        subject, from_email = self.acp_settings.mail_header, self.acp_settings.mail_from
        mail_tpl = Template(self.acp_settings.mail_body)
        c = Context({'profile': profile, 'activation_type': self.acp_settings.activation_type, 'activatelink': self.activate_link})
        user_email_msg = mail_tpl.render(c)
        try:
            connection = mail.get_connection(fail_silently=True)
        except smtplib.SMTPException:
            feedback = 'Your account was made, but an email delivery failure occured. Please contact the administrator!'
            dialog = render_to_string('profiles/registration_complete.html', {'profile': profile, 'activation_type': self.acp_settings.activation_type})
            return False
        user_email = mail.EmailMessage(subject, user_email_msg, from_email, [profile.email], connection=connection)
        user_email.content_subtype = "html"
        user_email.send()
        #send a mail to moderator if moderator activation is required, or moderator notify is enabled. Ignore in case the profile was made from acp
        if self.acp_settings.activation_type == 2 or self.acp_settings.registration_moderator_notify == 1 and not acp:
            mod_email_msg = render_to_string('profiles/registration_moderator_notify.html', {'profile': profile, 'activation_type': self.acp_settings.activation_type,'activatelink':self.activate_link, 'ip':profile.ip})
            moderators = self.model.objects.filter(is_staff=1)
            email_list = []
            for moderator in moderators:
                email_list.append(moderator.email)
            mod_email = mail.EmailMessage('New account registered at %s' % (self.acp_settings.site_name), mod_email_msg, from_email, email_list, connection=connection)
            mod_email.content_subtype = "html"
            mod_email.send()
        return True    
        
        
    def activate_profile(self,uuid):
        """Enables the profile by setting the is_active property of the profile

        :param str uuid: The uuid of the profile to activate
        :return: Profile or None - Returns the modified profile or None
    
        """
        profile = self.model.objects.get(uuid = uuid)
        if profile.is_active == 0:
            profile.is_active = 1
            profile.save()
            return profile
        else:
            return False     
