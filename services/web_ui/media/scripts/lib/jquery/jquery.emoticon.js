/* Copyright (c) 2009 Marak Squires - www.maraksquires.com

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

*/

/* we need to extend the RegExp object so we can remote regex special chars from emotes */
RegExp.escape = function(text) {
if (!arguments.callee.sRE) {
    var specials = ['/', '.', '*', '+', '?', '|','(', ')', '[', ']', '{', '}', '\\'];
    arguments.callee.sRE = new RegExp(
    '(\\' + specials.join('|\\') + ')', 'g'
    );
}
return text.replace(arguments.callee.sRE, '\\$1');
}

function create_urls_from(input) {
    return input.replace(/(ftp|http|https|file):\/\/[\S]+(\b|$)/gim,'<a href="$&" class="messenger_link" target="_blank">$&</a>')
    .replace(/([^\/])(www[\S]+(\b|$))/gim,'$1<a href="http://$2" class="messenger_link" target="_blank">$2</a>');
}

function create_smileys_from(path, input) {
    
    for( var a in emoticons.emoticon ) {
        emoticon = emoticons.emoticon[a];
        for( var emote in emoticon.emotes ) {
            emote = RegExp.escape(emote);
            input = input.replace( new RegExp( emote, 'gi' ), '<img src="'+path + emoticon.image + '" />');
        }
    }
    return input;
}

$.fn.emoticon = function(theme, theText) {
    var imagePath = "/media/themes/"+theme+"/css/images/emotes/"; 
    var smileyed = create_smileys_from(imagePath, theText);
    var urled = create_urls_from(smileyed);
    return urled;
};

var emoticons = {
    "emoticon": {
        "::smile": {
            "image": "smile.png",
            "emotes": {
                ":-)": "",
                ":)": "",
                ":]": "",
            }
        },
        "::bigSmile": {
            "image": "bigsmile.png",
            "emotes": {
                ":D": "",
                ":-D": "",
                "XD": "",
                "BD": ""
            }
        },
        "::shock": {
            "image": "shock.png",
            "emotes": {
                    ":O": "",
                    ":0": "",
                    ":-0": "",
                    ":-O": ""
            }
        },
        "::frown": {
            "image": "frown.png",
            "emotes": {
                ":-(": "",
                ":[": "",
                ":<": "",
                ":(": "",
                ":-\\": ""
            }
        },
        "::tongue": {
            "image": "tongue.png",
            "emotes": {
                ":P": "",
                "XP": "",
            }
        },
        "::bored": {
            "image": "bored.png",
            "emotes": {
                ":\\": "",
                ":-\\": "",
                ":|": ""
        }
        },
        "::wink": {
            "image": "wink.png",
            "emotes": {
                ";-)": "",
                ";)": "",
                ";]": ""
            }
        },
        "::confused": {
            "image": "confused.png",
            "emotes": {
                ":S": "",
                ":\?": ""
            }
        }
    }
};

