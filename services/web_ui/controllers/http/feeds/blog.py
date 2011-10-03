# -*- coding: utf-8 -*-
"""
    services.web_ui,controllers.http.feeds.blog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    HTTP RSS feeds for our blogging module

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""


from django.contrib.syndication.views import Feed
from pyparsing import *

from web_ui.models.blog import BlogArticle

class LatestArticlesFeed(Feed):
    title = "Latest HWIOS News"
    link = "/blog/"
    description = "Updates on changes and additions to HWIOS blog"


    def items(self):
        return BlogArticle.objects.order_by('-pub_date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        """
        Strip html content, and return the first 20 characters of the text as description
        """
        removeText = replaceWith("")
        scriptOpen,scriptClose = makeHTMLTags("script")
        scriptBody = scriptOpen + SkipTo(scriptClose) + scriptClose
        anyTag,anyClose = makeHTMLTags(Word(alphas,alphanums+":_"))
        anyTag.setParseAction(removeText)        
        anyClose.setParseAction(removeText)
        htmlComment.setParseAction(removeText)
        targetHTML = item.text
        firstPass = (htmlComment | scriptBody | commonHTMLEntity |
                    anyTag | anyClose ).transformString(targetHTML)
        repeatedNewlines = LineEnd() + OneOrMore(LineEnd())
        repeatedNewlines.setParseAction(replaceWith("\n\n"))
        secondPass = repeatedNewlines.transformString(firstPass)
        return '%s...' % secondPass[0:30]

    def item_pubdate(self, item):
        """
        Returns the pubdate for every item in the feed.
        """
        return item.pub_date

        
    def item_author_name(self, item):
        """
        Returns the author name for every item in the feed.
        """
        return item.author.username

    def item_link(self, item):
        return '/blog/%s/  ' % item.slug