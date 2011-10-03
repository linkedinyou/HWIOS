# -*- coding: utf-8 -*-
"""
    services.web_ui.models.activity
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Activity tracking model class and logic

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""
import uuid

from django.db.models import CharField, DateTimeField, ForeignKey, Model, TextField, IntegerField
from django.contrib.auth.models import Group
from django.template.loader import render_to_string

from web_ui.models.profiles import Profile
from hwios.core.application import HWIOS

#0:ignore, 1:view, 2:participate, 3:respond, 4:act
ACTIVITY_CSS = ['ui-icon-dummy','ui-icon-search','ui-icon-person','ui-icon-comment','ui-icon-alert']

VISIBILITY_TYPES = {
    'all':0,
    'users':1,
    'moderators':2,
    #will be added later
    'friends':3,
    'group':4
}

ACTIVITY_ACTIONS = {
    'ignore':0,
    'view':1,
    'respond':2,
    'participate':3,
    'act':4,
}


class Activity(Model):
    """
    ORM Model for the activity functionality
    """
    connection_name="default" 

    uuid = CharField(max_length=36,  primary_key=True, default=lambda:str(uuid.uuid4()))
    message = CharField(max_length=36)
    link = CharField(max_length=128)
    actor_user = ForeignKey(Profile, blank=True, null=True)
    actor_group = ForeignKey(Group, blank=True, null=True)
    #0: all, 1:users, 2:moderators, 3:friends,4:group
    #0:ignore, 1:view, 2:participate, 3:respond, 4:act
    action_all = IntegerField()
    action_users = IntegerField()
    action_moderators = IntegerField()
    action_friends = IntegerField()
    action_group = IntegerField()    
    pub_date = DateTimeField(auto_now_add=True)    

    class Meta:
        verbose_name_plural = "Activities"
        app_label = 'no_fixture'
        db_table = 'hwios_activities'
        ordering = ['-pub_date']


def publish_activity(actor, message, link, target):
    '''Sends activity notifications to a collection of clients. Target looks like a 5-element list:
    [0,0,0,0,0]. Each item is a client-collection:
    **0: all,1: logged_in,2: moderators,3: friends,4: group**
    Each item can have a different value, describing the type of action suggested:
    **0: ignore, 1: view, 2: participate, 3: respond, 4: act**
    
    :param actor: Profile, Group or None
    :param str message: The message to publish
    :param str link: The link to add to the message
    :param list target: Describes which target-clients to publish to. 
    '''
    activity = Activity()
    activity.message = message
    activity.link = link
    response = {'data':{}}
    if isinstance(actor, Profile):
        activity.actor_user = actor
        response['data']['actor'] = actor.username
    elif isinstance(actor, Group):
        activity.actor_group = actor
    elif actor == None:
        pass
    else:
        return False
    activity.action_all = target[0]
    activity.action_users = target[1]
    activity.action_moderators = target[2]
    activity.action_friends = target[3]
    activity.action_group = target[4]
    activity.save()
    #print activity.pub_date
    #pub_date = activity.pub_date.strftime("%a %d %B, %H:%M")    
    for _client in HWIOS.ws_realm.pool.get_clients():
        #type 2 - moderators/staff
        if _client.profile.is_staff:
            if target[2] != 0:
                activity.action_css = ACTIVITY_CSS[activity.action_moderators]
                tpl_activity = render_to_string("activity/activity.html", {"activity":activity,'profile':_client.profile})                
                response['data']['dom'] = {'activity':tpl_activity}
                _client.remote('/data/activity/create/', response)
        #type 1 - users
        elif _client.profile.is_authenticated:
            if target[1] != 0:
                activity.action_css = ACTIVITY_CSS[activity.action_users]
                tpl_activity = render_to_string("activity/activity.html", {"activity":activity,'profile':_client.profile})                
                response['data']['dom'] = {'activity':tpl_activity}
                _client.remote('/data/activity/create/', response)
        #type 0 - all
        else:
            if target[0] != 0:
                activity.action_css = ACTIVITY_CSS[activity.action_all]
                tpl_activity = render_to_string("activity/activity.html", {"activity":activity,'profile':_client.profile})
                response['data']['dom'] = {'activity':tpl_activity}
                _client.remote('/data/activity/create/', response)


