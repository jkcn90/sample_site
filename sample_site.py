from time import time
from gevent import monkey
from socketio import socketio_manage
from socketio.mixins import BroadcastMixin
from socketio.namespace import BaseNamespace
from flask import Flask, Response, render_template, request, jsonify

from sample_parser.parse import sentence_tree, word_tree, message_group
from sample_parser.parse import message_predictions, km, vectorizer

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
    query_words = query.split()
    if query_words:
        last_word = query_words[-1]
    else:
        last_word = query
    word_completions = word_tree.get_completions(last_word)
    output['words'] = word_completions

    if last_word in sentence_tree.root_map:
        sentence_completions = sentence_tree.get_completions(query_words)
    else:
        sentence_completions = sentence_tree.get_completions(query_words[:-1])
    sentence_completions = [' '.join(sentence)
                            for sentence in sentence_completions]

    test_sentence = vectorizer.transform([query])
    predicted_group = km.predict(test_sentence)
    similar_messages = message_group[predicted_group[0]]

    similar_messages = sentence_completions + similar_messages

    output['sentence_completions'] = similar_messages

    output['query'] = query
    return jsonify(output)
