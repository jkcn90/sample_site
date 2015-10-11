from time import time
from gevent import monkey
from socketio import socketio_manage
from socketio.mixins import BroadcastMixin
from socketio.namespace import BaseNamespace
from flask import Flask, Response, render_template, request, jsonify

from sample_parser.parse import word_tree, sentence_tree, words

monkey.patch_all()

application = Flask(__name__)
application.debug = True
application.config['PORT'] = 5000


class ChatNamespace(BaseNamespace, BroadcastMixin):
    
    stats = {
        "people" : []
    }

    def initialize(self):
        self.logger = application.logger
        self.log("Socketio session started")

    def log(self, message):
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

    def report_stats(self):
        self.broadcast_event("stats",self.stats)

    def recv_connect(self):
        self.log("New connection")

    def recv_disconnect(self):
        self.log("Client disconnected")
        
        if self.session.has_key("username"):
            username = self.session['username']

            self.broadcast_event_not_me("debug", "%s left" % username)
            
            self.stats["people"] = filter(lambda e : e != username, self.stats["people"])
            self.report_stats()

    def on_join(self, username):
        self.log("%s joined chat" % username)
        self.session['username'] = username

        if not username in self.stats["people"]:
            self.stats["people"].append(username) 

        self.report_stats()

        return True, username

    def on_message(self, message):
        message_data = {
            "sender" : self.session["username"],
            "content" : message,
            "sent" : time()*1000 #ms
        }
        self.broadcast_event_not_me("message",{ "sender" : self.session["username"], "content" : message})
        return True, message_data



@application.route('/', methods=['GET'])
def landing():
    return render_template('landing.html')

@application.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/chat': ChatNamespace}, request)
    except:
        application.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()

@application.route('/autosuggest')
def get_tasks():
    output = {}

    query = request.args.get('q')
    word_completions = word_tree.get_completions(query)
    output['word_completions'] = word_completions

    sentence_completions = sentence_tree.get_completions([query])
    sentence_completions = [' '.join(sentence)
                            for sentence in sentence_completions]
    output['sentence_completions'] = sentence_completions
    output['query'] = query
    return jsonify(output)
