(function($,jQuery,window){

    var templates = {
        chatMessage : null,
        statsBar : null,
        autoCompleteBar : null
    };


    var globals = {
        username : null
    };

    var tools = {
        getRandomArbitary : function(min, max) {
            return Math.floor(Math.random() * (max - min + 1)) + min;
        },

        getRandomListElement : function(list){
            return list[this.getRandomArbitary(0,list.length-1)];
        }
    };

    var chatAPI = {

        connect : function(done) {

            var that = this;

            this.socket = io.connect('/chat');
            this.socket.on('connect', done);

            this.socket.on('message', function(message){
                if(that.onMessage){
                    that.onMessage(message);
                }
            });

            this.socket.on('stats', function(stats){
                if(that.onStats){
                    that.onStats(stats);
                }
            });

            this.socket.on('debug', function(message){
                console.info(message);
            });
        },

        join : function(username, onJoin){
            this.socket.emit('join', username, onJoin);
        },

        sendMessage : function(message, onSent) {
            this.socket.emit('message', message, onSent);
        },

        disconnect : function(){
            this.socket.disconnect();
        }

    };	

    var bindUI = function(){

        var displayChatMessage = function(message){
            $(".messages").append(
                templates.chatMessage({
                    author : message.sender === globals.username ? "Me" : message.sender,
                    time : moment(message.sent).format("H:mm"),
                    message : message.content,
                    labelClass : tools.getRandomListElement(["label-default","label-primary","label-success","label-info","label-warning","label-danger"])
                })
            );
        };

        $(window).unload(function() {
            chatAPI.disconnect();
        });

        $(".join-chat").validate({
            submitHandler: function(form) {

                var username = $(form).find("[name='username']").val();

                $(".join-chat").find(".btn").attr("disabled","disabled");

                chatAPI.join(username, function(joined, name){
                    if(joined){
                        globals.username = username;
                        $(form).hide();
                        $(".chat-panel").addClass("animated slideInRight");
                        $(".messages-wrapper").addClass("animated slideInLeft");
                        $(".splash").addClass("animated fadeOutUp");
                        $(".stats-bar").addClass("animated fadeInRight");
                        $(".autosuggest-bar").addClass("animated fadeInLeft");
                        $("#autosuggest").attr("autofocus", true);
                    }
                });
            },

            invalidHandler: function(event, validator){
                $("[name='username']").parent().addClass("has-error");
            }
        });

        $(".compose-message-form").find("[name='message']").on("keyup",function(e){
            e = e || event;
            if (e.keyCode === 13 && !e.ctrlKey) {
                $(".compose-message-form").submit();
            }
            return true;
        });

        $(".compose-message-form").validate({
            submitHandler: function(form) {
                $(".compose-message-form").find("[name='message']").attr("disabled","disabled");

                chatAPI.sendMessage($(form).find("[name='message']").val(), function(sent,message){
                    if(sent){
                        $(".compose-message-form").find("[name='message']").removeAttr("disabled");
                        $(".compose-message-form").find("textarea").val("");
                        displayChatMessage(message);
                    }
                });
            },

            invalidHandler: function(event, validator){
                $("[name='message']").parent().addClass("has-error");
            }
        });

        chatAPI.onMessage = function(message){
            displayChatMessage(message);
        };

        chatAPI.onStats = function(stats){
            for(var i=0; i<stats.people.length; i++){
                stats.people[i] = {
                    username : stats.people[i],
                };
            }

            $(".stats-bar").html(
                templates.statsBar(stats)
            );
        };

    };

    var autosuggest = function() {
        $(" #autosuggest" ).keyup(function( event ) {
            var inputData = $('textarea[name="message"]').val();

            $.getJSON('/autosuggest', {
                q: inputData,
            }, function(data) {
                $("#autosuggest").autocomplete({
                    source: function( request, response ) {
                        response($.ui.autocomplete.filter(
                            data.words, request.term.split(" ").pop()
                        ));
                    }
                });

                var numberOfCompletions = Math.min(15, data.sentence_completions.length);
                for(var i = 0; i < numberOfCompletions; i++){
                    data.sentence_completions[i] = {
                        completion : data.sentence_completions[i],
                    };
                }
                $(".autosuggest-bar").html(
                    templates.autoCompleteBar(data)
                );
            });

        });
    };

    var ready = function(){
        templates.chatMessage = Handlebars.compile($("#template-chat-message").html());
        templates.statsBar = Handlebars.compile($("#template-stats-bar").html());
        templates.autoCompleteBar = Handlebars.compile($("#template-autosuggest-bar").html());

        bindUI();
        chatAPI.connect(function(){});
        autosuggest();
        $("#autosuggest").blur( function(){
            setTimeout(function() { 
                $("#autosuggest").focus(); 
            }, 50);
        });
    };

    $(function(){ ready(); });

}($,jQuery,window));
