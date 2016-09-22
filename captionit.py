#!/usr/bin/env python

# [START imports]
import os
import urllib

from google.appengine.ext import ndb
from google.appengine.api import app_identity
import logging
import os

import jinja2
import webapp2

import uuid
import StringIO

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

class Caption(ndb.Model):
    """model for representing a Caption"""
    captiontext = ndb.StringProperty()
    captiondate = ndb.DateTimeProperty(auto_now=True)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        # Return index page
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({}))

# [END main_page]

class MakeCaption(webapp2.RequestHandler):

    def post(self):
        input = ""

        # Check whether a caption was given
        if not self.request.get('caption'):
            input = "Choose a caption #easteregg"
        else:
            input = self.request.get('caption')

        # Save caption with the input text in the db
        caption = Caption(captiontext=input)
        caption_key = caption.put()

        # Redirect to caption webpage with the key of the element as a parameter
        query_params = {'ck': caption_key.urlsafe()}
        self.redirect('/caption?' + urllib.urlencode(query_params))

# [START generate_caption]

#Dynamically generate
class GenerateCaption(webapp2.RequestHandler):

    def get(self):

        # Get the key of the caption from the request
    	ck = self.request.get('ck')
    	caption_key = ndb.Key(urlsafe=ck)

        # Retrieve from db
        caption = caption_key.get()

        # ****** CHANGE THIS WHEN USING ANOTHER IMAGE *******
        # (width, height, x, y, line height, number of lines)
        # ***************************************************
        c = ImageConstants(694,540,520,456,90,6)

        # Load the template image
        img = Image.open("captionimage/caption.jpeg")
        draw = ImageDraw.Draw(img)

        # Load the font used for the captions
        font = ImageFont.truetype("fonts/Libertine.ttf", c.lh-6)
        input = caption.captiontext
        # Split the input sentence in words
        words = input.split(' ')

        nb_lines = 0
        word_nb = 0
        lines = []

        # Calculate which words should be displayed on which line
        while nb_lines < c.l and word_nb < len(words):
            currentLine = words[word_nb]
            currentWidth = draw.textsize(currentLine, font=font)[0]
            word_nb += 1

            # Try to add words for as long as the width of the words on
            #    the current line are still smaller than the width of
            #    the caption area
            while currentWidth < c.w and word_nb < len(words):
                newWord = " " + words[word_nb]
                currentWidth +=  draw.textsize(newWord, font=font)[0]
                if currentWidth < c.w:
                    word_nb += 1
                    currentLine += newWord

            lines.append(currentLine)
            nb_lines += 1

        # Draw every line of words onto the template image
        # Lines are centered in X- and Y-axis
        line = 0
        while line < len(lines):
            text_line = lines[line]
            width = draw.textsize(text_line, font=font)[0]
            start_x = c.centerX() - (width/2)
            start_y = c.centerY() - ((c.lh*len(lines))/2)
            draw.text((start_x, start_y + (line * c.lh)), text_line, (0, 0, 0), font=font)
            line += 1

        # Get the output image
        imageOutput = StringIO.StringIO()
        img.save(imageOutput, format="jpeg")
        imageData = imageOutput.getvalue()

        # Return the output image
        self.response.headers['Content-Type'] = "image/jpeg"
        self.response.write(imageData)

# [END generate_caption]

# [START caption_page]
class CaptionPage(webapp2.RequestHandler):

    def get(self):
        # Get the caption key
        ck = self.request.get('ck')

        try:
        	caption_key = ndb.Key(urlsafe=ck)

            # Retrieve caption
        	caption = caption_key.get()

        	query_params = {'ck': caption_key.urlsafe()}

            # Set template values for the page
        	template_values = {
            	'captionimg': "generate?" + urllib.urlencode(query_params),
            	'urllink' : self.request.url,
            	'urllinkkey' : ck
        	}

            # Return the caption page
        	template = JINJA_ENVIRONMENT.get_template('caption.html')
            self.response.write(template.render(template_values))

        # If an error occurs, redirect to 404 page
        except:
            template_values = {}
            template = JINJA_ENVIRONMENT.get_template('404.html')
            self.response.write(template.render(template_values))

class ImageConstants(object):
	def __init__(self, width, height, x, y, line_height, lines):
		super(ImageConstants, self).__init__()
		self.w = width
		self.h = height
		self.x = x
		self.y = y
		self.lh = line_height
		self.l = lines
	def centerX(self):
		return self.x + (self.w/2)
	def centerY(self):
		return self.y + (self.h/2)

# [END caption_page]

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/makecaption', MakeCaption),
    ('/generate', GenerateCaption),
    ('/caption', CaptionPage),
], debug=False)
# [END app]
